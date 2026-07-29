"use client";

import { useCallback, useEffect, useState } from "react";

type Locale = "en" | "ar";
type ConnectionState = "checking" | "connected" | "disconnected";

const copy = {
  en: {
    language: "العربية",
    projectName: "HookCut",
    description: "A local-first workspace for turning your own long-form video into real short-form clips.",
    foundation: "Foundation",
    phaseLabel: "Current phase",
    backendLabel: "Backend connection",
    checking: "Checking connection…",
    connected: "Connected",
    disconnected: "Disconnected",
    retry: "Retry health check",
    environmentLabel: "Environment readiness",
    environmentValue: "Validated — safe to scaffold",
    nextNote: "Video upload will be implemented in the next authorized phase.",
  },
  ar: {
    language: "English",
    projectName: "هوك كت",
    description: "مساحة عمل محلية لتحويل فيديوهاتك الطويلة إلى مقاطع قصيرة حقيقية.",
    foundation: "الأساس",
    phaseLabel: "المرحلة الحالية",
    backendLabel: "اتصال الخادم",
    checking: "يتم التحقق من الاتصال…",
    connected: "متصل",
    disconnected: "غير متصل",
    retry: "إعادة فحص الاتصال",
    environmentLabel: "جاهزية البيئة",
    environmentValue: "تم التحقق — جاهزة لبدء الأساس",
    nextNote: "سيُنفّذ رفع الفيديو في المرحلة المصرّح بها التالية.",
  },
} as const;

const apiBaseUrl = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export function FoundationDashboard() {
  const [locale, setLocale] = useState<Locale>("en");
  const [connection, setConnection] = useState<ConnectionState>("checking");
  const text = copy[locale];

  const checkHealth = useCallback(async () => {
    try {
      const response = await fetch(`${apiBaseUrl}/api/health`, { cache: "no-store" });
      const payload: unknown = await response.json();
      const isHealthy =
        response.ok &&
        typeof payload === "object" &&
        payload !== null &&
        "status" in payload &&
        "service" in payload &&
        payload.status === "ok" &&
        payload.service === "hookcut-api";
      setConnection(isHealthy ? "connected" : "disconnected");
    } catch {
      setConnection("disconnected");
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void checkHealth();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [checkHealth]);

  const retryHealth = () => {
    setConnection("checking");
    void checkHealth();
  };

  const connectionLabel = connection === "connected" ? text.connected : connection === "disconnected" ? text.disconnected : text.checking;
  const statusClass = connection === "connected" ? "bg-emerald-500" : connection === "disconnected" ? "bg-rose-500" : "bg-amber-400";

  return (
    <main dir={locale === "ar" ? "rtl" : "ltr"} lang={locale} className="min-h-screen px-5 py-6 sm:px-8 lg:px-12">
      <div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-5xl flex-col rounded-3xl border border-[var(--line)] bg-[var(--panel)] p-6 shadow-2xl shadow-black/5 sm:p-10">
        <header className="flex items-center justify-between gap-4">
          <p className="text-sm font-semibold tracking-[0.2em] text-[var(--accent)]">HOOKCUT / 01</p>
          <button
            type="button"
            onClick={() => setLocale((current) => (current === "en" ? "ar" : "en"))}
            className="rounded-full border border-[var(--line)] px-4 py-2 text-sm font-semibold transition hover:border-[var(--accent)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
          >
            {text.language}
          </button>
        </header>

        <section className="flex flex-1 flex-col justify-center py-16 sm:py-24">
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.18em] text-[var(--muted)]">{text.phaseLabel}</p>
          <h1 className="max-w-3xl text-5xl font-black tracking-tight sm:text-7xl">{text.projectName}</h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-[var(--muted)] sm:text-xl">{text.description}</p>
          <div className="mt-10 grid max-w-3xl gap-4 sm:grid-cols-3">
            <StatusCard label={text.phaseLabel} value={text.foundation} />
            <StatusCard label={text.environmentLabel} value={text.environmentValue} />
            <div className="rounded-2xl border border-[var(--line)] p-5">
              <p className="text-sm text-[var(--muted)]">{text.backendLabel}</p>
              <div className="mt-3 flex items-center gap-2 font-semibold" aria-live="polite">
                <span className={`h-2.5 w-2.5 rounded-full ${statusClass}`} aria-hidden="true" />
                <span>{connectionLabel}</span>
              </div>
              <button
                type="button"
                onClick={retryHealth}
                className="mt-4 text-sm font-semibold text-[var(--accent)] underline-offset-4 hover:underline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--accent)]"
              >
                {text.retry}
              </button>
            </div>
          </div>
        </section>

        <footer className="border-t border-[var(--line)] pt-6 text-sm leading-6 text-[var(--muted)]">{text.nextNote}</footer>
      </div>
    </main>
  );
}

function StatusCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-[var(--line)] p-5">
      <p className="text-sm text-[var(--muted)]">{label}</p>
      <p className="mt-3 font-semibold leading-6">{value}</p>
    </div>
  );
}
