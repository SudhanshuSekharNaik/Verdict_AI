import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aadalat AI",
  description: "Evidence-grounded multi-agent courtroom simulation and legal intelligence platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-slate-50">{children}</body>
    </html>
  );
}
