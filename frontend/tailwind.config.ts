import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        plaintiff: { DEFAULT: "#ef4444", light: "#fca5a5", dark: "#b91c1c", glow: "rgba(239,68,68,0.15)" },
        defence: { DEFAULT: "#3b82f6", light: "#93c5fd", dark: "#1d4ed8", glow: "rgba(59,130,246,0.15)" },
        judge: { DEFAULT: "#f59e0b", light: "#fcd34d", dark: "#b45309", glow: "rgba(245,158,11,0.15)" },
        court: { DEFAULT: "#1e293b", light: "#334155", dark: "#0f172a" },
        surface: { DEFAULT: "#1e293b", raised: "#273548", overlay: "#334155" },
      },
    },
  },
  plugins: [],
};

export default config;
