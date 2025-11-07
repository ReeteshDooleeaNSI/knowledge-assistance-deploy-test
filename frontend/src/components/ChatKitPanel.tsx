import { ChatKit, useChatKit } from "@openai/chatkit-react";
import type { ColorScheme } from "../hooks/useColorScheme";
import {
  KNOWLEDGE_CHATKIT_API_DOMAIN_KEY,
  KNOWLEDGE_CHATKIT_API_URL,
  KNOWLEDGE_COMPOSER_PLACEHOLDER,
  KNOWLEDGE_GREETING,
  KNOWLEDGE_STARTER_PROMPTS,
} from "../lib/config";

type ChatKitPanelProps = {
  theme: ColorScheme;
  onThreadChange: (threadId: string | null) => void;
  onResponseCompleted: () => void;
};

export function ChatKitPanel({
  theme,
  onThreadChange,
  onResponseCompleted,
}: ChatKitPanelProps) {
  const isDark = theme === "dark";
  const accentPrimary = "#97D4C6";
  const accentSecondary = "#F5CC80";
  const emphasis = "#1D345E";

  const chatkit = useChatKit({
    api: {
      url: KNOWLEDGE_CHATKIT_API_URL,
      domainKey: KNOWLEDGE_CHATKIT_API_DOMAIN_KEY,
    },
    theme: {
      colorScheme: theme,
      color: {
        grayscale: {
          hue: 215,
          tint: isDark ? 3 : 8,
          shade: isDark ? -2 : -4,
        },
        accent: {
          primary: isDark ? accentSecondary : emphasis,
          level: 2,
        },
      },
      radius: "round",
    },
    startScreen: {
      greeting: KNOWLEDGE_GREETING,
      prompts: KNOWLEDGE_STARTER_PROMPTS,
    },
    composer: {
      placeholder: KNOWLEDGE_COMPOSER_PLACEHOLDER,
    },
    threadItemActions: {
      feedback: false,
    },
    onResponseEnd: () => {
      onResponseCompleted();
    },
    onThreadChange: ({ threadId }) => {
      onThreadChange(threadId ?? null);
    },
    onError: ({ error }) => {
      // ChatKit propagates the error to the UI; keep logging for debugging.
      console.error("ChatKit error", error);
    },
  });

  return (
    <div className="relative h-full w-full overflow-hidden rounded-[12px] border border-brand-primary/30 bg-white shadow-[0_30px_70px_rgba(29,52,94,0.12)] dark:border-brand-primary/40 dark:bg-[#14243b]" style={{ height: "600px" }}>
      <ChatKit
        control={chatkit.control}
        className="block h-full w-full text-[1.05rem] leading-relaxed font-sans"
        style={{
          fontFamily:
            '"Montserrat", "Arial", "Helvetica", "メイリオ", "ヒラギノ角ゴ pro w3", sans-serif',
        }}
      />
    </div>
  );
}
