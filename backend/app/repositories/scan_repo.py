"""Scan repository: DB access for scans, findings and reports."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models import Report, Scan, ScanFinding
from app.utils.time import utcnow


class ScanRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, scan_id: int, load_findings: bool = True) -> Scan | None:
        stmt = select(Scan).where(Scan.id == scan_id)
        if load_findings:
            stmt = stmt.options(selectinload(Scan.findings))
        return self.db.scalar(stmt)

    def get_for_user(self, scan_id: int, user_id: int) -> Scan | None:
        return self.db.scalar(
            select(Scan)
            .where(Scan.id == scan_id, Scan.user_id == user_id)
            .options(selectinload(Scan.findings))
        )

    def list_for_user(self, user_id: int, page: int = 1, page_size: int = 20,
                      scan_type: str | None = None, risk: str | None = None):
        stmt = select(Scan).where(Scan.user_id == user_id).order_by(Scan.id.desc())
        if scan_type:
            stmt = stmt.where(Scan.scan_type == scan_type)
        if risk:
            stmt = stmt.where(Scan.risk_level == risk)
        total = len(self.db.scalars(stmt).all())
        items = self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
        return total, items

    def list_public(self, page: int = 1, page_size: int = 20):
        stmt = (
            select(Scan)
            .where(Scan.is_public.is_(True), Scan.status == "completed")
            .order_by(Scan.id.desc())
        )
        total = len(self.db.scalars(stmt).all())
        items = self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
        return total, items

    def create(self, data: dict) -> Scan:
        scan = Scan(**data)
        self.db.add(scan)
        self.db.flush()
        return scan

    def add_finding(self, scan_id: int, finding: dict) -> ScanFinding:
        row = ScanFinding(
            scan_id=scan_id,
            category=finding.get("category", "analysis"),
            code=finding.get("code", "unknown"),
            title=finding.get("title", "Finding"),
            description=finding.get("description"),
            evidence=finding.get("evidence"),
            severity=finding.get("severity", "info"),
            impact=float(finding.get("impact") or 0.0),
            confidence=float(finding.get("confidence") or 0.5),
            ai_label=finding.get("ai_label"),
            ai_probability=finding.get("ai_probability"),
            extra=finding.get("extra"),
        )
        self.db.add(row)
        return row

    def complete(self, scan: Scan, trust_score: float, risk_level: str,
                 confidence: float, summary: str | None) -> None:
        scan.trust_score = trust_score
        scan.risk_level = risk_level
        scan.confidence = confidence
        scan.summary = summary
        scan.status = "completed"
        scan.completed_at = utcnow()
        self.db.add(scan)

    def save(self, scan: Scan) -> None:
        self.db.add(scan)
        self.db.flush()

    def delete(self, scan: Scan) -> None:
        self.db.delete(scan)
        self.db.flush()

    def toggle_bookmark(self, scan: Scan, user) -> bool:
        if user in scan.bookmarked_by:
            scan.bookmarked_by.remove(user)
            bookmarked = False
        else:
            scan.bookmarked_by.append(user)
            bookmarked = True
        self.db.add(scan)
        self.db.flush()
        return bookmarked

    def list_bookmarks(self, user_id: int) -> list[Scan]:
        return self.db.scalars(
            select(Scan)
            .join(Scan.bookmarked_by)
            .where(Scan.id.in_(
                select(func.max(func.group_concat(Scan.id))).where(True)
            ))
        ).all() or []

    # --- stats ---------------------------------------------------------------
    def count(self, scan_type: str | None = None) -> int:
        stmt = select(func.count(Scan.id))
        if scan_type:
            stmt = stmt.where(Scan.scan_type == scan_type)
        return self.db.scalar(stmt) or 0

    def count_today(self) -> int:
        return (
            self.db.scalar(
                select(func.count(Scan.id)).where(
                    Scan.created_at >= utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
                )
            ) or 0
        )

    def risk_distribution(self):
        rows = self.db.execute(
            select(Scan.risk_level, func.count(Scan.id))
            .group_by(Scan.risk_level)
        ).all()
        return [{"risk": r, "count": c} for r, c in rows]

    def count_by_day(self, days: int = 14):
        start = (utcnow() - timedelta(days=days)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        rows = self.db.execute(
            select(func.date(Scan.created_at), func.count(Scan.id))
            .where(Scan.created_at >= start)
            .group_by(func.date(Scan.created_at))
        ).all()
        return {str(d): int(c) for d, c in rows}

    def high_risk_recent(self, limit: int = 10):
        return self.db.scalars(
            select(Scan)
            .where(Scan.risk_level.in_(("high", "critical")), Scan.status == "completed")
            .order_by(Scan.id.desc())
            .limit(limit)
        ).all()

    def save_report(self, scan: Scan, title: str, summary: str | None,
                    recommendation: str | None, highlights: list | None,
                    timeline: list | None, user_id: int | None) -> Report:
        report = Report(
            scan_id=scan.id, user_id=user_id, title=title, summary=summary,
            recommendation=recommendation, highlights=highlights or [], timeline=timeline or [],
        )
        self.db.add(report)
        self.db.flush()
        return report

    def get_report(self, scan_id: int) -> Report | None:
        return self.db.scalar(select(Report).where(Report.scan_id == scan_id))
