from pydantic import BaseModel


class UploadResponse(BaseModel):
    total_rows: int
    columns: list[str]
    data: list[dict]
    missing_data: dict[str, int]


class LookupRequest(BaseModel):
    data: list[dict]


class LookupResponse(BaseModel):
    data: list[dict]
    enriched_count: int
