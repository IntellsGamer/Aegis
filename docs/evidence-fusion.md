# AEGIS Evidence Fusion Engine

**Author:** Manus AI  
**Status:** Active architecture  
**Engine identifier:** `evidence-fusion-v2`

## Purpose and Boundary

AEGIS must provide a useful scam-risk assessment without learning from customer scans, training a statistical model, or delegating judgement to an LLM. The engine therefore consumes only findings produced by deterministic scanners. It estimates the likelihood that the observed content is risky; it does **not** claim that an unobserved threat is absent.

> A low-risk result means that the available evidence did not reach the configured concern threshold. It is not a safety guarantee.

## Evidence Pipeline

| Stage | Input | Protection against misleading output | Output |
|---|---|---|---|
| Acquisition | URL, message, raw email, file text, image OCR, QR payload | Input validation and bounded scanners | Scanner findings and metadata |
| Normalization | Finding code, evidence, occurrence count, source confidence | Invalid / missing fields clamp to safe bounds | Normalized evidence item |
| Correlation control | Same-code and same-family observations | Strongest duplicate only; diminishing returns in a family | Independent evidence families |
| Fusion | Family likelihood contributions | Positive signals cannot linearly cancel a verified threat match | Risk probability and trust score |
| Calibration | Source diversity, reliability, coverage, probability margin | Empty scans receive low confidence | Risk level, confidence, recommendations |

For a finding *i*, the engine forms a signed evidence mass:

\[
m_i = \frac{|impact_i|}{scale} \times reliability_i \times density(occurrences_i)
\]

where negative rule impacts increase risk and positive rule impacts reduce it. Repeated matches are intentionally logarithmic and bounded. Evidence within one family is discounted geometrically, because three urgency phrases are not three independent facts. Families then contribute to the prior log odds:

\[
logit(P(risk)) = logit(0.08) + \sum_{family} fuse(m_i) + interactionBonus
\]

The interaction bonus activates only for independently meaningful combinations, such as an email-authentication failure plus a credential request, or a deceptive link plus an impersonated brand. A verified local threat-intelligence match also receives a direct bonus so that HTTPS or an old domain cannot mask it.

## Active Evidence Families

| Family | Examples | Typical role |
|---|---|---|
| Threat intelligence | Manually curated known threat | Direct, high-reliability evidence |
| Email authentication | SPF, DKIM, DMARC, Reply-To mismatch | Sender provenance evidence |
| Link delivery | Shortener, numeric IP, redirect payload, hostile lexical structure | Destination concealment evidence |
| Identity | Punycode, typosquatting, brand impersonation | Claim-versus-identity conflict |
| Requested action | Credential, OTP, payment, remote-access request | Victim-impact evidence |
| Social engineering | Urgency, fear, reward, money-transfer pressure | Persuasion evidence |
| Site reputation / behavior | TLS, age, hidden frames, obfuscated code | Supporting technical context |

The indicator selection follows official guidance: urgency, suspicious or shortened/misspelled links, claimed-source verification, sensitive-information requests, and email authentication are materially more useful together than any one generic phrase.[1] [2]

## False-Positive Controls

The scanner does not treat a mention of a bank, government, cryptocurrency, job, or relationship as a scam by itself. Those terms require an action-oriented context before becoming an active finding. This distinction avoids flagging ordinary news, educational material, or a transactional notification merely because it names a sensitive topic.

A repeated code is reduced to its strongest finding before fusion. This corrects the former behavior where duplicate scanner discoveries were silently treated as the first occurrence without retaining the strongest or most useful evidence.

## Confidence Semantics

Confidence is based on observable coverage, source reliability, evidence-family diversity, and the distance from the decision boundary. It is not a proxy for independently measured accuracy, nor does it become high simply because a long message repeats the same phrase. The user interface and report should therefore present score and confidence together.

## Validation Contract

The regression suite must retain at least the following cases:

| Scenario | Expected property |
|---|---|
| A known malicious destination with benign transport signals | Critical risk; positive signals cannot cancel the threat match |
| A deceptive brand-like hostname plus credential request | High or critical risk through independent identity and action evidence |
| A normal topical sentence mentioning a bank or cryptocurrency | Not elevated solely because of the topic |
| A message with repeated urgency wording | Less effect than several independent attack stages |
| An empty or minimally observable scan | Low confidence regardless of low risk |
| A full API text-scan path | Persists evidence and returns a verdict without invoking a model |

## References

[1] [CISA, *Recognize and Report Phishing*](https://www.cisa.gov/secure-our-world/recognize-and-report-phishing)

[2] [NIST, *Phishing Guidance for Small Businesses*](https://www.nist.gov/itl/smallbusinesscyber/guidance-topic/phishing)
