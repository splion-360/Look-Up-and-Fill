import asyncio
import io
from typing import Any

import httpx
import pandas as pd
from fastapi import HTTPException, UploadFile

from app.config import CONCURRENCY_LIMIT, get_header, setup_logger


logger = setup_logger(__name__)
header = get_header()


def hamming_distance(s1: str, s2: str) -> int:
    if len(s1) != len(s2):
        return max(len(s1), len(s2))
    return sum(c1 != c2 for c1, c2 in zip(s1, s2, strict=False))


async def search_with_query(query: str) -> list:
    base_url = "https://finnhub.io/api/v1/search"
    search_url = f"{base_url}?q={query}"

    async with httpx.AsyncClient(headers=header, timeout=10.0) as client:
        response = await client.get(search_url)

        if response.status_code == 429:
            raise HTTPException(
                429,
                detail="API rate limit exceeded. Please try again later.",
            )

        response.raise_for_status()
        data = response.json()

    return data.get("result", [])


async def get_symbol_from_name(name: str) -> str | None:
    try:
        if not isinstance(name, str) or not name.strip():
            logger.warning(f"Invalid name provided: {name}")
            return None

        data = name.lower().strip()
        data = data.replace(".", " ")
        entities = data.split()

        if not entities:
            return None

        for word_count in range(len(entities), 0, -1):
            current_query = " ".join(entities[:word_count])

            if len(current_query) > 20:
                current_query = current_query[:20]

            logger.info(f"Trying search with query: {current_query}")
            company_info = await search_with_query(current_query)

            if company_info:
                logger.info(
                    f"Found {len(company_info)} results for query: {current_query}"
                )
                break
            
            await asyncio.sleep(0.2)
        else:
            logger.info(f"No results found for any variation of: {name}")
            return None

        for result in company_info:
            symbol = result.get("symbol", "")
            company_name = result.get("description", "")

            if symbol and company_name:
                if name == company_name.lower().strip():
                    logger.info(f"Found exact match - {symbol} for {name}")
                    return symbol

        best_match = None
        min_distance = float("inf")

        for result in company_info:
            symbol = result.get("symbol", "")
            company_name = result.get("description", "")

            if symbol and company_name:
                distance = hamming_distance(name, company_name.lower().strip())
                if distance < min_distance:
                    min_distance = distance
                    best_match = symbol

        if best_match:
            logger.info(
                f"Found best match - {best_match} for {name} with distance {min_distance}"
            )
            return best_match

        return None

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            e.response.status_code, detail=f"API error: {e.response.text}"
        ) from e

    except Exception as e:
        raise HTTPException(
            500, detail=f"Failed to lookup symbol for {name}"
        ) from e


def is_valid(text: str):
    """
    Check whether the given text is a valid ticker
    """
    if len(text) < 10 and text.isupper():
        return True

    return False


async def get_name_from_symbol(symbol: str) -> str | None:
    try:
        if not is_valid(symbol):
            return ""

        logger.info(f"Calling get_name_from_symbol with {symbol}")
        if not isinstance(symbol, str) or not symbol.strip():
            logger.warning(f"Invalid symbol provided: {symbol}")
            return None

        symbol_clean = symbol.upper().strip()
        base_url = "https://finnhub.io/api/v1/stock/profile2"
        query = f"{base_url}?symbol={symbol_clean}"

        async with httpx.AsyncClient(headers=header, timeout=10.0) as client:
            response = await client.get(query)

            if response.status_code == 429:
                logger.error("Finnhub API rate limit exceeded")
                raise HTTPException(
                    429,
                    detail="API rate limit exceeded. Please try again later.",
                )

            response.raise_for_status()
            data = response.json()

        if not data or not isinstance(data, dict):
            logger.info(f"No company data found for symbol: {symbol}")
            return None

        name = data.get("name", "")
        if name and name.strip():
            logger.info(f"Found company name: {name} for symbol {symbol}")
            return name.strip()
        else:
            logger.info(f"No company name found for symbol: {symbol}")
            return None

    except httpx.HTTPStatusError as e:

        logger.error(f"Finnhub API error: {e.response.status_code}")
        raise HTTPException(
            e.response.status_code, detail=f"API error: {e.response.text}"
        ) from e

    except Exception as e:

        raise HTTPException(
            500, detail=f"Failed to lookup company name for {symbol}"
        ) from e


