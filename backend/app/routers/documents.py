from fastapi import APIRouter, File, UploadFile

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
    result = await process_csv_file(file)
    return result


@router.post("/lookup/full", response_model=LookupResponse)
async def lookup_missing(lookup_request: LookupRequest):
    result = await lookup_missing_data(lookup_request.data)
    return result


@router.post("/lookup/single", response_model=LookupResponse)
async def lookup_single(lookup_request: LookupRequest):
    result = await lookup_missing_data(lookup_request.data)
    return result


@router.get("/")
async def root():
    return {
        "message": "document cleaner service is up and running",
        "version": settings.version,
    }
