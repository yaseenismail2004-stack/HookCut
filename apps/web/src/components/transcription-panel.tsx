"use client";

import { useCallback, useEffect, useState } from "react";

type Locale = "en" | "ar";
type Provider = "gemini" | "openai";
type Video = { id: string; duration_seconds: number; original_filename: string };
type Capabilities = {
  configuration: {
    gemini_transcription_provider_available: boolean;
    openai_api_key_configured: boolean;
    transcription_model_configured: boolean;
    transcription_provider_available: boolean;
    configured_transcription_providers: Provider[];
  };
};
type Job = { id: string; state: string; current_stage: string; progress_percent: number | null; progress_indeterminate: boolean; estimated_cost_usd: number | null; cost_approval_required: boolean; retry_available: boolean; cancellation_available: boolean; error_code: string | null };
type Transcript = { detected_language: string | null; full_text: string; duration_seconds: number; provider: string; model: string; segments: { index: number; start_seconds: number; end_seconds: number; text: string; confidence: number | null }[] };

const api = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const labels = {
  en: {
    heading: "Transcription", automatic: "Automatic", arabic: "Arabic", english: "English", start: "Extract audio and transcribe", configured: "{provider} transcription configured", notConfigured: "{provider} transcription is not configured on this device.", cost: "Estimated cost", approval: "Approval is required before the provider call.", approve: "Approve estimated cost", cancel: "Cancel job", retry: "Retry job", transcribing: "Transcribing", done: "Transcription complete. Clip selection will be added in the next phase.", provider: "Provider", providerPrivacy: "Gemini sends the extracted audio to Google for this transcription. Do not use it for sensitive media unless you accept that provider's data terms.", chooseProvider: "Transcription provider",
  },
  ar: {
    heading: "التفريغ", automatic: "تلقائي", arabic: "العربية", english: "English", start: "استخرج الصوت وفرّغ", configured: "تم إعداد تفريغ {provider}", notConfigured: "لم يتم إعداد تفريغ {provider} على هذا الجهاز.", cost: "التكلفة المتوقعة", approval: "تلزم موافقة صريحة قبل اتصال مزوّد الخدمة.", approve: "وافق على التكلفة المتوقعة", cancel: "ألغ المهمة", retry: "أعد المحاولة", transcribing: "يتم التفريغ", done: "اكتمل التفريغ. سيكون اختيار المقاطع في المرحلة القادمة.", provider: "المزوّد", providerPrivacy: "يرسل Gemini الصوت المستخرج إلى Google لهذه المهمة. لا تستخدمه للمحتوى الحساس ما لم توافق على شروط بيانات المزوّد.", chooseProvider: "مزوّد التفريغ",
  },
} as const;

function providerLabel(provider: Provider): string {
  return provider === "gemini" ? "Gemini" : "OpenAI";
}

