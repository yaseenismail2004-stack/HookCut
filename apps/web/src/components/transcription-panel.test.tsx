import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { TranscriptionPanel } from "./transcription-panel";

const video = { id: "video-1", duration_seconds: 21, original_filename: "demo.mp4" };
const capability = (configured: boolean) => new Response(JSON.stringify({ configuration: { transcription_provider_available: configured, openai_api_key_configured: configured, transcription_model_configured: configured, cost_estimation_configured: true } }));
const extracting = { id: "job-1", state: "extracting_audio", current_stage: "extracting_audio", progress_percent: 42, progress_indeterminate: false, estimated_cost_usd: 0.01, cost_approval_required: false, retry_available: false, cancellation_available: true, error_code: null };

describe("TranscriptionPanel", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith("/api/system/capabilities")) return Promise.resolve(capability(true));
    if (url.endsWith("/api/videos/video-1/jobs")) return Promise.resolve(new Response(JSON.stringify([])));
    if (url.endsWith("/transcription-jobs") && init?.method === "POST") return Promise.resolve(new Response(JSON.stringify(extracting), { status: 201 }));
    return Promise.resolve(new Response(JSON.stringify(extracting)));
  })));
  afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
  it("shows provider configuration, language selection, and sends a real job request", async () => { render(<TranscriptionPanel video={video} locale="en" />); expect(await screen.findByText("OpenAI transcription configured")).toBeInTheDocument(); fireEvent.change(screen.getByRole("combobox"), { target: { value: "ar" } }); fireEvent.click(screen.getByRole("button", { name: "Extract audio and transcribe" })); await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/transcription-jobs"), expect.objectContaining({ method: "POST" }))); expect(await screen.findByLabelText("Audio extraction progress")).toHaveValue(42); });
  it("disables work when the provider is not configured", async () => { vi.mocked(fetch).mockImplementation((input) => Promise.resolve(String(input).endsWith("capabilities") ? capability(false) : new Response(JSON.stringify([])))); render(<TranscriptionPanel video={video} locale="en" />); expect(await screen.findByText("OpenAI transcription is not configured on this device.")).toBeInTheDocument(); expect(screen.getByRole("button", { name: "Extract audio and transcribe" })).toBeDisabled(); });
  it("renders Arabic RTL-safe completed transcript text", async () => { vi.mocked(fetch).mockImplementation((input) => { const url = String(input); if (url.endsWith("capabilities")) return Promise.resolve(capability(true)); if (url.endsWith("/jobs")) return Promise.resolve(new Response(JSON.stringify([{ ...extracting, state: "completed", current_stage: "completed", cancellation_available: false }]))); if (url.endsWith("/transcript")) return Promise.resolve(new Response(JSON.stringify({ detected_language: "ar", full_text: "هلا world", duration_seconds: 21, provider: "openai", model: "test", segments: [{ index: 0, start_seconds: 0, end_seconds: 1, text: "هلا world", confidence: null }] }))); return Promise.resolve(new Response(JSON.stringify({ ...extracting, state: "completed" }))); }); render(<TranscriptionPanel video={video} locale="ar" />); expect(await screen.findByText("هلا world")).toBeInTheDocument(); });
});
