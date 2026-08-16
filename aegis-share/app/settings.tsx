import { router } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, StyleSheet, View } from "react-native";

import { AegisSettingsPanel } from "@/components/aegis-settings-panel";
import { ScreenContainer } from "@/components/screen-container";
import { type AegisSettings, loadSettings } from "@/lib/aegis-share";

export default function SettingsScreen() {
  const [settings, setSettings] = useState<AegisSettings | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    void loadSettings().then((value) => { setSettings(value); setLoading(false); });
  }, []);

  return (
    <ScreenContainer className="px-5" edges={["top", "bottom", "left", "right"]}>
      <View style={styles.content}>
        {loading ? <ActivityIndicator color="#0786A6" /> : <AegisSettingsPanel initialSettings={settings} onSaved={() => router.replace("/")} />}
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({ content: { flex: 1, justifyContent: "center" } });
