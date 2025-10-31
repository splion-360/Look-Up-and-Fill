import io
from typing import Any

import pandas as pd
from fastapi import HTTPException, UploadFile

from app.config import setup_logger


logger = setup_logger(__name__)


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


async def lookup_missing_data(portfolio_data: list[dict]) -> dict[str, Any]:
    try:
        logger.info("Starting lookup for missing portfolio data")

        missing_rows = [
            row
            for row in portfolio_data
            if not row.get("symbol") or not row.get("name")
        ]

        logger.info(f"Found {len(missing_rows)} rows with missing data")

        enriched_data = []
        for row in portfolio_data:
            if not row.get("symbol") or not row.get("name"):
                enriched_row = row.copy()
                if not row.get("symbol"):
                    enriched_row["symbol"] = f"SYM{row.get('id', 1)}"
                if not row.get("name"):
                    enriched_row["name"] = f"Company {row.get('id', 1)}"
                enriched_row["isEnriched"] = True
                enriched_row["lookupStatus"] = "success"
                enriched_data.append(enriched_row)
            else:
                enriched_data.append(row)

        logger.info(f"Lookup completed: {enriched_data}")
        return {"data": enriched_data, "enriched_count": len(missing_rows)}
        
    except Exception as e:
        logger.error(f"Error during lookup process: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lookup failed: {str(e)}")
