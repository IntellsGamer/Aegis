"""Admin repository: threats, keywords, rules, logs, community reports."""
from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import (
    AuditLog,
    Keyword,
    Rule,
    Threat,
    ThreatReport,
    User,
)
from app.utils.time import utcnow


class ThreatRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def search(self, query: str, limit: int = 20) -> list[Threat]:
        like = f"%{query.lower()}%"
        return self.db.scalars(
            select(Threat)
            .where(Threat.active.is_(True), Threat.value.ilike(like))
            .order_by(Threat.last_seen.desc())
            .limit(limit)
        ).all()

    def match(self, value: str) -> Threat | None:
        """Match a domain/hash/phone against the threat table."""
        return self.db.scalar(
            select(Threat).where(
                Threat.active.is_(True),
                func.lower(Threat.value) == value.lower(),
            )
        )

    def match_any(self, values: list[str]) -> list[Threat]:
        if not values:
            return []
        lowered = [v.lower() for v in values]
        return self.db.scalars(
            select(Threat).where(Threat.active.is_(True), func.lower(Threat.value).in_(lowered))
        ).all()

    def list(self, page: int = 1, page_size: int = 20, category: str | None = None):
        stmt = select(Threat).order_by(Threat.last_seen.desc())
        if category:
            stmt = stmt.where(Threat.category == category)
        total = len(self.db.scalars(stmt).all())
        items = self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
        return total, items

    def get(self, threat_id: int) -> Threat | None:
        return self.db.get(Threat, threat_id)

    def create(self, data: dict) -> Threat:
        existing = self.match(data["value"])
        if existing:
            existing.hits += 1
            existing.last_seen = utcnow()
            existing.category = data.get("category", existing.category)
            self.db.add(existing)
            self.db.flush()
            return existing
        threat = Threat(**data)
        self.db.add(threat)
        self.db.flush()
        return threat

    def update(self, threat: Threat, data: dict) -> Threat:
        for key, value in data.items():
            if value is not None and hasattr(threat, key):
                setattr(threat, key, value)
        self.db.add(threat)
        self.db.flush()
        return threat

    def delete(self, threat: Threat) -> None:
        self.db.delete(threat)
        self.db.flush()

    def increment_hit(self, threat: Threat) -> None:
        threat.hits += 1
        threat.last_seen = utcnow()
        self.db.add(threat)

    def count(self) -> int:
        return self.db.scalar(select(func.count(Threat.id))) or 0

    def active_count(self) -> int:
        return (
            self.db.scalar(select(func.count(Threat.id)).where(Threat.active.is_(True))) or 0
        )


class ThreatReportRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create(self, data: dict) -> ThreatReport:
        report = ThreatReport(**data)
        self.db.add(report)
        self.db.flush()
        return report

    def list_pending(self) -> list[ThreatReport]:
        return self.db.scalars(
            select(ThreatReport).where(ThreatReport.status == "pending").order_by(ThreatReport.id.desc())
        ).all()

    def list(self, status: str | None = None, page: int = 1, page_size: int = 20):
        stmt = select(ThreatReport).order_by(ThreatReport.id.desc())
        if status:
            stmt = stmt.where(ThreatReport.status == status)
        total = len(self.db.scalars(stmt).all())
        items = self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
        return total, items

    def get(self, report_id: int) -> ThreatReport | None:
        return self.db.get(ThreatReport, report_id)

    def update_status(self, report: ThreatReport, status: str) -> None:
        report.status = status
        self.db.add(report)
        self.db.flush()

    def vote(self, report: ThreatReport, delta: int) -> None:
        report.votes += delta
        self.db.add(report)
        self.db.flush()

    def geo_points(self, max_points: int = 2000):
        rows = self.db.execute(
            select(
                ThreatReport.latitude, ThreatReport.longitude, ThreatReport.risk if False else None,
                ThreatReport.country_name, ThreatReport.category, ThreatReport.content_type,
            )
            .where(ThreatReport.latitude.is_not(None), ThreatReport.longitude.is_not(None))
            .limit(max_points)
        ).all()
        points = []
        for lat, lng, _, country, category, ctype in rows:
            if lat is None or lng is None:
                continue
            points.append(
                {"lat": float(lat), "lng": float(lng), "country": country,
                 "category": category or "unknown", "type": ctype or "url"}
            )
        return points

    def country_counts(self):
        rows = self.db.execute(
            select(ThreatReport.country_name, func.count(ThreatReport.id))
            .where(ThreatReport.country_name.is_not(None))
            .group_by(ThreatReport.country_name)
            .order_by(func.count(ThreatReport.id).desc())
        ).all()
        return [{"country": c, "count": n} for c, n in rows]

    def count(self) -> int:
        return self.db.scalar(select(func.count(ThreatReport.id))) or 0

    def count_pending(self) -> int:
        return (
            self.db.scalar(
                select(func.count(ThreatReport.id)).where(ThreatReport.status == "pending")
            ) or 0
        )


class KeywordRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, page: int = 1, page_size: int = 100, category: str | None = None,
             enabled: bool | None = None):
        stmt = select(Keyword).order_by(Keyword.category, Keyword.keyword)
        if category:
            stmt = stmt.where(Keyword.category == category)
        if enabled is not None:
            stmt = stmt.where(Keyword.enabled == enabled)
        total = len(self.db.scalars(stmt).all())
        items = self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
        return total, items

    def create(self, data: dict) -> Keyword:
        keyword = Keyword(**data)
        self.db.add(keyword)
        self.db.flush()
        return keyword

    def update(self, keyword: Keyword, data: dict) -> Keyword:
        for key, value in data.items():
            if value is not None and hasattr(keyword, key):
                setattr(keyword, key, value)
        self.db.add(keyword)
        self.db.flush()
        return keyword

    def delete(self, keyword: Keyword) -> None:
        self.db.delete(keyword)
        self.db.flush()

    def get(self, keyword_id: int) -> Keyword | None:
        return self.db.get(Keyword, keyword_id)


class RuleRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list(self, enabled: bool | None = None):
        stmt = select(Rule).order_by(Rule.code)
        if enabled is not None:
            stmt = stmt.where(Rule.enabled == enabled)
        return self.db.scalars(stmt).all()

    def get(self, rule_id: int) -> Rule | None:
        return self.db.get(Rule, rule_id)

    def update(self, rule: Rule, data: dict) -> Rule:
        for key, value in data.items():
            if value is not None and hasattr(rule, key):
                setattr(rule, key, value)
        self.db.add(rule)
        self.db.flush()
        return rule

    def upsert_defaults(self, defaults: list[dict]) -> int:
        count = 0
        for item in defaults:
            existing = self.db.scalar(select(Rule).where(Rule.code == item["code"]))
            if existing:
                continue
            self.db.add(Rule(**item))
            count += 1
        self.db.flush()
        return count


class AuditLogRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def add(self, user_id: int | None, action: str, category: str = "system",
            detail: str | None = None, meta: dict | None = None, ip: str | None = None) -> AuditLog:
        log = AuditLog(
            user_id=user_id, action=action, category=category,
            detail=detail, meta=meta or {}, ip_address=ip,
        )
        self.db.add(log)
        self.db.flush()
        return log

    def list(self, page: int = 1, page_size: int = 50, category: str | None = None):
        stmt = select(AuditLog).order_by(AuditLog.id.desc())
        if category:
            stmt = stmt.where(AuditLog.category == category)
        total = len(self.db.scalars(stmt).all())
        items = self.db.scalars(stmt.offset((page - 1) * page_size).limit(page_size)).all()
        return total, items

    def count_last_days(self, days: int = 7) -> int:
        cutoff = utcnow() - timedelta(days=days)
        return (
            self.db.scalar(select(func.count(AuditLog.id)).where(AuditLog.created_at >= cutoff)) or 0
        )
