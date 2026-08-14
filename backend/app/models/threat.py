"""Known threat indicators, blacklists and community reports."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utcnow


class Threat(Base):
    """A known malicious domain/URL/hash/phone collected or reported."""

    __tablename__ = "threats"
    __table_args__ = (UniqueConstraint("threat_type", "value", name="uq_threat_value"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    threat_type: Mapped[str] = mapped_column(String(32), index=True)
    value: Mapped[str] = mapped_column(String(512), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str | None] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[float] = mapped_column(Float, default=0.9)
    severity: Mapped[str] = mapped_column(String(16), default="high")
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    source: Mapped[str] = mapped_column(String(64), default="community")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    hits: Mapped[int] = mapped_column(Integer, default=0)

    @property
    def summary(self) -> str:
        return f"{self.threat_type}: {self.value} ({self.category})"


class ThreatReport(Base):
    """A user-submitted report that feeds the anonymous threat map."""

    __tablename__ = "threat_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(Integer)
    scan_id: Mapped[int | None] = mapped_column(Integer, index=True)
    content_type: Mapped[str] = mapped_column(String(32), default="url")
    content: Mapped[str] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(64), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(4))
    country_name: Mapped[str | None] = mapped_column(String(128))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    votes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
