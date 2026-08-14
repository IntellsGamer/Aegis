# Aegis Contest-Readiness Audit

## Jury lens

A country-level cyber-security competition will typically reward more than an attractive prediction screen. Aegis must make three propositions immediately credible: it detects observable deception without unexplained automation; it guides the next safe action for a citizen or analyst; and it produces governed intelligence that can be reviewed without exposing users or fabricating threat data.

The joint CISA, NSA, FBI, and MS-ISAC guidance frames phishing as both credential theft and malware delivery, and organizes defenses around prevention, incident response, and reporting. It specifically highlights sender authentication, malicious-link and attachment blocking, phishing-resistant MFA, documented response, and usable reporting pathways.[1] NIST SP 800-63B likewise describes phishing resistance as a property of authentication protocols and requires an available phishing-resistant option at AAL2, reinforcing that a verdict alone is not the end of the user journey.[2]

| Contest criterion | Current Aegis strength | Material gap to close |
| --- | --- | --- |
| Transparent detection | Deterministic, family-aware evidence fusion; visible evidence and calibration | No compact analyst-grade chain of evidence or exportable assessment provenance in the main experience |
| Safe user action | Assessment state, recommendations, incident packet, MFA advice | Actions are generic rather than organized as an incident-response playbook with ownership, priority, and completion state |
| Threat intelligence integrity | Governed feed catalog, terms acceptance, provenance-aware map, moderated reports | No evidence graph or indicator correlation view that demonstrates how a report becomes trustworthy intelligence |
| Public-sector readiness | Privacy-aware retention and no fabricated map data | Missing an explicit operational readiness dashboard: coverage, limitations, governance, and quality measures |
| Competition demonstration | Strong first-run flow and multi-input scan UI | Missing a curated, non-deceptive guided scenario that tells the innovation story in under three minutes |

## Highest-value differentiated capabilities

1. **Threat casefile / explainable evidence chain.** Turn every assessment into a structured, exportable casefile with observed artifacts, source class, confidence, evidence-family contribution, assessment limitations, and a response checklist. This raises Aegis from a checker to an analyst tool.
2. **Response orchestration rather than static advice.** Give users a context-sensitive containment playbook, with steps that can be marked complete locally and a clear escalation packet. Tie the steps to credential-phishing versus attachment/malware scenarios.
3. **Intelligence correlation surface.** Present a safe, provenance-labelled relationship view among a scan, URL/domain artifacts, finding families, verified community reports, and governed sources. It must show no invented links and must label absent enrichment honestly.
4. **Readiness and accountability surface.** Show engine version, indicator source status, coverage conditions, retention posture, feedback/outcome counts, and publicly explain the non-training boundary. This is a contest-quality answer to "why should we trust it?"
5. **Guided competition demo.** A visible, deterministic walkthrough uses fixture-level content and highlights input safety, explainability, privacy, response action, and governance—without claiming a live threat is confirmed.

## References

[1] [CISA, NSA, FBI & MS-ISAC, *Phishing Guidance: Stopping the Attack Cycle at Phase One*](https://www.cisa.gov/sites/default/files/2025-03/Phishing%20Guidance%20-%20Stopping%20the%20Attack%20Cycle%20at%20Phase%20One%20508.pdf)

[2] [NIST, *SP 800-63B: Digital Identity Guidelines—Authentication and Authenticator Management*](https://pages.nist.gov/800-63-4/sp800-63b.html)

## Selected implementation increment

This increment will prioritize three connected surfaces that can be shown in one coherent judging flow. First, the existing report becomes an **assessment casefile**: it will expose the assessment state, a provenance-labelled evidence chain, a deterministic integrity fingerprint, and a response checklist whose completion is stored only in the viewer’s browser. Second, the existing administrator console will replace its obsolete training tab with **Operational Readiness**, showing deterministic-engine policy, feed governance, outcome-review counts, and explicit limitations. Third, the scan workspace will gain a clearly marked **guided demo scenario** that loads a fictional credential-lure email and explains that it is safe sample content—not live threat intelligence.

| Surface | What judges can verify | Deliberate boundary |
| --- | --- | --- |
| Assessment casefile | Evidence source, confidence, contribution, assessment state, integrity fingerprint, and concrete containment actions | Fingerprint detects a changed exported payload but is not represented as a digital signature or external validation |
| Operational Readiness | No-training policy, feed terms and activation state, outcome counts, quality terminology, and privacy posture | Outcome counts remain review data; they never claim measured classifier accuracy or automatic retraining |
| Guided demo | End-to-end scan, explainability, response, and report generation in a repeatable short path | The scenario is explicitly fictional and contains no live indicator claim or hidden network action |

## Operational triage rationale

MITRE ATT&CK identifies phishing as technique **T1566** within Initial Access and describes delivery through malicious attachments, links, and third-party services, including social platforms. Its detection guidance emphasizes correlating message metadata, file creation, process execution, and network activity when those telemetry sources exist.[3] Aegis does not claim endpoint telemetry it does not possess; its triage surface must instead make the available email, URL, file, and evidence-family observations explicit and package them for a human reviewer.

NIST SP 800-61r3 frames incident response as an organizational capability that connects preparation, detection, response, and continuous improvement. A casefile and review queue therefore need measurable states, reviewer decisions, and a clear boundary between a human-confirmed outcome and the assessment engine itself.[4]

[3] [MITRE ATT&CK, *Phishing: T1566*](https://attack.mitre.org/techniques/T1566/)

[4] [NIST, *SP 800-61r3: Incident Response Recommendations and Considerations for Cybersecurity Risk Management*](https://nvlpubs.nist.gov/nistpubs/specialpublications/nist.sp.800-61r3.pdf)

## Selected next increment

The next increment will add an **Analyst Triage Queue** and an **Engine Conformance Scorecard** to the administrator experience. The triage queue will surface bounded, high-risk persisted assessments, their state, strongest evidence families, and latest human-review outcome. Reviewers will continue to use the existing auditable outcome endpoint; the queue itself will not create automatic policy decisions, public reports, or rule changes.

The scorecard will execute a compact, versioned set of fictional deterministic fixtures through the production text parser and evidence-fusion engine. It will show each expected property, observed result, and a pass/fail summary. It is deliberately a *conformance test suite*, not a benchmark, live-threat feed, or claim of detection accuracy. Together these capabilities demonstrate both operational workflow and engineering discipline.

| Capability | Contest question answered | Boundary |
| --- | --- | --- |
| Analyst Triage Queue | Can an operator turn evidence into a controlled decision rather than stare at a dashboard? | Only persisted high/critical scans are listed; review remains human and separately logged. |
| Conformance Scorecard | How does the project detect regression without a black-box accuracy number? | Fictitious fixed fixtures validate intended contracts; no accuracy or real-world generalization claim is made. |
