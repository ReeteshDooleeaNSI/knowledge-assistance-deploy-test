import { ChatKit, useChatKit } from "@openai/chatkit-react";
import { useEffect } from "react";
import type { ColorScheme } from "../hooks/useColorScheme";
import {
  KNOWLEDGE_CHATKIT_API_DOMAIN_KEY,
  KNOWLEDGE_CHATKIT_API_URL,
  KNOWLEDGE_COMPOSER_PLACEHOLDER,
  KNOWLEDGE_GREETING,
  KNOWLEDGE_STARTER_PROMPTS,
} from "../lib/config";

// Global function for ChatKit to call when ticket.open action is triggered
declare global {
  interface Window {
    handleZohoTicketOpen?: (url: string) => void;
  }
}

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

  useEffect(() => {
    const handleClick = (event: MouseEvent) => {
      const target = event.target as HTMLElement;
      const button = target.closest("button");
      
      if (button && button.textContent?.trim() === "Open in Zoho Desk") {
        // Try to find the widget and extract URL
        let element: HTMLElement | null = button;
        while (element) {
          // Look for widget container
          const widgetKey = element.getAttribute("data-widget-key");
          if (widgetKey === "zoho_ticket") {
            // Search for URL in the widget's HTML content
            const widgetHTML = element.innerHTML;
            const urlMatch = widgetHTML.match(/"url"\s*:\s*"([^"]+)"/);
            if (urlMatch && urlMatch[1]) {
              event.preventDefault();
              event.stopPropagation();
              event.stopImmediatePropagation();
              window.open(urlMatch[1], "_blank");
              return false;
            }
          }
          
          // Also check if the button has action data stored
          const actionData = (button as any).__actionData;
          if (actionData?.payload?.url) {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
            window.open(actionData.payload.url, "_blank");
            return false;
          }
          
          element = element.parentElement;
        }
      }
    };

    // Also intercept fetch to catch the URL from the request
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      const [url, options] = args;
      
      if (
        typeof url === "string" &&
        url.includes("/knowledge/chatkit") &&
        options?.method === "POST"
      ) {
        // Try to extract URL from the request
        try {
          if (options.body) {
            let bodyText: string;
            if (typeof options.body === "string") {
              bodyText = options.body;
            } else {
              // Clone the body to read it
              const clonedBody = options.body instanceof ReadableStream
                ? options.body
                : new Blob([options.body as BlobPart]).stream();
              bodyText = await new Response(clonedBody).text();
            }
            
            if (bodyText.includes('"type":"ticket.open"') || bodyText.includes('"type": "ticket.open"')) {
              const urlMatch = bodyText.match(/"url"\s*:\s*"([^"]+)"/);
              if (urlMatch && urlMatch[1]) {
                // Open URL in background
                setTimeout(() => window.open(urlMatch[1], "_blank"), 0);
              }
            }
          }
        } catch (e) {
          // Ignore errors
        }
      }
      
      return originalFetch(...args);
    };

    const chatkitElement = document.querySelector("openai-chatkit");
    if (chatkitElement) {
      // Use capture phase to intercept before ChatKit
      chatkitElement.addEventListener("click", handleClick, true);
      
      return () => {
        chatkitElement.removeEventListener("click", handleClick, true);
        window.fetch = originalFetch;
      };
    }
    
    return () => {
      window.fetch = originalFetch;
    };
  }, []);

  return (
    <div className="relative h-full w-full overflow-hidden rounded-[12px] border border-brand-primary/30 bg-white shadow-[0_30px_70px_rgba(29,52,94,0.12)] dark:border-brand-primary/40 dark:bg-[#14243b]">
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
