import asyncio
import io
from typing import Any

import httpx
import pandas as pd
from fastapi import HTTPException, UploadFile

from app.services.cache_service import company_cache
from app.utils import (
    CONCURRENCY_LIMIT,
    MAX_RETRIES,
    get_header,
    is_valid,
    levenshtein_distance,
    retry_handler,
    setup_logger,
    typo_checker,
)


logger = setup_logger(__name__)
header = get_header()
COLOR = "CYAN"


@retry_handler(MAX_RETRIES)
async def search_with_query(query: str) -> list:
    base_url = "https://finnhub.io/api/v1/search"
    search_url = f"{base_url}?q={query}"

    try:
        async with httpx.AsyncClient(headers=header, timeout=10.0) as client:
            response = await client.get(search_url)
            response.raise_for_status()
            data = response.json()
            results = data.get("result", [])
            return results

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            e.response.status_code, detail=f"Rate limit hit: {e.response.text}"
        ) from e

    except Exception as e:
        raise HTTPException(500, detail="Internal Server Error") from e

    return []


@retry_handler(MAX_RETRIES)
async def search_with_symbol(symbol: str) -> dict:
    base_url = "https://finnhub.io/api/v1/stock/profile2"
    profile_url = f"{base_url}?symbol={symbol}"

    try:
        async with httpx.AsyncClient(headers=header, timeout=10.0) as client:
            response = await client.get(profile_url)
            response.raise_for_status()
            profile_data = response.json()
            return profile_data

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            e.response.status_code, detail=f"Rate limit hit: {e.response.text}"
        ) from e

    except Exception as e:
        raise HTTPException(500, detail="Internal Server Error") from e
    return {}


async def get_symbol_from_name(name: str) -> str | None:
    try:
        if not isinstance(name, str) or not name.strip():
            logger.warning(f"Invalid name provided: {name or "UNK"}")
            return

        # Check cache first
        cached_symbol = company_cache.get_symbol_from_name(name)
        if cached_symbol:
            logger.info(f"Cache hit: {name} -> {cached_symbol}", "WHITE")
            return cached_symbol

        data = name.lower().strip()
        data = data.replace(".", " ")
        entities = data.split()

        if not entities:
            return

        for word_count in range(len(entities), 0, -1):
            current_query = " ".join(entities[:word_count])

            if len(current_query) > 20:
                current_query = current_query[:20]

            logger.info(f"Trying search with query: {current_query}", COLOR)
            company_info = await search_with_query(current_query)

            if company_info:
                logger.info(
                    f"Found {len(company_info)} results for query: {current_query}",
                    COLOR,
                )
                company_cache.set_name_to_symbols(name, company_info)
                break

            await asyncio.sleep(0.1)
        else:
            logger.info(
                f"No results found for any variation of: {name}. Trying spell check...",
                "CYAN",
            )
            suggestions = typo_checker.requires_check(name)
            for suggestion, distance in suggestions[:3]:
                logger.info(
                    f"Trying suggestion: {suggestion} (distance: {distance})",
                    "YELLOW",
                )
                company_info = await search_with_query(suggestion)
                if company_info:
                    logger.info(
                        f"Found results with: {suggestion}",
                        "GREEN",
                    )
                    company_cache.set_name_to_symbols(name, company_info)
                    break
                await asyncio.sleep(0.1)
            else:
                logger.info(
                    f"No results found even with spell checking for: {name}",
                    "CYAN",
                )
                return

        for result in company_info:
            symbol = result.get("symbol", "")
            company_name: str = result.get("description", "")

            if symbol and company_name:
                if name.lower().strip() == company_name.lower().strip():
                    logger.info(
                        f"Found exact match: {symbol} for {name}", COLOR
                    )
                    return symbol

        best_match = None
        min_distance = float("inf")

        for result in company_info:
            symbol = result.get("symbol", "")
            company_name = result.get("description", "")

            if symbol and company_name:
                distance = levenshtein_distance(
                    name.lower().strip(), company_name.lower().strip()
                )
                if distance < min_distance:
                    min_distance = distance
                    best_match = symbol

        if best_match:
            logger.info(
                f"Found best match - {best_match} for {name} with distance {min_distance}",
                "GREEN",
            )
            return best_match

        return

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            e.response.status_code, detail=f"API error: {e.response.text}"
        ) from e

    except Exception as e:
        raise HTTPException(
            500, detail=f"Failed to lookup symbol for {name}"
        ) from e


async def get_name_from_symbol(symbol: str) -> str | None:
    try:
        if not is_valid(symbol):
            return ""

        cached_name = company_cache.get_name_from_symbol(symbol)
        if cached_name:
            logger.info(f"Cache hit: {symbol} -> {cached_name}", "WHITE")
            return cached_name

        logger.info(f"Calling get_name_from_symbol with {symbol}", COLOR)
        if not isinstance(symbol, str) or not symbol.strip():
            logger.warning(f"Invalid symbol provided: {symbol}")
            return

        symbol_clean = symbol.upper().strip()
        data = await search_with_symbol(symbol_clean)

        if not data or not isinstance(data, dict):
            logger.info(f"No company data found for symbol: {symbol}", "CYAN")
            return

        name = data.get("name", "")
        if name and name.strip():
            company_cache.set_symbol_to_name(symbol_clean, name.strip())
            logger.info(
                f"Found company name: {name} for symbol {symbol}", COLOR
            )
            return name.strip()
        else:
            logger.info(f"No company name found for symbol: {symbol}", "CYAN")
            return

    except Exception as e:
        raise HTTPException(
            500, detail=f"Failed to lookup company name for {symbol}"
        ) from e


