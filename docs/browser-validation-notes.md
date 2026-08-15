# Browser Validation Notes

## Completed checks

| Area | Result | Evidence |
| --- | --- | --- |
| Threat map | Passed | OpenStreetMap tiles rendered; an honest empty state showed zero approved reports with country-level provenance. |
| Limited assessment | Passed after scanner refinement | An unresolved `paypa1-login.example` URL rendered **Limited assessment** and an **Unverified** verdict, while preserving local typosquatting and credential-lure evidence. |
| Blocked assessment | Passed | A loopback target rendered **Safety boundary applied** with a threat verdict and the private-network fetch prohibition. |
| Evidence copy | Passed | The live result displayed the "Evidence summary copied" confirmation. |
| Feedback workflow | Passed | A stored scan accepted a neutral user outcome and replaced its controls with a quality-review confirmation. |
| First-run dashboard | Passed | A new validation account displayed the first-run guidance, zero stats, meaningful "Needs attention" label, no canvases, and the empty-history action. |
| Profile API hydration | Passed | Live profile identity, locale, theme, retention, contrast, and notification values loaded in the rewritten page. |
| Profile save | Passed after fix | The save action displayed a successful confirmation. |
| Light theme | Passed | The profile saved light mode and the sidebar remained correctly light. |
| Dark theme | Passed | The global toggle rendered the profile, scanner, dashboard, and navigation in coherent dark mode. |

## Defects found and corrected during validation

1. The profile preference action called a theme helper that was not exposed by the shared client. The helper is now exported, and `unverified` is presented with a proper label rather than raw lowercase text.
2. Feedback confirmation from one assessment remained visible after beginning a different scan. The client now clears scan state and restores a fresh, event-delegated feedback panel for each assessment.
3. DNS-limited scans initially discarded safe-to-evaluate local URL clues. They now preserve local typosquatting, suspicious-keyword, punycode, `@`-obfuscation, and local-indicator evidence without making a remote request.
4. A reachable `example.com` scan exposed a false-positive typosquatting match caused by whole-host similarity and one-character brand tokens. The lexical matcher is being constrained to the registrable domain label and its tokens.

## Pending revalidation

After the typosquatting correction, re-run the reachable-domain browser scan to verify `example.com` is no longer treated as an impersonation, then rerun full tests, smoke validation, and continuous-integration status.

## Precision recheck in progress

The scanner was reloaded after the matcher change, and a fresh `https://example.com/` assessment has been prepared in the browser. The next result will confirm that the former lexical false positive is gone while standard reachable-domain checks still complete.

The post-fix reachable-domain scan remained in its explicit loading state after the initial short wait; this is expected while bounded DNS, TLS, WHOIS, and page checks execute. Final result inspection remains pending.

## Final reachable-domain precision recheck

The post-fix browser scan of `https://example.com/` completed as **Safe** with a 94.2/100 trust score. Its evidence set contained only the legitimate HTTPS and certificate observations; the earlier typosquatting finding was absent. This confirms the false-positive correction in the live product.

## Contest walkthrough check

The live `scan?demo=credential-lure` path loaded an explicitly labelled fictional email without submitting automatically. After the user-facing Analyze action, the normal deterministic engine produced a threat assessment from multiple independent email and URL cues, displayed its evidence, and exposed the new **Open Casefile** transition. No live threat-intelligence confirmation was claimed.

The live casefile rendered the recorded evidence families, detailed evidence chain, browser-local containment checklist, limitations, SHA-256 integrity fingerprint, and source disclosure. After the provenance correction, the email case correctly displayed `network_acquisition: not_applicable` rather than implying a remote fetch.

The end-user casefile path was exited cleanly and the browser was prepared for an administrator-only readiness review using the seeded local administrator account.

The administrator session successfully exposed the renamed **Operational Readiness** tab in place of the obsolete ML-training control. The dashboard and administrative data remained accessible after the feature update.

The public landing page now presents deterministic evidence fusion, assessment boundaries, casefile preservation, and a visible guided-demo entry point. The obsolete ML claim has been removed from the user-facing narrative.

## Operations and conformance check

The live **Engine Conformance** administrator panel rendered three fictional, local-only deterministic fixtures with a 3/3 pass result. Each card exposed its expected contract and observed risk, score, confidence, and finding-code checks. The view explicitly stated that it is a regression conformance suite—not a benchmark or measured accuracy claim.

The live Analyst Triage panel initially revealed that a safety-boundary block could be presented for maliciousness confirmation. The queue was corrected to exclude `unsafe_destination` assessments because a refused network acquisition is not evidence of maliciousness. Focused regressions passed; the live panel was then reloaded for the corrected state.

## Persian header localization check

The live header selector successfully persisted `fa`, reloaded the scanner into an RTL document, moved the sidebar to the right, and translated the navigation plus the core scan DOM into Persian. The first rendered screenshot showed a transient English visual layer during reload, so a follow-up visual refresh and route check is required before accepting the RTL presentation as complete.
The settled Persian scanner rendered correctly in RTL: sidebar right, search and header controls mirrored, navigation and core scan content translated, and the language selector showed Persian as active. The guided demo also switched into the Persian email form successfully, including translated labels, placeholder, action button, and feedback toast.
The Persian scanner was reloaded after fixing feedback-panel reset localization. The refreshed page retained the persisted Persian locale, dark-theme RTL layout, right-side navigation, translated header/search/scan controls, and translated footer without the transient English layer.
The refreshed Persian guided-demo result rendered with Persian assessment state, score/evidence labels, verdict badge, result actions, and—after the reset fix—a fully translated outcome-feedback panel. Recorded evidence titles and response recommendations intentionally remain in their source language because they are evidence payloads rather than interface chrome.
The English round trip returned the full profile and preference workflow to its original LTR rendering, including the header selector and no stale RTL layout state. The refreshed profile template retained its English labels and real API-bound controls.
The settled Persian profile view rendered its account, privacy, notification, language, and password controls in RTL Persian. Its danger-zone content remained English and is outside the completed core preference translation set; the current typography pass focuses on the common English/Persian UI font treatment and direction safeguards.
The browser confirmed the final Persian profile state as `lang=fa`, `dir=rtl`, and localization-ready before display. Computed typography resolved to `Vazirmatn Local`, and the browser Font Loading API confirmed the locally bundled Vazirmatn face was loaded.
The browser confirmed the English profile state as `lang=en`, `dir=ltr`, and localization-ready. Computed typography resolved to `Inter Local`, and the browser Font Loading API confirmed Inter was loaded from the bundled local asset. No Persian font or RTL state remained after the round trip.
The remaining profile danger-zone strings and deletion confirmation were subsequently added to the Persian catalog before the final automated validation pass.
