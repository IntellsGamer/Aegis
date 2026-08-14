"""Threat, report, map, keyword, rule and admin schemas."""
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ThreatOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    threat_type: str
    value: str
    category: str
    title: str | None = None
    description: str | None = None
    confidence: float
    severity: str
    first_seen: datetime
    last_seen: datetime
    source: str
    active: bool
    hits: int


class ThreatCreate(BaseModel):
    threat_type: str = Field(min_length=1)
    value: str = Field(min_length=1)
    category: str = Field(min_length=1)
    title: str | None = None
    description: str | None = None
    confidence: float = Field(default=0.9, ge=0, le=1)
    severity: str = "high"
    source: str = "manual"


class ThreatUpdate(BaseModel):
    category: str | None = None
    title: str | None = None
    description: str | None = None
    confidence: float | None = None
    severity: str | None = None
    active: bool | None = None


class ThreatReportCreate(BaseModel):
    content_type: str = "url"
    content: str = Field(min_length=1)
    category: str = "unknown"
    description: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    country: str | None = None
    country_name: str | None = None


class ThreatReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content_type: str
    content: str
    category: str
    description: str | None = None
    status: str
    votes: int
    latitude: float | None = None
    longitude: float | None = None
    country: str | None = None
    country_name: str | None = None
    created_at: datetime


class MapPoint(BaseModel):
    lat: float
    lng: float
    risk: str
    type: str
    country: str | None = None
    count: int = 1


class MapResponse(BaseModel):
    points: list[MapPoint]
    countries: list[dict]
    total_reports: int


class KeywordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    keyword: str
    category: str
    impact: float
    severity: str
    description: str | None = None
    case_sensitive: bool
    is_regex: bool
    enabled: bool


class KeywordCreate(BaseModel):
    keyword: str
    category: str
    impact: float = -5.0
    severity: str = "medium"
    description: str | None = None
    case_sensitive: bool = False
    is_regex: bool = False


class KeywordUpdate(BaseModel):
    category: str | None = None
    impact: float | None = None
    severity: str | None = None
    description: str | None = None
    case_sensitive: bool | None = None
    enabled: bool | None = None


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    description: str | None = None
    category: str
    impact: float
    weight: float
    severity: str
    enabled: bool
    explain: str | None = None


class RuleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    impact: float | None = None
    weight: float | None = None
    severity: str | None = None
    enabled: bool | None = None
    explain: str | None = None


class AnalyticsOut(BaseModel):
    totals: dict
    weekly: list[dict]
    monthly: list[dict]
    categories: list[dict]
    risk_distribution: list[dict]
    accuracy: dict


class AdminStatsOut(BaseModel):
    users: dict
    scans: dict
    threats: dict
    reports: dict
    daily_scans: list[dict]
    top_threats: list[dict]
    model_info: dict | None = None


class RetrainResponse(BaseModel):
    status: str
    task_id: str | None = None
    message: str
    metrics: dict | None = None
