# AEGIS Share

AEGIS Share is the native Android companion for the [AEGIS](https://github.com/IntellsGamer/Aegis) anti-phishing platform. It registers in Android’s Share sheet for shared text and URLs, classifies the shared item locally, then opens the selected browser at the AEGIS scan page with a short-lived fragment handoff. The website validates the handoff, selects the appropriate scanner tab, pre-fills the content, and preserves it through sign-in.

## First use

Open the app once and set the **AEGIS base URL**. For a local AEGIS server running on your LAN, use a reachable address such as `http://192.168.1.25:8000`, not `localhost`. Select either the Android default browser or a specific installed browser.

Then long-press a message or URL in another Android app, choose **Share**, and choose **AEGIS Share**. The browser opens AEGIS’s `/scan` page with the content ready for review. The app never uploads the shared text itself.

## Native Android build

The share target depends on `expo-share-intent`, so it requires a development or release build and does not work in Expo Go.

```bash
pnpm install
npx eas-cli build --platform android --profile preview
```

The `preview` profile emits an installable APK. A locally generated debug package can also be built after Android SDK setup:

```bash
npx expo prebuild --platform android
cd android && ./gradlew assembleDebug
```

## Validation

```bash
pnpm run check
pnpm test
```