export function TranscriptionPanel({ video, locale }: { video: Video; locale: Locale }) {
  const [capabilities, setCapabilities] = useState<Capabilities | null>(null);
  const [provider, setProvider] = useState<Provider>("gemini");
  const [language, setLanguage] = useState("auto");
  const [job, setJob] = useState<Job | null>(null);
  const [transcript, setTranscript] = useState<Transcript | null>(null);
  const [error, setError] = useState<string | null>(null);
  const t = labels[locale];
  const selectedProvider = providerLabel(provider);

  const getJob = useCallback(async (jobId: string) => {
    const response = await fetch(`${api}/api/jobs/${jobId}`, { cache: "no-store" });
    if (!response.ok) throw new Error("job_unavailable");
    const current = await response.json() as Job;
    setJob(current);
    return current;
  }, []);
  const getTranscript = useCallback(async () => {
    const response = await fetch(`${api}/api/videos/${video.id}/transcript`, { cache: "no-store" });
    if (response.ok) setTranscript(await response.json() as Transcript);
  }, [video.id]);

  useEffect(() => {
    void (async () => {
      try {
        const [capabilityResponse, jobsResponse] = await Promise.all([
          fetch(`${api}/api/system/capabilities`),
          fetch(`${api}/api/videos/${video.id}/jobs`, { cache: "no-store" }),
        ]);
        if (capabilityResponse.ok) setCapabilities(await capabilityResponse.json() as Capabilities);
        if (jobsResponse.ok) {
          const jobs = await jobsResponse.json() as Job[];
          if (jobs[0]) {
            setJob(jobs[0]);
            if (jobs[0].state === "completed") await getTranscript();
          }
        }
      } catch {
        setError("network_error");
      }
    })();
  }, [getTranscript, video.id]);

  useEffect(() => {
    if (!job || ["completed", "failed", "cancelled", "awaiting_cost_approval"].includes(job.state)) return;
    const interval = window.setInterval(() => {
      void getJob(job.id).then((current) => {
        if (current.state === "completed") void getTranscript();
      }).catch(() => setError("network_error"));
    }, 1000);
    return () => window.clearInterval(interval);
  }, [getJob, getTranscript, job]);

  const create = async () => {
    setError(null);
    const response = await fetch(`${api}/api/videos/${video.id}/transcription-jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ language_mode: language, provider, approve_estimated_cost: false }),
    });
    if (!response.ok) {
      const body = await response.json().catch(() => null) as { detail?: { code?: string } } | null;
      setError(body?.detail?.code ?? "transcription_failed");
      return;
    }
    setJob(await response.json() as Job);
  };
  const action = async (route: "approve-cost" | "cancel" | "retry") => {
    if (!job) return;
    const response = await fetch(`${api}/api/jobs/${job.id}/${route}`, { method: "POST" });
    if (response.ok) setJob(await response.json() as Job);
    else setError("transcription_failed");
  };
  const configuration = capabilities?.configuration;
  const configured = provider === "gemini"
    ? configuration?.gemini_transcription_provider_available === true
    : configuration?.configured_transcription_providers?.includes("openai") === true;

  return <section className="mt-8 rounded-2xl border border-[var(--line)] p-5" aria-live="polite">
    <h2 className="text-xl font-bold">{t.heading}</h2>
    <p className="mt-2 text-sm">{(configured ? t.configured : t.notConfigured).replace("{provider}", selectedProvider)}</p>
    <p className="mt-2 text-sm">{t.provider}: {selectedProvider} · {video.duration_seconds.toFixed(1)} s</p>
    {provider === "gemini" && <p className="mt-2 text-sm text-[var(--muted)]">{t.providerPrivacy}</p>}
    {!job && <>
      <label className="mt-4 block text-sm" htmlFor="transcription-provider">{t.chooseProvider}
        <select id="transcription-provider" aria-label={t.chooseProvider} value={provider} onChange={(event) => setProvider(event.target.value as Provider)} className="ms-2 rounded border p-2">
          <option value="gemini">Gemini</option><option value="openai">OpenAI</option>
        </select>
      </label>
      <label className="mt-4 block text-sm" htmlFor="language">{t.automatic}
        <select id="language" value={language} onChange={(event) => setLanguage(event.target.value)} className="ms-2 rounded border p-2">
          <option value="auto">{t.automatic}</option><option value="ar">{t.arabic}</option><option value="en">{t.english}</option>
        </select>
      </label>
      <button type="button" disabled={!configured} onClick={() => void create()} className="mt-4 rounded bg-[var(--accent)] px-4 py-2 text-white disabled:opacity-50">{t.start}</button>
    </>}
    {job && <div className="mt-4">
      <p>{job.current_stage}</p>
      {job.current_stage === "extracting_audio" && <progress aria-label="Audio extraction progress" value={job.progress_percent ?? 0} max="100" className="w-full" />}
      {job.progress_indeterminate && <p><progress aria-label="Transcription in progress" /> {t.transcribing}</p>}
      {job.estimated_cost_usd !== null && <p>{t.cost}: ${job.estimated_cost_usd.toFixed(4)}</p>}
      {job.cost_approval_required && <><p>{t.approval}</p><button type="button" onClick={() => void action("approve-cost")} className="rounded border p-2">{t.approve}</button></>}
      {job.cancellation_available && <button type="button" onClick={() => void action("cancel")} className="m-2 rounded border p-2">{t.cancel}</button>}
      {job.retry_available && <button type="button" onClick={() => void action("retry")} className="m-2 rounded border p-2">{t.retry}</button>}
      {job.error_code && <p role="alert" className="text-rose-500">{job.error_code}</p>}
    </div>}
    {error && <p role="alert" className="mt-3 text-rose-500">{error}</p>}
    {transcript && <article className="mt-5 rounded border p-4">
      <p className="font-semibold">{t.done}</p><p className="mt-3 whitespace-pre-wrap break-words" dir="auto">{transcript.full_text}</p>
      <p className="mt-2 text-sm">{transcript.provider} / {transcript.model}</p>
      <ol className="mt-3 space-y-2">{transcript.segments.map((segment) => <li key={segment.index} dir="auto">{segment.start_seconds.toFixed(2)}–{segment.end_seconds.toFixed(2)} · {segment.text}</li>)}</ol>
    </article>}
  </section>;
}
