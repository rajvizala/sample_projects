import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SecureSignal — AI Threat Detection",
  description: "Real-time personal security monitor that detects AI-driven scams, phishing, and account takeover attempts before they reach you.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
