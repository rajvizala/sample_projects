import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SkillForge — Adaptive AI Upskilling Coach",
  description: "Master AI/ML through an adaptive learning platform powered by knowledge graphs and a personalized AI coach.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
