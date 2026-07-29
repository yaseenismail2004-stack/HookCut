"use client";

import { useCallback, useEffect, useState } from "react";

type Locale = "en" | "ar";
type Video = { id: string };
type Job = {
  state: string;
  current_stage: string;
  cost_approval_required: boolean;
  error_code: string | null;
};
type Run = { id: string; job_id: string; status: string };
type Candidate = {
  id: string;
  start_seconds: number;
  end_seconds: number;
  duration_seconds: number;
  timestamp_precision: string;
  transcript_text: string;
  hook_type: string;
  hook_score: number;
  retention_score: number;
  viral_potential_score: number;
  confidence_score: number;
  ideal_platform: string;
  suggested_title: string;
  suggested_on_screen_hook: string;
  selection_reason: string;
  rejection_reason: string | null;
  detected_weaknesses: string[];
  selection_status: string;
};

const api = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");

export function ClipSelectionPanel({ video, locale }: { video: Video; locale: Locale }) {
  const [requested, setRequested] = useState(3);
  const [platform, setPlatform] = useState("instagram");
  const [duration, setDuration] = useState("auto");
  const [mode, setMode] = useState("balanced");
  const [diversity, setDiversity] = useState("strict");
  const [run, setRun] = useState<Run | null>(null);
  const [job, setJob] = useState<Job | null>(null);
  const [items, setItems] = useState<Candidate[]>([]);
  const [error, setError] = useState<string | null>(null);

  const copy = locale === "ar"
    ? {
        title: "اختيار المقاطع",
        platform: "المنصة",
        count: "عدد المقاطع",
        duration: "المدة",
        mode: "وضع الاختيار",
        diversity: "التنوع",
        analyze: "حلّل المقاطع",
        timing: "التوقيت مبني على مقاطع التفريغ الصوتي.",
        done: "اكتمل اختيار المقاطع. ستتم إضافة معالجة الفيديو والتصدير في المرحلة القادمة.",
        approve: "أوافق على التكلفة",
        selected: "المختارة",
        reserve: "الاحتياطية",
        rejected: "المرفوضة",
        select: "اختيار يدوياً",
        reserveAction: "نقل إلى الاحتياط",
        stage: "حالة المعالجة",
        restoreError: "تعذّر استعادة حالة الاختيار.",
        startError: "تعذّر بدء اختيار المقاطع.",
      }
    : {
        title: "Clip selection",
        platform: "Platform",
        count: "Clip count",
        duration: "Duration",
        mode: "Selection mode",
        diversity: "Diversity",
        analyze: "Analyze clips",
        timing: "Timing is based on transcript segments.",
        done: "Selection complete. Video rendering will be added in the next phase.",
        approve: "Approve cost",
        selected: "Selected",
        reserve: "Reserve",
        rejected: "Rejected",
        select: "Select manually",
        reserveAction: "Move to reserve",
        stage: "Processing status",
        restoreError: "Could not restore selection state.",
        startError: "Could not start clip selection.",
      };

  const refresh = useCallback(async () => {
    try {
      const latest = await fetch(`${api}/api/videos/${video.id}/clip-selection-runs/latest`);
      if (!latest.ok) return;
      const current = await latest.json() as Run;
      setRun(current);
      const [jobResponse, candidatesResponse] = await Promise.all([
        fetch(`${api}/api/jobs/${current.job_id}`),
        fetch(`${api}/api/clip-selection-runs/${current.id}/candidates`),
      ]);
      if (jobResponse.ok) setJob(await jobResponse.json() as Job);
      if (candidatesResponse.ok) setItems(await candidatesResponse.json() as Candidate[]);
    } catch {
      setError(copy.restoreError);
    }
  }, [copy.restoreError, video.id]);

  useEffect(() => {
    const initial = window.setTimeout(() => void refresh(), 0);
    const timer = window.setInterval(() => void refresh(), 2000);
    return () => {
      window.clearTimeout(initial);
      window.clearInterval(timer);
    };
  }, [refresh]);

  const start = async () => {
    setError(null);
    const response = await fetch(`${api}/api/videos/${video.id}/clip-selection-jobs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        requested_clip_count: requested,
        platform,
        duration_mode: duration,
        selection_mode: mode,
        diversity_mode: diversity,
        approve_estimated_cost: false,
      }),
    });
    if (!response.ok) {
      setError(copy.startError);
      return;
    }
    await refresh();
  };

  const approve = async () => {
    if (!run) return;
    await fetch(`${api}/api/clip-selection-runs/${run.id}/approve-cost`, { method: "POST" });
    await refresh();
  };

  const adjust = async (id: string, selectionStatus: string) => {
    await fetch(`${api}/api/clip-candidates/${id}/selection`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ selection_status: selectionStatus }),
    });
    await refresh();
  };

  const labels: Record<string, string> = {
    selected: copy.selected,
    reserve: copy.reserve,
    rejected: copy.rejected,
  };

  return (
    <section className="mt-8 rounded-2xl border p-5" aria-labelledby="selection-title">
      <h2 id="selection-title" className="text-xl font-bold">{copy.title}</h2>
      <p className="text-sm text-[var(--muted)]">{copy.timing}</p>

      {!run && (
        <div className="mt-4 grid gap-3 sm:grid-cols-2">
          <label>{copy.platform}<select value={platform} onChange={(event) => setPlatform(event.target.value)}><option value="instagram">Instagram Reels</option><option value="tiktok">TikTok</option><option value="youtube">YouTube Shorts</option></select></label>
          <label>{copy.count}<input aria-label={copy.count} type="number" min="1" max="10" value={requested} onChange={(event) => setRequested(Math.max(1, Math.min(10, Number(event.target.value))))} /></label>
          <label>{copy.duration}<select value={duration} onChange={(event) => setDuration(event.target.value)}><option value="auto">Auto</option><option value="15_to_30">15–30</option><option value="30_to_60">30–60</option><option value="45_to_90">45–90</option></select></label>
          <label>{copy.mode}<select value={mode} onChange={(event) => setMode(event.target.value)}><option value="highest_potential">Highest Potential</option><option value="balanced">Balanced</option><option value="exact_count">Exact Count</option></select></label>
          <label>{copy.diversity}<select value={diversity} onChange={(event) => setDiversity(event.target.value)}><option value="strict">Strict</option><option value="balanced">Balanced</option><option value="similar_allowed">Similar moments allowed</option></select></label>
        </div>
      )}

      {!run && <button type="button" onClick={() => void start()} className="mt-4 rounded bg-[var(--accent)] px-4 py-2 text-white">{copy.analyze}</button>}
      {job && (
        <div role="status" aria-live="polite" className="mt-4">
          {!['completed', 'failed', 'cancelled', 'awaiting_cost_approval'].includes(job.state) && <progress aria-label={copy.stage} />}
          <p>{job.current_stage}</p>
          {job.cost_approval_required && <button type="button" onClick={() => void approve()}>{copy.approve}</button>}
          {job.error_code && <p role="alert">{job.error_code}</p>}
        </div>
      )}
      {error && <p role="alert">{error}</p>}

      {run?.status === "completed" && (
        <>
          <p className="mt-4">{copy.done}</p>
          {['selected', 'reserve', 'rejected'].map((group) => (
            <section key={group} className="mt-4" aria-label={labels[group]}>
              <h3 className="font-semibold">{labels[group]}</h3>
              {items.filter((item) => item.selection_status === group || (group === "selected" && item.selection_status === "manually_selected")).map((item) => (
                <article key={item.id} className="mt-2 rounded border p-3">
                  <p>{item.start_seconds.toFixed(2)}–{item.end_seconds.toFixed(2)} · {item.duration_seconds.toFixed(1)}s · {item.timestamp_precision}</p>
                  <p dir="auto" className="break-words">{item.transcript_text}</p>
                  <p>{item.hook_type}: {item.hook_score} · {locale === "ar" ? "إمكانية الانتشار المقدّرة" : "Estimated Viral Potential"}: {item.viral_potential_score} · {item.confidence_score}</p>
                  <p>{item.suggested_title} · {item.suggested_on_screen_hook}</p>
                  <p>{item.selection_reason || item.rejection_reason}</p>
                  {group === "reserve" && <button type="button" onClick={() => void adjust(item.id, "manually_selected")}>{copy.select}</button>}
                  {group === "selected" && <button type="button" onClick={() => void adjust(item.id, "reserve")}>{copy.reserveAction}</button>}
                </article>
              ))}
            </section>
          ))}
        </>
      )}
    </section>
  );
}
