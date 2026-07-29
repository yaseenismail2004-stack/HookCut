import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HookCut",
  description: "Local-first AI UGC clipper foundation",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en" className="h-full">
      <body className="min-h-full">{children}</body>
    </html>
  );
}
