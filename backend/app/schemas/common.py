"""
Shared Pydantic response schemas used across multiple API routes.
"""

from typing import Generic, TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class VersionResponse(BaseModel):
    application: str
    version: str
    environment: str


class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    database: str


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


class PaginatedResponse(BaseModel, Generic[DataT]):
    items: list[DataT]
    total: int
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)
