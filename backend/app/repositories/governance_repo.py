"""Repositories for governed intelligence sources and measured scan outcomes."""
from __future__ import annotations

from collections import Counter
from datetime import timedelta
from typing import Iterable

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Scan, ScanOutcome, ThreatFeed
from app.repositories.admin_repo import ThreatRepository
from app.utils.time import utcnow

FEED_CATALOG = {
    "local": {
        "provider": "AEGIS local indicators",
        "terms_url": None,
        "description": "Administrator-created and moderated community indicators.",
        "minimum_interval": None,
    },
    "urlhaus": {
        "provider": "abuse.ch URLhaus",
        "terms_url": "https://urlhaus.abuse.ch/api/",
        "description": "Malware-distribution URL intelligence; credentials and provider terms are required.",
        "minimum_interval": 5,
    },
    "openphish": {
        "provider": "OpenPhish",
        "terms_url": "https://openphish.com/kb.html",
        "description": "Phishing intelligence; a licensed feed or database configuration is required.",
        "minimum_interval": 5,
    },
    "phishtank": {
        "provider": "PhishTank",
        "terms_url": "https://www.phishtank.net/api_info.php",
        "description": "Rate-limited phishing URL lookup; an application key and descriptive agent are recommended.",
        "minimum_interval": 5,
    },
}

VALID_OUTCOMES = {"confirmed_malicious", "confirmed_benign", "inconclusive", "expired_unreachable"}


class GovernanceRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def ensure_feed_catalog(self) -> None:
        existing = {feed.slug: feed for feed in self.db.scalars(select(ThreatFeed)).all()}
        for slug, spec in FEED_CATALOG.items():
            if slug in existing:
                continue
            self.db.add(ThreatFeed(
                slug=slug,
                provider=spec["provider"],
                enabled=(slug == "local"),
                terms_accepted=(slug == "local"),
                refresh_interval_minutes=spec["minimum_interval"],
                metadata_json={
                    "terms_url": spec["terms_url"],
                    "description": spec["description"],
                    "automatic_sync": False,
                    "data_boundary": "disabled_until_admin_configuration" if slug != "local" else "local_only",
                },
            ))
        self.db.flush()

    def list_feeds(self) -> list[ThreatFeed]:
        self.ensure_feed_catalog()
        return self.db.scalars(select(ThreatFeed).order_by(ThreatFeed.slug)).all()

    def get_feed(self, slug: str) -> ThreatFeed | None:
        self.ensure_feed_catalog()
        return self.db.scalar(select(ThreatFeed).where(ThreatFeed.slug == slug))

    def configure_feed(self, feed: ThreatFeed, *, enabled: bool, terms_accepted: bool,
                       refresh_interval_minutes: int | None) -> ThreatFeed:
        if feed.slug != "local" and enabled and not terms_accepted:
            raise ValueError("Provider terms must be explicitly accepted before enabling a remote feed")
        minimum = FEED_CATALOG.get(feed.slug, {}).get("minimum_interval")
        if refresh_interval_minutes is not None and minimum and refresh_interval_minutes < minimum:
            raise ValueError(f"Refresh interval cannot be lower than {minimum} minutes for this source")
        feed.enabled = enabled
        feed.terms_accepted = terms_accepted
        feed.refresh_interval_minutes = refresh_interval_minutes
        feed.last_status = "configured"
        self.db.add(feed)
        self.db.flush()
        return feed

    def import_indicators(self, feed: ThreatFeed, indicators: Iterable[dict]) -> dict:
        if not feed.enabled or not feed.terms_accepted:
            raise ValueError("The source is disabled or its terms have not been accepted")
        threat_repo = ThreatRepository(self.db)
        now = utcnow()
        inserted = 0
        rejected = 0
        for item in indicators:
            value = str(item.get("value") or "").strip()
            threat_type = str(item.get("threat_type") or "url").strip().lower()
            if not value or threat_type not in {"url", "domain", "hash", "ip", "phone", "email"}:
                rejected += 1
                continue
            threat_repo.create({
                "threat_type": threat_type,
                "value": value[:512],
                "category": str(item.get("category") or "phishing")[:64],
                "title": str(item.get("title") or f"{feed.provider} indicator")[:255],
                "description": str(item.get("source_reference") or "")[:2000] or None,
                "confidence": max(0.0, min(1.0, float(item.get("confidence", 0.9)))),
                "severity": str(item.get("severity") or "high")[:16],
                "source": f"feed:{feed.slug}",
            })
            inserted += 1
        feed.last_refreshed_at = now
        feed.last_success_at = now
        feed.last_status = "success"
        feed.last_error = None
        self.db.add(feed)
        self.db.flush()
        return {"ingested": inserted, "rejected": rejected, "feed": feed.slug}

    def record_outcome(self, *, scan: Scan, reviewer_user_id: int | None, verdict: str,
                       rationale: str | None, engine_version: str, evidence_snapshot: dict) -> ScanOutcome:
        if verdict not in VALID_OUTCOMES:
            raise ValueError(f"Outcome must be one of: {', '.join(sorted(VALID_OUTCOMES))}")
        outcome = ScanOutcome(
            scan_id=scan.id,
            reviewer_user_id=reviewer_user_id,
            verdict=verdict,
            rationale=(rationale or "")[:2000] or None,
            engine_version=engine_version,
            evidence_snapshot=evidence_snapshot,
        )
        self.db.add(outcome)
        self.db.flush()
        return outcome

    def outcome_summary(self, days: int = 30) -> dict:
        cutoff = utcnow() - timedelta(days=days)
        rows = self.db.execute(
            select(ScanOutcome.verdict, func.count(ScanOutcome.id))
            .where(ScanOutcome.created_at >= cutoff)
            .group_by(ScanOutcome.verdict)
        ).all()
        counts = Counter({verdict: int(count) for verdict, count in rows})
        return {
            "window_days": days,
            "total": sum(counts.values()),
            "by_verdict": {outcome: counts.get(outcome, 0) for outcome in sorted(VALID_OUTCOMES)},
            "definition": "Human or policy-verified outcomes; not training data and not a replacement for measured evaluation metrics.",
        }
