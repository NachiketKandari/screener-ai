import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Strattest — Indian Stock Screener",
  description: "Screen NSE stocks with filters or natural language",
  icons: { icon: "/favicon.svg" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-background text-foreground antialiased">
        {children}
      </body>
    </html>
  );
}