async def process_csv_file(file: UploadFile) -> dict[str, Any]:
    try:
        content = await file.read()
        logger.info(f"Processing CSV file: {file.filename}")
        csv_string = content.decode("utf-8")
        df = pd.read_csv(io.StringIO(csv_string))

        logger.info(f"# of Rows: {len(df)}")
        missing_data = df.isnull().sum()

        # Rename the columsn to remain consistent
        columns = df.columns

        for field in ["shares", "price", "market"]:
            closest = [
                name for name in columns if field in name.lower().strip()
            ]
            df.rename(columns={closest[-1]: field}, inplace=True)

        data = {
            "total_rows": len(df),
            "columns": list(df.columns),
            "data": df.to_dict("records"),
            "missing_data": missing_data.to_dict(),
        }

        logger.info("CSV processing completed")
        return data

    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400, detail="Failed to parse the uploaded file"
        ) from e
    except pd.errors.EmptyDataError as e:
        raise HTTPException(status_code=400, detail="CSV file is empty") from e
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=400, detail=f"CSV parsing error: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="Internal server error during file processing",
        ) from e


async def process_single(row: dict) -> dict:
    if not row.get("symbol") or not row.get("name"):
        enriched_row = row.copy()
        lookup_success = False

        try:
            tasks = []

            if not row.get("symbol") and row.get("name"):
                tasks.append(("symbol", get_symbol_from_name(row["name"])))

            if not row.get("name") and row.get("symbol"):
                tasks.append(("name", get_name_from_symbol(row["symbol"])))

            if tasks:
                results = await asyncio.gather(
                    *[task[1] for task in tasks], return_exceptions=True
                )

                for i, (field_name, _) in enumerate(tasks):
                    result = results[i]
                    if isinstance(result, Exception):
                        if isinstance(result, HTTPException):
                            enriched_row["lookupStatus"] = "failed"
                            enriched_row["failureReason"] = result.detail
                        else:
                            enriched_row["lookupStatus"] = "failed"
                            enriched_row["failureReason"] = (
                                "Service temporarily unavailable"
                            )
                        logger.error(
                            f"Lookup failed for row {row.get('id')}: {result}"
                        )
                        break
                    elif result is not None:
                        enriched_row[field_name] = result
                        lookup_success = True
                    else:
                        enriched_row["lookupStatus"] = "failed"
                        enriched_row["failureReason"] = (
                            f"No matching {field_name} found in financial databases"
                        )
                        break

                if lookup_success and "lookupStatus" not in enriched_row:
                    enriched_row["isEnriched"] = True
                    enriched_row["lookupStatus"] = "success"
                elif "lookupStatus" not in enriched_row:
                    enriched_row["lookupStatus"] = "failed"
                    enriched_row["failureReason"] = (
                        "No matching data found in financial databases"
                    )

        except Exception as e:
            enriched_row["lookupStatus"] = "failed"
            enriched_row["failureReason"] = "Service temporarily unavailable"
            logger.error(f"Unexpected error for row {row.get('id')}: {str(e)}")

        return enriched_row
    else:
        return row


async def lookup_missing_data(data: list[dict]) -> dict[str, Any]:
    try:
        missing_rows = [
            row for row in data if not row.get("symbol") or not row.get("name")
        ]

        logger.info(f"Found {len(missing_rows)} rows with missing data")

        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)

        async def process(row):
            async with semaphore:
                return await process_single(row)

        enriched_data = await asyncio.gather(*[process(row) for row in data])
        return {"data": enriched_data, "enriched_count": len(missing_rows)}

    except Exception as e:
        logger.error(f"Error during lookup process: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Lookup failed: {str(e)}"
        ) from e
