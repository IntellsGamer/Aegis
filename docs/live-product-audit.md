# Live Product Audit — 2026-08-14

The authenticated dashboard loads correctly but presents empty line charts as if they contained meaningful data. It needs a deliberate first-run state that explains how to start, rather than zero-value charts and an uncontextualized “Savings Estimate.”

The scan workflow is technically clear but operationally incomplete. The primary result uses the same “Threat” language for scanner-boundary failures and malicious evidence. In a live test, an unresolvable `.example` hostname appeared as **Unsafe destination blocked** and a **Threat** verdict. The product must distinguish an unverified/blocked acquisition from a confirmed malicious destination, while retaining the safe-fetch boundary.

The results page needs a tighter incident workflow: an outcome/feedback action, a copyable indicator or case reference, a clear storage statement, and an explanation of what was and was not checked. Current “Report as Threat” is too close to a high-confidence assertion and lacks a moderation-state explanation.

The file control advertises `.doc` and `.docx`, while the server safely accepts only PDF, TXT, EML, and MSG. This is a direct UI/server contract bug. The screen should state the real supported formats and static safety behavior.

The profile page exposes only email notifications. It omits the existing history/privacy settings, supported language/RTL controls, theme choice, scan storage controls, and an easy way to understand data handling. Those controls should be made explicit before users analyze sensitive messages.

The implemented improvement set should therefore prioritize: (1) evidence-boundary-aware scan classification, (2) result actions and outcome feedback, (3) truthful input/storage guidance, (4) a real first-run dashboard, and (5) accessible privacy/preferences controls.
