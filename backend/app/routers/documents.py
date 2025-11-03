from fastapi import APIRouter, File, Request, Response, UploadFile

from app.core.config import settings
from app.schemas.documents import (
    LookupRequest,
    LookupResponse,
    UploadResponse,
)
from app.services.document_processing_service import (
    lookup_missing_data,
    process_csv_file,
)


router = APIRouter()
_file = File(...)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = _file):
    try:
        result = await process_csv_file(file)
        return result

    except Exception as e:
        raise e


@router.post("/lookup/full", response_model=LookupResponse)
async def lookup_missing(lookup_request: LookupRequest, response: Response):
    try:
        result = await lookup_missing_data(lookup_request.data)
        if result.get("cache_hits", 0) > 0:
            response.status_code = 201
        return result
    except Exception as e:
        raise e


@router.post("/lookup/single", response_model=LookupResponse)
async def lookup_single(lookup_request: LookupRequest, response: Response):
    try:
        result = await lookup_missing_data(lookup_request.data)
        if result.get("cache_hits", 0) > 0:
            response.status_code = 201
        return result
    except Exception as e:
        raise e


@router.get("/")
async def root():
    return {
        "message": "document cleaner service is up and running",
        "version": settings.version,
    }


@router.post("/_private/rl/reset")
async def clear_rate_limits(request: Request):
    try:
        rate_limiter = request.app.state.rate_limiter

        forwarded_for = request.headers.get(
            "X-Forwarded-For", request.client.host
        )
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        else:
            real_ip = request.headers.get("X-Real-IP")
            client_ip = (
                real_ip
                if real_ip
                else (request.client.host if request.client else "UNK")
            )

        rate_limiter.reset_rate_limits(client_ip)
        return {"message": "Rate limits cleared"}
    except Exception as e:
        raise e
