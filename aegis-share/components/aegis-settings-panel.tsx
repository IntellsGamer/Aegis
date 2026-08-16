import { useEffect, useMemo, useState } from "react";
import { ActivityIndicator, Alert, Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { type AegisSettings, type BrowserOption, discoverBrowsers, normalizeBaseUrl, saveSettings } from "@/lib/aegis-share";

type Props = {
  initialSettings: AegisSettings | null;
  onSaved: (settings: AegisSettings) => void;
};

export function AegisSettingsPanel({ initialSettings, onSaved }: Props) {
  const [baseUrl, setBaseUrl] = useState(initialSettings?.baseUrl ?? "");
  const [browserKind, setBrowserKind] = useState<"default" | "package">(initialSettings?.browser.kind ?? "default");
  const [selectedPackage, setSelectedPackage] = useState(
    initialSettings?.browser.kind === "package" ? initialSettings.browser.packageName : "",
  );
  const [browsers, setBrowsers] = useState<BrowserOption[]>([]);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    void discoverBrowsers().then(setBrowsers).catch(() => setBrowsers([]));
  }, []);

  const selectedLabel = useMemo(
    () => browsers.find((browser) => browser.packageName === selectedPackage)?.label ?? selectedPackage,
    [browsers, selectedPackage],
  );

  async function submit() {
    try {
      setSaving(true);
      const browser = browserKind === "package" && selectedPackage
        ? { kind: "package" as const, packageName: selectedPackage }
        : { kind: "default" as const };
      const settings = await saveSettings({ baseUrl: normalizeBaseUrl(baseUrl), browser });
      onSaved(settings);
    } catch (error) {
      Alert.alert("Check the AEGIS address", error instanceof Error ? error.message : "Unable to save settings.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <View style={styles.card}>
      <Text style={styles.eyebrow}>CONNECTION SETUP</Text>
      <Text style={styles.title}>{initialSettings ? "Where should shares go?" : "Connect your AEGIS"}</Text>
      <Text style={styles.body}>AEGIS Share stays local. It opens this address in your chosen browser and never scans content itself.</Text>

      <Text style={styles.label}>AEGIS base URL</Text>
      <TextInput
        autoCapitalize="none"
        autoCorrect={false}
        keyboardType="url"
        placeholder="https://aegis.example.com"
        placeholderTextColor="#7A827C"
        value={baseUrl}
        onChangeText={setBaseUrl}
        style={styles.input}
      />
      <Text style={styles.hint}>Use the base address only. AEGIS Share adds `/scan` itself.</Text>

      <Text style={[styles.label, styles.browserLabel]}>Browser</Text>
      <Pressable
        accessibilityRole="radio"
        accessibilityState={{ selected: browserKind === "default" }}
        onPress={() => setBrowserKind("default")}
        style={({ pressed }) => [styles.choice, browserKind === "default" && styles.choiceActive, pressed && styles.pressed]}
      >
        <View style={[styles.radio, browserKind === "default" && styles.radioActive]} />
        <View style={styles.choiceCopy}><Text style={styles.choiceTitle}>Device default browser</Text><Text style={styles.choiceDetail}>Use Android’s current default.</Text></View>
      </Pressable>

      {browsers.map((browser) => (
        <Pressable
          key={browser.packageName}
          accessibilityRole="radio"
          accessibilityState={{ selected: browserKind === "package" && selectedPackage === browser.packageName }}
          onPress={() => { setBrowserKind("package"); setSelectedPackage(browser.packageName); }}
          style={({ pressed }) => [styles.choice, browserKind === "package" && selectedPackage === browser.packageName && styles.choiceActive, pressed && styles.pressed]}
        >
          <View style={[styles.radio, browserKind === "package" && selectedPackage === browser.packageName && styles.radioActive]} />
          <View style={styles.choiceCopy}><Text style={styles.choiceTitle}>{browser.label}</Text><Text numberOfLines={1} style={styles.choiceDetail}>{browser.packageName}</Text></View>
        </Pressable>
      ))}

      {browserKind === "package" && selectedLabel ? <Text style={styles.selectedNote}>Selected: {selectedLabel}</Text> : null}

      <Pressable disabled={saving} onPress={() => void submit()} style={({ pressed }) => [styles.primaryButton, (pressed || saving) && styles.primaryPressed]}>
        {saving ? <ActivityIndicator color="#FFFFFF" /> : <Text style={styles.primaryText}>Save configuration</Text>}
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: "#FFFFFF", borderColor: "#DCE3DD", borderWidth: 1, borderRadius: 24, padding: 20, gap: 12, shadowColor: "#122016", shadowOpacity: 0.06, shadowRadius: 18, elevation: 2 },
  eyebrow: { color: "#0786A6", fontWeight: "800", fontSize: 11, letterSpacing: 1.25 },
  title: { color: "#121816", fontSize: 25, lineHeight: 31, fontWeight: "800" },
  body: { color: "#59635C", fontSize: 14, lineHeight: 21, marginBottom: 6 },
  label: { color: "#263129", fontSize: 13, fontWeight: "800", marginTop: 4 },
  browserLabel: { marginTop: 10 },
  input: { minHeight: 50, borderRadius: 14, borderWidth: 1, borderColor: "#CCD7CE", paddingHorizontal: 14, color: "#121816", backgroundColor: "#F8FAF8", fontSize: 15 },
  hint: { color: "#717A73", fontSize: 12, lineHeight: 17 },
  choice: { minHeight: 62, flexDirection: "row", alignItems: "center", gap: 12, borderRadius: 15, paddingHorizontal: 14, borderWidth: 1, borderColor: "#DEE6DF", backgroundColor: "#FFFFFF" },
  choiceActive: { borderColor: "#0786A6", backgroundColor: "#EFFBFD" },
  pressed: { opacity: 0.72 },
  radio: { width: 20, height: 20, borderRadius: 10, borderWidth: 2, borderColor: "#9BA69E" },
  radioActive: { borderColor: "#0786A6", borderWidth: 6 },
  choiceCopy: { flex: 1, gap: 2 },
  choiceTitle: { color: "#18211B", fontWeight: "700", fontSize: 14 },
  choiceDetail: { color: "#6B756E", fontSize: 12 },
  selectedNote: { color: "#397E63", fontSize: 12 },
  primaryButton: { minHeight: 52, marginTop: 8, alignItems: "center", justifyContent: "center", backgroundColor: "#0786A6", borderRadius: 15 },
  primaryPressed: { opacity: 0.82, transform: [{ scale: 0.98 }] },
  primaryText: { color: "#FFFFFF", fontSize: 15, fontWeight: "800" },
});
