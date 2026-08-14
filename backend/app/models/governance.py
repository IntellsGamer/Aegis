"""Governance records for threat intelligence and evidence-quality outcomes."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.utils.time import utcnow


class ThreatFeed(Base):
    """Configured threat-intelligence source with explicit operational state."""

    __tablename__ = "threat_feeds"
    __table_args__ = (UniqueConstraint("slug", name="uq_threat_feed_slug"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(64), index=True)
    provider: Mapped[str] = mapped_column(String(128))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    terms_accepted: Mapped[bool] = mapped_column(Boolean, default=False)
    refresh_interval_minutes: Mapped[int | None] = mapped_column(Integer)
    last_refreshed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_success_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_status: Mapped[str] = mapped_column(String(32), default="never")
    last_error: Mapped[str | None] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)


class ScanOutcome(Base):
    """A human or policy outcome used for measured quality, never model training."""

    __tablename__ = "scan_outcomes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_id: Mapped[int] = mapped_column(Integer, index=True)
    reviewer_user_id: Mapped[int | None] = mapped_column(Integer, index=True)
    verdict: Mapped[str] = mapped_column(String(32), index=True)
    rationale: Mapped[str | None] = mapped_column(Text)
    engine_version: Mapped[str] = mapped_column(String(64))
    evidence_snapshot: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
