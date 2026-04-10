# FILE: backend/src/schemas.py
# VERSION: 1.1.0
# START_MODULE_CONTRACT
#   PURPOSE: Pydantic V2 schemas для валидации API request/response, включая PaginatedResponse.
#   SCOPE: FileItem, FileUpdate, AlertItem, PaginatedResponse
#   DEPENDS: none
#   LINKS: M-SCHEMAS, V-M-SCHEMAS
# END_MODULE_CONTRACT
#
# START_MODULE_MAP
#   FileItem - File response schema (from_attributes)
#   FileUpdate - File update input with title validation
#   AlertItem - Alert response schema (from_attributes)
#   PaginatedResponse - Generic paginated wrapper with items, total, limit, offset
# END_MODULE_MAP

from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, field_validator

T = TypeVar("T")


# START_BLOCK_FILE_SCHEMAS
class FileItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    original_name: str
    stored_name: str
    mime_type: str
    size: int
    processing_status: str
    scan_status: str | None
    scan_details: str | None
    metadata_json: dict | None
    requires_attention: bool
    created_at: datetime
    updated_at: datetime


class FileUpdate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("title must not be blank")
        return v.strip()
# END_BLOCK_FILE_SCHEMAS


# START_BLOCK_ALERT_SCHEMA
class AlertItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    file_id: str
    level: str
    message: str
    created_at: datetime
# END_BLOCK_ALERT_SCHEMA


# START_BLOCK_PAGINATED_RESPONSE
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    limit: int
    offset: int
# END_BLOCK_PAGINATED_RESPONSE

# START_CHANGE_SUMMARY
#   LAST_CHANGE: [v1.1.0 - Added PaginatedResponse generic, added stored_name to FileItem,
#                  added title validation to FileUpdate, added GRACE markup]
# END_CHANGE_SUMMARY
