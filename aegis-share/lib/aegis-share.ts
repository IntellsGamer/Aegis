import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";
import * as WebBrowser from "expo-web-browser";
import { Linking, Platform } from "react-native";
import {
  classifySharedContent,
  encodeHandoffFragment,
  normalizeBaseUrl,
  type ScanMode,
} from "@/lib/aegis-share-contract";

export { classifySharedContent, normalizeBaseUrl, type ScanMode } from "@/lib/aegis-share-contract";

const SETTINGS_KEY = "aegis-share.settings.v1";
const PENDING_KEY = "aegis-share.pending.v1";
const PENDING_SECURE_KEY = "aegis-share.pending-secure.v1";
const PENDING_TTL_MS = 30 * 60 * 1000;
const SECURE_CONTENT_LIMIT = 1800;

export type BrowserPreference =
  | { kind: "default" }
  | { kind: "package"; packageName: string };

export interface AegisSettings {
  baseUrl: string;
  browser: BrowserPreference;
}

export interface PendingHandoff {
  id: string;
  mode: ScanMode;
  content: string;
  createdAt: number;
  expiresAt: number;
}

export interface BrowserOption {
  packageName: string;
  label: string;
}

const browserNames: Record<string, string> = {
  "com.android.chrome": "Google Chrome",
  "org.mozilla.firefox": "Firefox",
  "com.microsoft.emmx": "Microsoft Edge",
  "com.opera.browser": "Opera",
  "com.brave.browser": "Brave",
  "com.sec.android.app.sbrowser": "Samsung Internet",
};

export function createPendingHandoff(payload: { mode: ScanMode; content: string }): PendingHandoff {
  const createdAt = Date.now();
  return {
    ...payload,
    id: `${createdAt}-${Math.random().toString(36).slice(2, 10)}`,
    createdAt,
    expiresAt: createdAt + PENDING_TTL_MS,
  };
}

export async function loadSettings(): Promise<AegisSettings | null> {
  const raw = await AsyncStorage.getItem(SETTINGS_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as AegisSettings;
    return { baseUrl: normalizeBaseUrl(parsed.baseUrl), browser: parsed.browser ?? { kind: "default" } };
  } catch {
    await AsyncStorage.removeItem(SETTINGS_KEY);
    return null;
  }
}

export async function saveSettings(settings: AegisSettings): Promise<AegisSettings> {
  const normalized: AegisSettings = { ...settings, baseUrl: normalizeBaseUrl(settings.baseUrl) };
  await AsyncStorage.setItem(SETTINGS_KEY, JSON.stringify(normalized));
  return normalized;
}

export async function savePendingHandoff(handoff: PendingHandoff): Promise<void> {
  const raw = JSON.stringify(handoff);
  if (Platform.OS !== "web" && raw.length <= SECURE_CONTENT_LIMIT) {
    await SecureStore.setItemAsync(PENDING_SECURE_KEY, raw);
    await AsyncStorage.removeItem(PENDING_KEY);
    return;
  }
  await AsyncStorage.setItem(PENDING_KEY, raw);
  if (Platform.OS !== "web") await SecureStore.deleteItemAsync(PENDING_SECURE_KEY);
}

export async function loadPendingHandoff(): Promise<PendingHandoff | null> {
  const secure = Platform.OS !== "web" ? await SecureStore.getItemAsync(PENDING_SECURE_KEY) : null;
  const raw = secure ?? await AsyncStorage.getItem(PENDING_KEY);
  if (!raw) return null;
  try {
    const pending = JSON.parse(raw) as PendingHandoff;
    if (!pending.content || pending.expiresAt <= Date.now()) {
      await clearPendingHandoff();
      return null;
    }
    return pending;
  } catch {
    await clearPendingHandoff();
    return null;
  }
}

export async function clearPendingHandoff(): Promise<void> {
  await AsyncStorage.removeItem(PENDING_KEY);
  if (Platform.OS !== "web") await SecureStore.deleteItemAsync(PENDING_SECURE_KEY);
}

export function buildAegisScanUrl(settings: AegisSettings, handoff: PendingHandoff): string {
  const fragment = encodeHandoffFragment({ v: 1, mode: handoff.mode, content: handoff.content, createdAt: handoff.createdAt });
  return `${normalizeBaseUrl(settings.baseUrl)}/scan#${fragment}`;
}

export async function discoverBrowsers(): Promise<BrowserOption[]> {
  if (Platform.OS !== "android") return [];
  const result = await WebBrowser.getCustomTabsSupportingBrowsersAsync();
  const packageNames = Array.from(new Set([
    ...(result.browserPackages ?? []),
    ...(result.preferredBrowserPackage ? [result.preferredBrowserPackage] : []),
    ...(result.defaultBrowserPackage ? [result.defaultBrowserPackage] : []),
  ])).sort();
  return packageNames.map((packageName) => ({
    packageName,
    label: browserNames[packageName] ?? packageName,
  }));
}

export async function openAegisScan(settings: AegisSettings, handoff: PendingHandoff): Promise<void> {
  const url = buildAegisScanUrl(settings, handoff);
  if (Platform.OS === "web") {
    await Linking.openURL(url);
    return;
  }
  if (settings.browser.kind === "package") {
    try {
      await WebBrowser.openBrowserAsync(url, {
        browserPackage: settings.browser.packageName,
        createTask: true,
        showInRecents: true,
        toolbarColor: "#161816",
      });
      return;
    } catch {
      // Fall through to Android's browser resolver/default handler.
    }
  }
  const supported = await Linking.canOpenURL(url);
  if (!supported) throw new Error("No browser is available to open your AEGIS address.");
  await Linking.openURL(url);
}
