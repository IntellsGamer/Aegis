# AEGIS Share — Native Android Interface Design

## Product intent

AEGIS Share is a small, native Android companion for the existing AEGIS anti-phishing service. It reduces the unsafe copy–open browser–paste workflow to a single Android Share-sheet action. The application does not analyze content itself and does not replace the AEGIS website; it receives shared content, lets the user keep control of the destination and browser, then opens the configured AEGIS instance with a protected scan handoff.

## Screen list

| Screen | Primary content and functionality |
|---|---|
| Setup | First-run configuration for the AEGIS base URL and the browser preference: Android default browser or a chosen installed browser. Includes a connection-safe URL validation explanation and saves settings locally. |
| Ready | A compact confirmation screen shown when the app is opened normally. It shows the configured AEGIS instance, browser preference, and actions to update settings or open AEGIS. |
| Share review | A transient screen shown when Android sends text or a URL through the Share sheet. It presents a short redacted preview, identifies whether the handoff will use Message or URL scan mode, and opens the configured browser. |
| Settings | Lets the user change the AEGIS base URL and browser preference, restore the Android default browser, and inspect the privacy behavior. |
| Handoff error | Explains why the browser could not be opened, preserves the shared content in local encrypted storage, and provides a retry action. |

## Key user flows

1. **First launch:** User opens AEGIS Share → enters their AEGIS URL, for example `http://192.168.1.5:8000` or public HTTPS URL → selects Default browser or an installed browser → saves → sees the Ready screen.
2. **Share a message:** User long-presses a message in Android → Share → AEGIS Share → the Share review screen classifies content as Message → app stores a short-lived pending handoff locally → app launches the selected browser to `/scan` with a signed handoff reference → the website opens Message scan mode with the shared text filled in.
3. **Sign-in continuation:** If the AEGIS website needs authentication, it preserves the pending scan intent in browser session storage and redirects to login → successful sign-in returns to `/scan` and restores the selected scan mode and content.
4. **Share a URL:** User shares a URL → AEGIS Share identifies URL-only content → opens AEGIS in URL scan mode with the URL prefilled. The companion never treats text containing a URL as URL-only when it also carries message context.
5. **Browser failure:** If no preferred package can handle the URL, the app falls back to Android’s resolver/default browser. If that fails, it keeps the pending payload locally and offers retry/copy actions without silently losing the shared text.

## Mobile layout and interaction details

The portrait-first layout uses a single column and 20–24pt horizontal spacing for one-handed use. The primary action occupies the bottom portion of its card with a 48pt minimum touch target. The share review’s preview is intentionally capped and fades after several lines so private content does not persist visibly longer than necessary. Selection controls use iOS/Android-native-feeling rows: a label, a concise current value, and a chevron; browser package selection is a compact modal sheet.

## Brand and color choices

The native companion continues the AEGIS product language without copying the website’s dense desktop shell. The primary ink is **#121816**, the surface is **#F7F9F8**, and the structured panel is **#FFFFFF**. Operational cyan is **#0786A6**, used only for the handoff action and active selection. Trust green is **#16A36A**, caution amber is **#B96A00**, and threat red is **#C9284E**. Graphite dark mode uses **#161816** background, **#20231F** panels, and warm-grey divider **#363A35**; it avoids pure black and blue-grey glare.

## Data model and privacy boundary

| Entity | Fields | Storage and retention |
|---|---|---|
| AppSettings | `baseUrl`, `browserMode`, `browserPackage` | Android secure local storage; retained until changed by the user. |
| PendingHandoff | `id`, `content`, `scanMode`, `createdAt` | Secure local storage; consumed after browser handoff or expires after a short fixed interval. |
| WebsiteHandoff | `mode`, `payload`, `createdAt` | Browser session storage only; survives sign-in navigation but not an intentional browser session reset. |

The native app makes no network request and does not upload shared content. The selected browser sends the payload only to the user-configured AEGIS base URL.
