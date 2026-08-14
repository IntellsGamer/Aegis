"""Scan-related schemas."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator


class ScanRequestBase(BaseModel):
    """Common metadata every scan request may carry."""

    is_public: bool = False
    save_history: bool | None = None  # defaults to user settings


class UrlScanRequest(ScanRequestBase):
    url: str = Field(min_length=1, max_length=2048)


class TextScanRequest(ScanRequestBase):
    text: str = Field(min_length=3, max_length=100_000)


class QrScanRequest(ScanRequestBase):
    image: str = Field(min_length=20, description="Base64 encoded image data URI")


class EmailScanRequest(ScanRequestBase):
    raw_email: str = Field(min_length=10, max_length=1_000_000)
    filename: str | None = None


class FileScanRequest(ScanRequestBase):
    pass  # multipart upload


class FindingOut(BaseModel):
    id: int | None = None
    category: str
    code: str
    title: str
    description: str | None = None
    evidence: str | None = None
    severity: str
    impact: float
    confidence: float
    ai_label: str | None = None
    ai_probability: float | None = None
    extra: dict[str, Any] | None = None


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_type: str
    trust_score: float
    risk_level: str
    confidence: float
    summary: str | None = None
    status: str
    input_text: str | None = None
    input_url: str | None = None
    file_name: str | None = None
    country: str | None = None
    country_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    is_public: bool
    created_at: datetime
    completed_at: datetime | None = None
    findings: list[FindingOut] = []


class ScanCreate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    scan_type: str
    input_text: str | None = None
    input_url: str | None = None
    file_path: str | None = None
    file_name: str | None = None
    file_mime: str | None = None
    is_public: bool = False
    ip_address: str | None = None
    country: str | None = None
    country_name: str | None = None
    latitude: float | None = None
    longitude: float | None = None


class ScanListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_type: str
    trust_score: float
    risk_level: str
    confidence: float
    summary: str | None = None
    input_text: str | None = None
    input_url: str | None = None
    file_name: str | None = None
    is_public: bool
    created_at: datetime
    completed_at: datetime | None = None


class ScanListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ScanListItem]


class BookmarkToggleResponse(BaseModel):
    bookmarked: bool
