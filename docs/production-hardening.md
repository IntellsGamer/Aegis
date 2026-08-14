# AEGIS Production Hardening Architecture

**Status:** Active implementation plan  
**Principle:** A scan may only claim what it observed, from a named source, at a known time and precision.

## Design Decisions

| Area | Decision | Rationale |
|---|---|---|
| URL acquisition | A dedicated safe-fetch boundary validates every submitted and redirected URL before network access. | URL scanning must not become access to private infrastructure. |
| Map data | The public map shows only approved real reports. Country-level aggregates use a declared centroid and never claim an exact victim or server location. | A visually plausible map with fabricated coordinates is worse than an empty map. |
| Geolocation | No pseudo-geolocation from IP bytes. Optional local GeoIP data may enrich an incident only when installed and the source is retained. | Location needs provenance and privacy boundaries. |
| Threat intelligence | Feed records carry source, fetched time, expiry, status, and indicator provenance. Connectors stay disabled until an administrator configures credentials and accepts provider terms. | Live indicators must be current, governed, and revocable. |
| Confidence | Engine confidence remains evidence coverage/agreement. Measured quality is stored separately as versioned evaluation outcomes. | A confidence value is not an accuracy claim. |
| Privacy | Scan retention is explicit: no storage, redacted evidence, or encrypted full artifact. Public reporting is opt-in and moderation-gated. | The platform handles sensitive messages and URLs. |
| Product integration | Detection should move toward pre-click browser/mail workflows, but the server API remains a deterministic evidence service. | The engine is useful only if it reaches the decision point. |

## Public Map Contract

A map point must satisfy all of the following conditions:

1. It is created from an actual user report or verified scan report, never a seed record.
2. It has passed moderation and has `approved` status.
3. Its time window is explicitly requested and server-enforced.
4. Its source and location precision are returned by the API and displayed in the interface.
5. Location is country-aggregate unless a future verified provider explicitly supplies another allowed precision.

The map never exposes a user IP address, a street-level location, or an unreviewed user-provided coordinate.

## Threat Intelligence Connector Contract

Every connector implements the same operations: `health`, `lookup`, `refresh`, `revoke`, and `provenance`. A connector result contains an indicator type/value, severity, confidence, source, source reference, observed timestamp, expiry timestamp, and raw-evidence hash. Refresh frequency must follow provider terms; it is not hard-coded into the web request path.

The initial repository includes an administrative local feed/import contract and preserves local indicators. Live providers require separately configured credentials and explicit terms acceptance. URLhaus, OpenPhish, and PhishTank have materially different access, scope, and rate-limit models; therefore no provider is silently enabled by default.[1] [2] [3]

## Quality and Outcome Contract

An analyst can mark a scan **confirmed malicious**, **confirmed benign**, **inconclusive**, or **expired/unreachable**. The outcome stores reviewer, time, rationale, and engine version. A future rule-weight review consumes only these verified outcomes. This retains the model-free design while enabling measurable improvement.

## References

[1] [abuse.ch, *URLhaus Community API*](https://urlhaus.abuse.ch/api/)

[2] [OpenPhish, *Knowledge Base*](https://openphish.com/kb.html)

[3] [PhishTank, *API Information*](https://www.phishtank.net/api_info.php)

## Connector Source Notes

| Source | Verified integration constraint | AEGIS handling |
|---|---|---|
| URLhaus | Community API access requires an Auth-Key; its datasets distinguish active and recent malware-distribution URLs, and the documented refresh cadence is as frequent as five minutes. It explicitly excludes phishing-only submissions from its malware scope. | Treat as an optional malware-URL connector with key configuration, terms acknowledgement, source/expiry metadata, and no silent phishing claim. |
| OpenPhish | Its commercial feed/database products distinguish current active phishing intelligence from offline historical data and describe refresh windows from five to fifteen minutes depending on product. | Treat as an optional licensed phishing connector; retain provider verdict time and feed tier in provenance. |
| PhishTank | Its URL lookup API uses POST, supports an optional application key, requires a descriptive user agent, and documents rate limiting. | Treat as a bounded per-URL lookup connector with request budgets, cache/TTL, and explicit rate-limit telemetry. |

These sources were read on 14 August 2026: [URLhaus Community API](https://urlhaus.abuse.ch/api/), [OpenPhish Knowledge Base](https://openphish.com/kb.html), and [PhishTank API Information](https://www.phishtank.net/api_info.php).
