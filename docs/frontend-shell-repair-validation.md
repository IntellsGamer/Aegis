# Frontend shell repair validation

## Local browser check — 2026-08-15

The authenticated dashboard was rechecked after removing the browser-time Tailwind runtime. The browser loaded only the local `static/css/tailwind.css` and `static/css/app.css` stylesheets. `window.tailwind` was absent, while both the local Turbo Drive bundle and the shared `window.Aegis` bootstrap were present.

The computed desktop `.app-main` offset was `248px` with `data-authenticated="true"` and a visible sidebar. The stylesheet now scopes the desktop offset to `body[data-authenticated="true"] .app-main`; public and account-entry routes therefore receive no sidebar reservation. Automated page tests assert this anonymous/authenticated shell contract, local-asset loading, removal of the legacy runtime, and the scanner’s page-module bootstrap.

A Turbo-driven dashboard-to-scanner navigation was also exercised. The scanner workspace and controls initialized successfully, and the browser console contained neither the previous `window.Aegis` destructuring error nor a Turbo body-script placement warning after Turbo was moved into the document head.

The initial one-time page-module registry revealed a late-registration edge case: a dashboard first reached through Turbo could retain skeleton content because its initializer registered after the lifecycle event. The registry now executes a newly registered module immediately when the document is already ready, and clears per-page completion state before Turbo renders a replacement body. A retest confirmed the dashboard populated its metrics, scan rows, and locally bundled Chart.js graphs; a subsequent Turbo dashboard-to-scanner transition rendered the scanner controls with an empty browser console.
