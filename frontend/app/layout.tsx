import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "VerdictAI — Nyay Manch",
  description: "VerdictAI (Nyay Manch) — Autonomous turn-based AI courtroom simulation and legal reasoning platform grounded in Bharatiya Nyaya Sanhita, Bharatiya Sakshya Adhiniyam & BNSS 2023.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50">{children}</body>
    </html>
  );
}
