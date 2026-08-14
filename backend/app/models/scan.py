"""Scan models. A Scan is polymorphic over url/text/image/qr/email/file."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
    JSON,
    Column,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.utils.time import utcnow

SCAN_TYPES = ("url", "text", "image", "qr", "email", "file")
RISK_LEVELS = ("low", "medium", "high", "critical")

scan_bookmarks = Table(
    "scan_bookmarks",
    Base.metadata,
    Column("user_id", ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("scan_id", ForeignKey("scans.id", ondelete="CASCADE"), primary_key=True),
)


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_type: Mapped[str] = mapped_column(String(16), index=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )

    # Normalized input
    input_text: Mapped[str | None] = mapped_column(Text)
    input_url: Mapped[str | None] = mapped_column(Text)
    file_path: Mapped[str | None] = mapped_column(String(512))
    file_name: Mapped[str | None] = mapped_column(String(255))
    file_mime: Mapped[str | None] = mapped_column(String(128))

    # Engine output
    trust_score: Mapped[float] = mapped_column(Float, default=50.0)
    risk_level: Mapped[str] = mapped_column(String(16), default="medium", index=True)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    provider: Mapped[str] = mapped_column(String(32), default="engine")

    country: Mapped[str | None] = mapped_column(String(4))
    country_name: Mapped[str | None] = mapped_column(String(128))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    is_public: Mapped[bool] = mapped_column(Boolean, default=False)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="scans")
    findings = relationship(
        "ScanFinding", back_populates="scan", cascade="all, delete-orphan", order_by="ScanFinding.id"
    )
    report = relationship("Report", back_populates="scan", uselist=False, cascade="all, delete-orphan")
    bookmarked_by = relationship("User", secondary=scan_bookmarks, back_populates="bookmarks")

    def to_public_map_payload(self) -> dict:
        """Anonymous geo payload used by the public threat map."""
        return {
            "id": self.id,
            "lat": self.latitude,
            "lng": self.longitude,
            "country": self.country_name,
            "risk": self.risk_level,
            "type": self.scan_type,
            "ts": self.created_at.isoformat() if self.created_at else None,
        }


class ScanFinding(Base):
    """A single indicator/finding produced by a scanner or the trust engine."""

    __tablename__ = "scan_findings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    category: Mapped[str] = mapped_column(String(64), index=True)
    code: Mapped[str] = mapped_column(String(64), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(16), default="info", index=True)
    impact: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.5)
    ai_label: Mapped[str | None] = mapped_column(String(64))
    ai_probability: Mapped[float | None] = mapped_column(Float)
    extra: Mapped[dict | None] = mapped_column(JSON, default=dict)

    scan = relationship("Scan", back_populates="findings")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category,
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "severity": self.severity,
            "impact": self.impact,
            "confidence": self.confidence,
            "ai_label": self.ai_label,
            "ai_probability": self.ai_probability,
            "extra": self.extra,
        }


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(255))
    recommendation: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    highlights: Mapped[list | None] = mapped_column(JSON, default=list)
    timeline: Mapped[list | None] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    scan = relationship("Scan", back_populates="report")
    user = relationship("User", back_populates="reports")
