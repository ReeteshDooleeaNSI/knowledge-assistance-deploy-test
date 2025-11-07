import clsx from "clsx";
import { Moon, Sun } from "lucide-react";

import type { ColorScheme } from "../hooks/useColorScheme";

type ThemeToggleProps = {
  value: ColorScheme;
  onChange: (scheme: ColorScheme) => void;
};

const buttonBase =
  "inline-flex h-9 w-9 items-center justify-center rounded-full text-[0.7rem] transition-colors duration-200";

export function ThemeToggle({ value, onChange }: ThemeToggleProps) {
  return (
    <div className="inline-flex items-center gap-1 rounded-full border border-brand-primary/30 bg-white/80 p-1 shadow-sm backdrop-blur-sm dark:border-brand-primary/40 dark:bg-[#14243b]/70">
      <button
        type="button"
        onClick={() => onChange("light")}
        className={clsx(
          buttonBase,
          value === "light"
            ? "bg-brand-primary text-brand-text shadow-sm dark:bg-brand-primary/90 dark:text-[#0d1b2a]"
            : "text-brand-link/60 hover:text-brand-link dark:text-brand-primary/70 dark:hover:text-brand-primary",
        )}
        aria-label="Use light theme"
        aria-pressed={value === "light"}
      >
        <Sun className="h-4 w-4" aria-hidden />
      </button>
      <button
        type="button"
        onClick={() => onChange("dark")}
        className={clsx(
          buttonBase,
          value === "dark"
            ? "bg-brand-link text-white shadow-sm"
            : "text-brand-link/60 hover:text-brand-link dark:text-brand-primary/70 dark:hover:text-brand-primary",
        )}
        aria-label="Use dark theme"
        aria-pressed={value === "dark"}
      >
        <Moon className="h-4 w-4" aria-hidden />
      </button>
    </div>
  );
}

