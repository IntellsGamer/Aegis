# Learning Localization and Dark-Theme Validation

## Initial Waitress check

On 2026-08-15, the current AEGIS build was served through a native Waitress instance on port 8012. The English Learning Center populated all five lesson cards, both quiz cards, four simulator scenarios, and progress statistics. After switching the active page to Persian, those dynamic cards displayed native Persian titles, summaries, categories, quiz descriptions, pass labels, simulator names, and progress labels. This confirms that the former empty lesson view was not an unavailable-content condition: it was caused by the detail endpoint serializing fields from the service wrapper rather than its `lesson` record.

The next checks cover a complete Persian lesson, a full Persian quiz flow, a Persian casefile response playbook, and the revised graphite dark-mode surfaces.

## Complete Persian lesson

The selected `what-is-phishing` lesson rendered its translated heading, category, reading time, full multi-paragraph explanation, example, four native Persian safety tips, back control, and completion action. This directly confirms the previously empty detail card is repaired.

## Persian quiz

The `phishing-101` quiz opened with a Persian title, the first translated question, and all four translated answer choices. The content is rendered as an interactive question rather than an empty state, and the available quiz card remains visible in the side rail.

## Persian casefile and graphite dark mode

The casefile for the guided assessment rendered fully localized evidence titles, descriptions, severity text, evidence-family labels, response playbook actions, containment ownership, provenance, and limitations. The top-level raw scan target remains intentionally unchanged because it is observed evidence, not interface copy. The dark Learning Center and casefile use a graphite canvas and warm charcoal cards rather than the prior blue-black field; cyan is now limited to focus, operational state, and selected-navigation emphasis.

## Dashboard bootstrap

The Persian dark dashboard initialized through the isolated Waitress server with populated metrics, scan rows, and both charts. Its browser console contained no output, including none of the former `window.Aegis` destructuring exception.
