import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        hcl: {
          // Primary indigo/blue palette
          indigo:        "#4F46E5",
          "indigo-2":    "#4338CA",
          "indigo-3":    "#3730A3",
          blue:          "#2563EB",
          "blue-2":      "#1D4ED8",
          "blue-3":      "#1E40AF",
          sky:           "#0EA5E9",
          "indigo-light":"#EEF2FF",
          "indigo-mid":  "#C7D2FE",
          // Neutrals
          dark:          "#111827",
          "dark-2":      "#1F2937",
          "dark-3":      "#374151",
          white:         "#FFFFFF",
          "gray-50":     "#F9FAFB",
          "gray-100":    "#F3F4F6",
          "gray-200":    "#E5E7EB",
          "gray-300":    "#D1D5DB",
          "gray-400":    "#9CA3AF",
          "gray-500":    "#6B7280",
          "gray-600":    "#4B5563",
          "gray-700":    "#374151",
          "gray-800":    "#1F2937",
          "gray-900":    "#111827",
          // Semantic
          green:         "#059669",
          "green-light": "#DCFCE7",
          "green-border":"#BBF7D0",
          amber:         "#D97706",
          "amber-light": "#FFFBEB",
          "amber-border":"#FDE68A",
          red:           "#DC2626",
          "red-light":   "#FEF2F2",
          "red-border":  "#FECACA",
          purple:        "#7C3AED",
          "purple-light":"#F5F3FF",
          "purple-border":"#DDD6FE",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
      boxShadow: {
        "xs":    "0 1px 2px 0 rgb(0 0 0 / 0.05)",
        "sm":    "0 1px 3px 0 rgb(0 0 0 / 0.08), 0 1px 2px -1px rgb(0 0 0 / 0.06)",
        "md":    "0 4px 12px 0 rgb(0 0 0 / 0.08), 0 2px 4px -1px rgb(0 0 0 / 0.04)",
        "lg":    "0 10px 30px -5px rgb(0 0 0 / 0.1), 0 4px 8px -2px rgb(0 0 0 / 0.06)",
        "xl":    "0 20px 50px -10px rgb(0 0 0 / 0.15)",
        "modal": "0 25px 80px -10px rgb(0 0 0 / 0.3)",
        "indigo":"0 4px 14px 0 rgb(79 70 229 / 0.35)",
        "dark":  "0 4px 14px 0 rgb(17 24 39 / 0.35)",
        "sidebar":"2px 0 8px 0 rgb(0 0 0 / 0.12)",
      },
      animation: {
        "fade-in":   "fadeIn 0.2s ease-out",
        "slide-up":  "slideUp 0.25s cubic-bezier(0.16,1,0.3,1)",
        "scale-in":  "scaleIn 0.2s cubic-bezier(0.16,1,0.3,1)",
        "pulse-dot": "pulseDot 2s ease-in-out infinite",
        "shimmer":   "shimmer 1.5s linear infinite",
      },
      keyframes: {
        fadeIn:   { "0%": { opacity: "0" }, "100%": { opacity: "1" } },
        slideUp:  { "0%": { transform: "translateY(12px)", opacity: "0" }, "100%": { transform: "translateY(0)", opacity: "1" } },
        scaleIn:  { "0%": { transform: "scale(0.96)", opacity: "0" }, "100%": { transform: "scale(1)", opacity: "1" } },
        pulseDot: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0.4" } },
        shimmer:  { "0%": { backgroundPosition: "-200% 0" }, "100%": { backgroundPosition: "200% 0" } },
      },
    },
  },
  plugins: [],
};

export default config;
