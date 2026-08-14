# Aegis Competition Demonstration Guide

## The thesis

> **Aegis is not a black-box “scam detector.” It is a digital-trust decision system that preserves evidence, shows its limits, guides containment, and converts only reviewed information into community intelligence.**

The strongest demonstration is not a feature tour. It tells a single story: a suspicious communication reaches a citizen; Aegis turns its observable cues into a clear assessment; the result becomes a reviewable casefile; and operators can show exactly how intelligence and feedback are governed.

| Segment | Time | What to show | Point to make |
| --- | ---: | --- | --- |
| Problem and principle | 0:00–0:25 | Scan Analyzer landing state | Most tools say “safe” or “dangerous.” Aegis shows evidence, coverage, and uncertainty. |
| Real assessment path | 0:25–1:15 | `/scan?demo=credential-lure`, then **Analyze** | This is fictional, repeatable sample content. It is assessed by the normal deterministic engine, not a hard-coded demo result. |
| Explainability and action | 1:15–2:10 | Result evidence and **Open Casefile** | Independent evidence families are separated; contribution and reliability are visible; recommended containment is concrete. |
| Analyst-grade record | 2:10–2:55 | Casefile: evidence chain, playbook, integrity fingerprint, limitations | A result becomes a reviewable record. The fingerprint is an integrity aid, not a signature. Completion checkboxes stay local to the browser. |
| Accountability | 2:55–3:40 | Admin → **Operational Readiness** | The platform exposes its no-training boundary, feed terms, outcome-review data, retention posture, and coverage terminology. |
| Public trust and close | 3:40–4:00 | Threat Map and final statement | The map contains approved country-level aggregates only; Aegis refuses fabricated precision and unsafe scanning. |

## Exact presenter path

Start on **Scan Analyzer** and say that the product accepts links, emails, messages, QR codes, images, and files, but does not blindly fetch arbitrary destinations. Open the **Load guided demo** control, or navigate directly to `/scan?demo=credential-lure`. Explain that the content is deliberately fictional and that it only populates the editor: the user must still select **Analyze**.

When the result appears, draw attention to the separation between the verdict, evidence confidence, and individual observations. Explain that repeated signals are not simply piled up: evidence is fused by family so that correlated clues do not masquerade as independent proof. The UI can also surface a **Limited assessment** when a hostname cannot be resolved and a **Safety boundary applied** state when a destination must not be probed. Those states are a strength, because the platform never converts lack of visibility into a false assurance.

Open the **Assessment casefile**. Explain the four evidence-family cards, the evidence chain, and the response playbook. Marking a response step complete demonstrates practical use but only changes local browser state; it neither alters the result nor writes a public report. Open the integrity disclosure and state precisely that it is a SHA-256 fingerprint of the exported payload—not a cryptographic signature, a blockchain claim, or external verification.

Finally, sign in as an operator and choose **Operational Readiness**. This is where Aegis answers the question a serious evaluator will ask: *what prevents the system from becoming an ungoverned prediction box?* Show the deterministic engine disclosure, the non-training boundary, the explicit feed terms, outcome-review counts, and the statement that evidence confidence is coverage and agreement—not claimed measured accuracy. Finish with the map’s country-level, approved-only provenance.

## Likely jury questions and grounded answers

| Question | Grounded answer |
| --- | --- |
| Why no LLM or trained classifier? | Aegis deliberately uses deterministic evidence fusion. This makes reasons, weights, evidence families, and limitations inspectable. User feedback is stored for review, not silently used to retrain a model or change rules. |
| Does a high score prove a site is safe? | No. Aegis states that confidence describes coverage and agreement, not a guarantee. A limited assessment is explicitly unverified. |
| How do you protect users during scanning? | Private, reserved, loopback, malformed, and non-web destinations are blocked at the acquisition boundary. File uploads undergo type and static-safety checks before text analysis. |
| Where does public threat intelligence come from? | Local indicators and optional governed feeds are separated. External feeds remain disabled until terms are accepted. Community reports are moderated, and the public map uses only approved country-level aggregates. |
| What happens after someone detects a likely phish? | The casefile provides containment steps and a portable JSON record. Users may submit a separate, moderated threat report or a quality outcome; neither action automatically changes public intelligence or the engine. |

## Integrity boundaries worth stating voluntarily

Aegis does not establish attribution, make criminal claims, or claim a live URL is malicious only because its name looks suspicious. It does not expose exact reporter or victim locations on the public map. It does not describe evidence confidence as benchmark accuracy. It does not execute uploaded documents or crawl private network targets. These are deliberate engineering boundaries, not missing polish.

The product maps to practical anti-phishing guidance: prevention combines user-facing recognition with containment, reporting, sender/authentication controls, and phishing-resistant MFA—not a single model score.[1] NIST similarly treats phishing resistance as an authenticator property and distinguishes it from ordinary credential checks.[2]

## References

[1] [CISA, NSA, FBI & MS-ISAC, *Phishing Guidance: Stopping the Attack Cycle at Phase One*](https://www.cisa.gov/sites/default/files/2025-03/Phishing%20Guidance%20-%20Stopping%20the%20Attack%20Cycle%20at%20Phase%20One%20508.pdf)

[2] [NIST, *SP 800-63B: Digital Identity Guidelines—Authentication and Authenticator Management*](https://pages.nist.gov/800-63-4/sp800-63b.html)
