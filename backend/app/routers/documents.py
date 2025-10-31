from fastapi import APIRouter, File, UploadFile

from app.config import setup_logger
from app.schemas.documents import (
    LookupRequest,
    LookupResponse,
    UploadResponse,
)
from app.services.document_service import (
    lookup_missing_data,
    process_csv_file,
)


router = APIRouter()
_file = File(...)
logger = setup_logger(__name__)


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = _file):
    result = await process_csv_file(file)
    return result


@router.post("/lookup/full", response_model=LookupResponse)
async def lookup_missing(request: LookupRequest):
    result = await lookup_missing_data(request.data)
    return result


@router.post("/lookup/single", response_model=LookupResponse)
async def lookup_single(request: LookupRequest):
    result = await lookup_missing_data(request.data)
    return result
