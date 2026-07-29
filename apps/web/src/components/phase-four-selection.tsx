"use client";

import { useEffect, useState } from "react";
import { ClipSelectionPanel } from "./clip-selection-panel";

const api = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export function PhaseFourSelection() {
  const [video, setVideo] = useState<{ id: string } | null>(null);
  const [locale, setLocale] = useState<"en" | "ar">("en");
  useEffect(() => { void (async () => { try { const response = await fetch(`${api}/api/videos`, { cache: "no-store" }); const items: unknown = await response.json(); if (Array.isArray(items)) { const ready = items.find((item): item is { id: string; status: string } => Boolean(item) && typeof item === "object" && "id" in item && "status" in item && (item as { status: string }).status === "ready"); if (ready) setVideo(ready); } } catch { /* The main dashboard remains usable when the API is offline. */ } })(); }, []);
  if (!video) return null;
  return <div dir={locale === "ar" ? "rtl" : "ltr"} lang={locale} className="mx-auto max-w-3xl px-5 pb-10 sm:px-10"><button type="button" className="rounded border px-2 py-1" onClick={() => setLocale(locale === "en" ? "ar" : "en")}>{locale === "en" ? "العربية" : "English"}</button><ClipSelectionPanel video={video} locale={locale} /></div>;
}
