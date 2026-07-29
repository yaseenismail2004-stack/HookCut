"use client";

import { ChangeEvent, DragEvent, useCallback, useEffect, useRef, useState } from "react";

type Locale = "en" | "ar";
type UploadState = "idle" | "uploading" | "validating" | "success" | "rejected";
type Video = { id: string; original_filename: string; file_size_bytes: number; container: string; duration_seconds: number; width: number; height: number; frame_rate: number; video_codec: string; audio_codec: string; status: string };

const api = (process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000").replace(/\/$/, "");
const allowed = [".mp4", ".mov", ".mkv", ".webm"];
const copy = {
  en: { title: "HookCut", language: "العربية", choose: "Choose video", upload: "Upload and validate", cancel: "Cancel upload", retry: "Try again", reset: "Reset", ready: "Ready", validating: "Validating media…", drop: "Drop a local video here or choose a file", note: "MP4, MOV, MKV, or WebM · up to 4 GB", next: "Video is ready for the next phase: audio extraction and transcription.", delete: "Delete video", confirm: "Permanently delete this video?", yes: "Delete", no: "Cancel", connected: "Backend connected", disconnected: "Backend disconnected", retryHealth: "Retry health check" },
  ar: { title: "هوك كت", language: "English", choose: "اختر فيديو", upload: "ارفع وتحقق", cancel: "إلغاء الرفع", retry: "حاول مجدداً", reset: "إعادة تعيين", ready: "جاهز", validating: "يتم التحقق من الوسائط…", drop: "اسحب فيديو محلياً هنا أو اختر ملفاً", note: "MP4 أو MOV أو MKV أو WebM · حتى 4GB", next: "الفيديو جاهز للمرحلة القادمة: استخراج الصوت والتفريغ.", delete: "حذف الفيديو", confirm: "هل تريد حذف هذا الفيديو نهائياً؟", yes: "حذف", no: "إلغاء", connected: "الخادم متصل", disconnected: "الخادم غير متصل", retryHealth: "أعد فحص الخادم" },
} as const;
const errors: Record<string, Record<Locale, string>> = {
  unsupported_format: { en: "Unsupported video format.", ar: "صيغة الفيديو غير مدعومة." },
  file_too_large: { en: "File exceeds the upload limit.", ar: "حجم الملف يتجاوز حد الرفع." },
  video_too_short: { en: "Video must be at least 20 seconds.", ar: "يجب أن تكون مدة الفيديو 20 ثانية على الأقل." },
  video_too_long: { en: "Video exceeds the maximum duration.", ar: "مدة الفيديو تتجاوز الحد الأقصى." },
  resolution_too_high: { en: "Video resolution exceeds 4K.", ar: "دقة الفيديو تتجاوز 4K." },
  missing_video_stream: { en: "Video stream is missing.", ar: "مسار الفيديو مفقود." },
  missing_audio_stream: { en: "Usable audio stream is missing.", ar: "مسار صوت صالح مفقود." },
  corrupt_media: { en: "Media cannot be read.", ar: "لا يمكن قراءة الوسائط." },
  upload_cancelled: { en: "Upload was cancelled.", ar: "تم إلغاء الرفع." },
  storage_error: { en: "Local storage failed.", ar: "فشل التخزين المحلي." },
  validation_timeout: { en: "Validation timed out.", ar: "انتهت مهلة التحقق." },
};

export function FoundationDashboard() {
  const [locale, setLocale] = useState<Locale>("en");
  const [connected, setConnected] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<UploadState>("idle");
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [video, setVideo] = useState<Video | null>(null);
  const [confirm, setConfirm] = useState(false);
  const xhr = useRef<XMLHttpRequest | null>(null);
  const t = copy[locale];

  const health = useCallback(async () => {
    try {
      const response = await fetch(`${api}/api/health`, { cache: "no-store" });
      const payload = await response.json();
      setConnected(response.ok && payload.status === "ok" && payload.service === "hookcut-api");
    } catch { setConnected(false); }
  }, []);
  useEffect(() => {
    const timer = window.setTimeout(() => { void health(); }, 0);
    return () => window.clearTimeout(timer);
  }, [health]);

  const select = (candidate: File | undefined) => {
    if (!candidate) return;
    const extension = `.${candidate.name.split(".").pop()?.toLowerCase()}`;
    setVideo(null); setError(null); setProgress(0);
    if (!allowed.includes(extension) || candidate.size > 4 * 1024 * 1024 * 1024) {
      setFile(null); setState("rejected"); setError(!allowed.includes(extension) ? "unsupported_format" : "file_too_large"); return;
    }
    setFile(candidate); setState("idle");
  };
  const upload = () => {
    if (!file) return;
    const request = new XMLHttpRequest(); xhr.current = request;
    setState("uploading"); setProgress(0); setError(null);
    request.open("POST", `${api}/api/videos/upload`);
    request.upload.onprogress = (event) => { if (event.lengthComputable) setProgress(Math.round((event.loaded / event.total) * 100)); };
    request.upload.onload = () => { if (request.status === 201) setState("validating"); };
    request.upload.onabort = () => { setState("rejected"); setError("upload_cancelled"); };
    request.upload.onloadend = () => {
      if (request.status === 0) return;
      if (request.status >= 200 && request.status < 300) { setVideo(JSON.parse(request.responseText) as Video); setState("success"); return; }
      try { setError((JSON.parse(request.responseText) as { detail: { code: string } }).detail.code); } catch { setError("storage_error"); }
      setState("rejected");
    };
    const data = new FormData(); data.append("file", file); request.send(data);
  };
  const reset = () => { xhr.current?.abort(); xhr.current = null; setFile(null); setVideo(null); setError(null); setProgress(0); setState("idle"); };
  const deleteVideo = async () => {
    if (!video) return;
    const response = await fetch(`${api}/api/videos/${video.id}`, { method: "DELETE" });
    if (response.ok) reset(); else setError("storage_error");
    setConfirm(false);
  };
  const message = error ? (errors[error]?.[locale] ?? errors.storage_error[locale]) : null;

  return <main dir={locale === "ar" ? "rtl" : "ltr"} lang={locale} className="min-h-screen p-5 sm:p-10">
    <section className="mx-auto max-w-3xl rounded-3xl border border-[var(--line)] bg-[var(--panel)] p-6 shadow-xl">
      <header className="flex items-center justify-between gap-4"><div><p className="text-sm text-[var(--accent)]">HOOKCUT / PHASE 2</p><h1 className="text-4xl font-bold">{t.title}</h1></div><button type="button" onClick={() => setLocale(locale === "en" ? "ar" : "en")} className="rounded border p-2">{t.language}</button></header>
      <p className="mt-4 text-sm" aria-live="polite">{connected ? t.connected : t.disconnected} <button type="button" onClick={() => void health()} aria-label={t.retryHealth} className="underline">↻</button></p>
      {!video && <div className="mt-8"><label onDrop={(event: DragEvent) => { event.preventDefault(); select(event.dataTransfer.files[0]); }} onDragOver={(event) => event.preventDefault()} className="block rounded-2xl border-2 border-dashed border-[var(--line)] p-10 text-center"><input aria-label={t.choose} type="file" accept="video/mp4,video/quicktime,video/x-matroska,video/webm" className="sr-only" onChange={(event: ChangeEvent<HTMLInputElement>) => select(event.target.files?.[0])}/><span>{file ? file.name : t.drop}</span><small className="mt-2 block text-[var(--muted)]">{t.note}</small></label>
        {file && <p className="mt-3 break-all text-sm">{file.name} · {(file.size / 1024 / 1024).toFixed(1)} MB</p>}
        {state === "uploading" && <><progress className="mt-4 w-full" value={progress} max="100" aria-label="Upload progress" />{progress}%</>}{state === "validating" && <p className="mt-4">{t.validating}</p>}{message && <p role="alert" className="mt-4 text-rose-500">{message}</p>}
        <div className="mt-5 flex flex-wrap gap-3">{file && state !== "uploading" && state !== "validating" && <button type="button" onClick={upload} className="rounded bg-[var(--accent)] px-4 py-2 text-white">{state === "rejected" ? t.retry : t.upload}</button>}{state === "uploading" && <button type="button" onClick={() => xhr.current?.abort()} className="rounded border px-4 py-2">{t.cancel}</button>}{(file || state === "rejected") && state !== "uploading" && <button type="button" onClick={reset} className="rounded border px-4 py-2">{t.reset}</button>}</div></div>}
      {video && <section className="mt-8 rounded-2xl border border-emerald-500/40 p-5"><h2 className="text-xl font-bold">{t.ready}</h2><dl className="mt-4 grid grid-cols-2 gap-3 text-sm"><div><dt>File</dt><dd className="break-all">{video.original_filename}</dd></div><div><dt>Size</dt><dd>{(video.file_size_bytes / 1024 / 1024).toFixed(1)} MB</dd></div><div><dt>Duration</dt><dd>{video.duration_seconds.toFixed(2)} s</dd></div><div><dt>Video</dt><dd>{video.width}×{video.height} · {video.frame_rate} fps</dd></div><div><dt>Container</dt><dd>{video.container}</dd></div><div><dt>Codecs</dt><dd>{video.video_codec} / {video.audio_codec}</dd></div></dl><p className="mt-5">{t.next}</p><button type="button" onClick={() => setConfirm(true)} className="mt-5 rounded border border-rose-500 px-4 py-2 text-rose-500">{t.delete}</button></section>}
      {confirm && <div role="dialog" aria-modal="true" className="mt-5 rounded border p-4"><p>{t.confirm}</p><button type="button" onClick={() => void deleteVideo()} className="mt-3 rounded bg-rose-600 px-3 py-2 text-white">{t.yes}</button><button type="button" onClick={() => setConfirm(false)} className="m-3 underline">{t.no}</button></div>}
    </section>
  </main>;
}
