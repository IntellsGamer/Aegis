import { router } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useShareIntentContext } from "expo-share-intent";

import { AegisSettingsPanel } from "@/components/aegis-settings-panel";
import { ScreenContainer } from "@/components/screen-container";
import {
  type AegisSettings,
  type PendingHandoff,
  classifySharedContent,
  clearPendingHandoff,
  createPendingHandoff,
  loadPendingHandoff,
  loadSettings,
  openAegisScan,
  savePendingHandoff,
} from "@/lib/aegis-share";

export default function HomeScreen() {
  const { hasShareIntent, shareIntent, resetShareIntent, error: shareError } = useShareIntentContext();
  const [settings, setSettings] = useState<AegisSettings | null>(null);
  const [pending, setPending] = useState<PendingHandoff | null>(null);
  const [loading, setLoading] = useState(true);
  const [opening, setOpening] = useState(false);
  const consumedShare = useRef<string | null>(null);

  useEffect(() => {
    void Promise.all([loadSettings(), loadPendingHandoff()]).then(([loadedSettings, loadedPending]) => {
      setSettings(loadedSettings);
      setPending(loadedPending);
      setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (!hasShareIntent) return;
    const key = `${shareIntent.type ?? ""}|${shareIntent.webUrl ?? ""}|${shareIntent.text ?? ""}`;
    if (consumedShare.current === key) return;
    consumedShare.current = key;
    const classified = classifySharedContent(shareIntent.text ?? null, shareIntent.webUrl ?? null);
    resetShareIntent();
    if (!classified) return;
    const handoff = createPendingHandoff(classified);
    void savePendingHandoff(handoff).then(() => setPending(handoff));
  }, [hasShareIntent, resetShareIntent, shareIntent.text, shareIntent.type, shareIntent.webUrl]);

  const launch = useCallback(async () => {
    if (!settings || !pending || opening) return;
    try {
      setOpening(true);
      await openAegisScan(settings, pending);
      await clearPendingHandoff();
      setPending(null);
    } catch (error) {
      Alert.alert("Browser handoff failed", error instanceof Error ? error.message : "Your shared content is still saved. Try again from AEGIS Share.");
    } finally {
      setOpening(false);
    }
  }, [opening, pending, settings]);

  useEffect(() => {
    if (settings && pending && !opening) void launch();
  }, [launch, opening, pending, settings]);

  return (
    <ScreenContainer className="px-5" edges={["top", "bottom", "left", "right"]}>
      <ScrollView contentContainerStyle={styles.scroll} showsVerticalScrollIndicator={false}>
        <View style={styles.brandRow}>
          <View style={styles.logoMark}><Text style={styles.logoGlyph}>A</Text></View>
          <View><Text style={styles.brand}>AEGIS SHARE</Text><Text style={styles.brandDetail}>Android share-to-scan companion</Text></View>
        </View>

        {loading ? <View style={styles.loading}><ActivityIndicator color="#0786A6" /></View> : !settings ? (
          <AegisSettingsPanel initialSettings={null} onSaved={setSettings} />
        ) : (
          <View style={styles.readyCard}>
            <View style={styles.statusDot} />
            <Text style={styles.eyebrow}>READY FOR ANDROID SHARE</Text>
            <Text style={styles.readyTitle}>Send suspicious messages to AEGIS in one step.</Text>
            <Text style={styles.readyBody}>Long-press a message or link, choose Share, then select AEGIS Share. Your browser opens directly to the right scan type.</Text>
            <View style={styles.destination}><Text style={styles.destinationLabel}>AEGIS DESTINATION</Text><Text numberOfLines={1} style={styles.destinationValue}>{settings.baseUrl}</Text></View>
            {pending ? (
              <View style={styles.handoffCard}>
                <Text style={styles.handoffLabel}>{pending.mode === "url" ? "URL CHECK READY" : "MESSAGE CHECK READY"}</Text>
                <Text numberOfLines={4} style={styles.handoffPreview}>{pending.content}</Text>
                <Pressable onPress={() => void launch()} style={({ pressed }) => [styles.primaryButton, (pressed || opening) && styles.primaryPressed]}>
                  {opening ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryText}>Open AEGIS now</Text>}
                </Pressable>
              </View>
            ) : null}
            {shareError ? <Text style={styles.errorText}>Share receiver: {shareError}</Text> : null}
            <Pressable onPress={() => router.push("/settings" as never)} style={({ pressed }) => [styles.secondaryButton, pressed && styles.secondaryPressed]}>
              <Text style={styles.secondaryText}>Configure AEGIS & browser</Text>
            </Pressable>
          </View>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  scroll: { flexGrow: 1, justifyContent: "center", paddingVertical: 24, gap: 24 },
  brandRow: { flexDirection: "row", alignItems: "center", gap: 12 },
  logoMark: { width: 42, height: 42, borderRadius: 14, alignItems: "center", justifyContent: "center", backgroundColor: "#121816" },
  logoGlyph: { color: "#62D9E8", fontWeight: "900", fontSize: 22 },
  brand: { color: "#172019", fontSize: 14, fontWeight: "900", letterSpacing: 1.2 },
  brandDetail: { color: "#717A73", fontSize: 12, marginTop: 2 },
  loading: { minHeight: 320, alignItems: "center", justifyContent: "center" },
  readyCard: { backgroundColor: "#FFFFFF", borderColor: "#DCE3DD", borderWidth: 1, borderRadius: 26, padding: 22, gap: 14, shadowColor: "#122016", shadowOpacity: 0.07, shadowRadius: 18, elevation: 2 },
  statusDot: { width: 10, height: 10, borderRadius: 5, backgroundColor: "#16A36A", position: "absolute", right: 23, top: 26 },
  eyebrow: { color: "#0786A6", fontWeight: "900", fontSize: 11, letterSpacing: 1.15 },
  readyTitle: { color: "#121816", fontSize: 26, lineHeight: 33, fontWeight: "900", paddingRight: 14 },
  readyBody: { color: "#59635C", fontSize: 14, lineHeight: 22 },
  destination: { backgroundColor: "#F1F7F3", borderRadius: 15, padding: 14, gap: 4 },
  destinationLabel: { color: "#5C6D61", fontSize: 10, fontWeight: "900", letterSpacing: 1 },
  destinationValue: { color: "#263129", fontSize: 14, fontWeight: "700" },
  handoffCard: { backgroundColor: "#EDF9FC", borderColor: "#BCE7EE", borderWidth: 1, borderRadius: 16, padding: 14, gap: 9 },
  handoffLabel: { color: "#08738B", fontSize: 10, letterSpacing: 1, fontWeight: "900" },
  handoffPreview: { color: "#142729", fontSize: 14, lineHeight: 20 },
  primaryButton: { minHeight: 50, borderRadius: 14, backgroundColor: "#0786A6", justifyContent: "center", alignItems: "center", marginTop: 2 },
  primaryPressed: { opacity: 0.83, transform: [{ scale: 0.98 }] },
  primaryText: { color: "#FFFFFF", fontSize: 15, fontWeight: "900" },
  secondaryButton: { minHeight: 48, borderRadius: 14, justifyContent: "center", alignItems: "center", borderColor: "#CAD5CC", borderWidth: 1 },
  secondaryPressed: { opacity: 0.72 },
  secondaryText: { color: "#1D3225", fontSize: 14, fontWeight: "800" },
  errorText: { color: "#B12242", fontSize: 12, lineHeight: 18 },
});
