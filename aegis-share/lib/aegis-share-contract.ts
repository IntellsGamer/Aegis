export type ScanMode = "message" | "url";

export type HandoffFragmentPayload = {
  v: 1;
  mode: ScanMode;
  content: string;
  createdAt: number;
};

function isHttpUrl(value: string): boolean {
  try {
    const url = new URL(value);
    return url.protocol === "https:" || url.protocol === "http:";
  } catch {
    return false;
  }
}

export function normalizeBaseUrl(value: string): string {
  const candidate = value.trim().replace(/\/+$/, "");
  if (!isHttpUrl(candidate)) {
    throw new Error("Enter a complete http:// or https:// AEGIS URL.");
  }
  const parsed = new URL(candidate);
  if (parsed.username || parsed.password || parsed.pathname !== "/" || parsed.search || parsed.hash) {
    throw new Error("Use the AEGIS base address only, without a path or credentials.");
  }
  return parsed.toString().replace(/\/$/, "");
}

export function classifySharedContent(text: string | null, webUrl: string | null): { mode: ScanMode; content: string } | null {
  const raw = (text ?? webUrl ?? "").trim();
  if (!raw) return null;
  const normalizedUrl = webUrl?.trim() ?? null;
  const isUrlOnly = Boolean(normalizedUrl && raw === normalizedUrl && isHttpUrl(normalizedUrl));
  return {
    mode: isUrlOnly ? "url" : "message",
    content: isUrlOnly ? normalizedUrl! : raw,
  };
}

export function encodeHandoffFragment(payload: HandoffFragmentPayload): string {
  return `aegis-share=${encodeURIComponent(JSON.stringify(payload))}`;
}