async def process_csv_file(file: UploadFile) -> dict[str, Any]:
    if not file.filename or not file.filename.lower().endswith(".csv"):

        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only CSV files are allowed.",
        )

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded.")

        logger.info(f"Processing CSV file: {file.filename}")
        csv_string = content.decode("utf-8")

        df = pd.read_csv(io.StringIO(csv_string))

        logger.info(f"# of Rows: {len(df)}", COLOR)

        columns = df.columns
        available_columns = [col.lower().strip() for col in columns]

        has_name_field = any("name" in col for col in available_columns)
        has_symbol_field = any("symbol" in col for col in available_columns)

        if not has_name_field:
            raise HTTPException(
                status_code=400,
                detail="Invalid file: must contain a COMPANY NAME field or similar",
            )
        if not has_symbol_field:
            raise HTTPException(
                status_code=400,
                detail="Invalid file: must contain a SYMBOL field or similar",
            )

        missing_data = df.isnull().sum()

        # Rename the columsn to remain consistent

        for field in ["shares", "price", "market"]:
            closest = [
                name for name in columns if field in name.lower().strip()
            ]
            if closest:
                df.rename(columns={closest[-1]: field}, inplace=True)

        data = {
            "total_rows": len(df),
            "columns": list(df.columns),
            "data": df.to_dict("records"),
            "missing_data": missing_data.to_dict(),
        }

        logger.info("CSV processing completed", COLOR)
        return data

    except UnicodeDecodeError as e:
        raise HTTPException(
            status_code=400, detail="Failed to parse the uploaded file"
        ) from e
    except pd.errors.ParserError as e:
        raise HTTPException(
            status_code=400, detail=f"CSV parsing error: {str(e)}"
        ) from e
    except Exception as e:
        if isinstance(e, HTTPException) and e.status_code == 400:
            raise e
        else:
            raise HTTPException(
                status_code=500,
                detail="Internal server error during file processing",
            ) from e


async def process_single(row: dict) -> dict:
    if not row.get("symbol") or not row.get("name"):
        enriched_row = row.copy()
        lookup_success = False
        cache_hit = False

        try:
            tasks = []

            if not row.get("symbol") and row.get("name"):
                cached_symbol = company_cache.get_symbol_from_name(row["name"])
                if cached_symbol:
                    cache_hit = True
                    enriched_row["symbol"] = cached_symbol
                    lookup_success = True
                else:
                    tasks.append(("symbol", get_symbol_from_name(row["name"])))

            if not row.get("name") and row.get("symbol"):
                cached_name = company_cache.get_name_from_symbol(row["symbol"])
                if cached_name:
                    cache_hit = True
                    enriched_row["name"] = cached_name
                    lookup_success = True
                else:
                    tasks.append(("name", get_name_from_symbol(row["symbol"])))

            if tasks:
                results = await asyncio.gather(
                    *[task[1] for task in tasks], return_exceptions=True
                )

                for i, (field_name, _) in enumerate(tasks):
                    result = results[i]
                    if isinstance(result, Exception):
                        enriched_row["lookupStatus"] = "failed"
                        enriched_row["failureReason"] = result.detail
                        logger.error(f"Lookup failed for {result}")
                        break

                    elif result is not None:
                        enriched_row[field_name] = result
                        lookup_success = True

                    else:
                        enriched_row["lookupStatus"] = "failed"
                        enriched_row["failureReason"] = (
                            f"No matching {field_name} found"
                        )
                        break

            if lookup_success and "lookupStatus" not in enriched_row:
                enriched_row["isEnriched"] = True
                enriched_row["lookupStatus"] = "success"
                enriched_row["cache_hit"] = cache_hit
            elif "lookupStatus" not in enriched_row:
                enriched_row["lookupStatus"] = "failed"
                enriched_row["failureReason"] = "No matching data found"

        except Exception as e:
            enriched_row["lookupStatus"] = "failed"
            enriched_row["failureReason"] = "Internal Server Error"
            logger.error(f"Unexpected error for row {row.get('id')}: {str(e)}")

        return enriched_row
    else:
        return row


async def lookup_missing_data(data: list[dict]) -> dict[str, Any]:
    try:
        missing_rows = [
            row for row in data if not row.get("symbol") or not row.get("name")
        ]

        if len(missing_rows) == 0:
            logger.info(
                "Table is complete (or) Invalid fields. Not proceeding further!!",
                "CYAN",
            )
            return {"data": data, "enriched_count": 0, "cache_hits": 0}

        logger.info(f"Found {len(missing_rows)} rows with missing data", COLOR)

        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
        cache_hit_count = 0

        async def process(row):
            nonlocal cache_hit_count
            async with semaphore:
                result = await process_single(row)
                if result.get("cache_hit"):
                    cache_hit_count += 1  # Monitoring the cache hits
                return result

        enriched_data = await asyncio.gather(*[process(row) for row in data])
        return {
            "data": enriched_data,
            "enriched_count": len(missing_rows),
            "cache_hits": cache_hit_count,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Lookup failed: {str(e)}"
        ) from e
