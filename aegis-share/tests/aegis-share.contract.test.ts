import { describe, expect, it } from "vitest";

import { classifySharedContent, encodeHandoffFragment, normalizeBaseUrl } from "../lib/aegis-share-contract";

describe("AEGIS Share handoff contract", () => {
  it("classifies an exact shared HTTP URL as a URL assessment", () => {
    expect(classifySharedContent("https://example.com/login", "https://example.com/login")).toEqual({
      mode: "url",
      content: "https://example.com/login",
    });
  });

  it("preserves a message containing a link as a Message assessment", () => {
    expect(classifySharedContent("Urgent: verify https://example.com/login", "https://example.com/login")).toEqual({
      mode: "message",
      content: "Urgent: verify https://example.com/login",
    });
  });

  it("rejects credentials and paths in the configured AEGIS base URL", () => {
    expect(normalizeBaseUrl("https://aegis.example.com/")).toBe("https://aegis.example.com");
    expect(() => normalizeBaseUrl("https://user:secret@aegis.example.com")).toThrow("base address only");
    expect(() => normalizeBaseUrl("https://aegis.example.com/scan")).toThrow("base address only");
  });

  it("encodes handoff content into a fragment rather than a network query", () => {
    const fragment = encodeHandoffFragment({ v: 1, mode: "message", content: "code 1234", createdAt: 1 });
    expect(fragment).toMatch(/^aegis-share=/);
    expect(fragment).not.toContain("?aegis-share=");
    expect(JSON.parse(decodeURIComponent(fragment.slice("aegis-share=".length)))).toMatchObject({ mode: "message", content: "code 1234" });
  });
});
