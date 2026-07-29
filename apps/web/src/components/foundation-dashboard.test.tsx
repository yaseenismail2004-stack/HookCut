import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FoundationDashboard } from "./foundation-dashboard";

const healthy = () => new Response(JSON.stringify({ status: "ok", service: "hookcut-api", version: "0.1.0" }), { status: 200 });
const video = { id: "v1", original_filename: "demo.mp4", file_size_bytes: 1024 * 1024, container: "mov,mp4,m4a,3gp,3g2,mj2", duration_seconds: 21, width: 320, height: 240, frame_rate: 30, video_codec: "h264", audio_codec: "aac", status: "ready" };
type Handler = ((event: ProgressEvent) => void) | null;

class UploadRequest {
  static instances: UploadRequest[] = [];
  status = 0; responseText = ""; timeout = 0; upload = {} as XMLHttpRequestUpload; onload: Handler = null; onerror: Handler = null; ontimeout: Handler = null; onabort: Handler = null;
  open = vi.fn(); send = vi.fn(() => { (this.upload.onprogress as unknown as Handler)?.({ lengthComputable: true, loaded: 5, total: 10 } as ProgressEvent); }); abort = vi.fn(() => this.onabort?.(new ProgressEvent("abort")));
  constructor() { UploadRequest.instances.push(this); }
  completeBody() { (this.upload.onload as unknown as Handler)?.(new ProgressEvent("load")); }
  respond(status: number, body: unknown) { this.status = status; this.responseText = typeof body === "string" ? body : JSON.stringify(body); this.onload?.(new ProgressEvent("load")); }
  failTimeout() { this.ontimeout?.(new ProgressEvent("timeout")); }
}

function selectVideo() { fireEvent.change(screen.getByLabelText("Choose video"), { target: { files: [new File(["x"], "demo.mp4", { type: "video/mp4" })] } }); }
function startUpload() { fireEvent.click(screen.getByRole("button", { name: "Upload and validate" })); return UploadRequest.instances[0]; }

describe("FoundationDashboard", () => {
  beforeEach(() => { UploadRequest.instances = []; vi.stubGlobal("fetch", vi.fn().mockImplementation(healthy)); vi.stubGlobal("XMLHttpRequest", UploadRequest); });
  afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
  it("shows real connected state and permits retry", async () => { render(<FoundationDashboard />); expect(await screen.findByText("Backend connected")).toBeInTheDocument(); fireEvent.click(screen.getByRole("button", { name: "Retry health check" })); await waitFor(() => expect(vi.mocked(fetch).mock.calls.filter(([url]) => String(url).endsWith("/api/health")).length).toBe(2)); });
  it("rejects an unsupported file before upload", async () => { render(<FoundationDashboard />); fireEvent.change(screen.getByLabelText("Choose video"), { target: { files: [new File(["x"], "unsafe.txt", { type: "text/plain" })] } }); expect(await screen.findByRole("alert")).toHaveTextContent("Unsupported video format."); expect(UploadRequest.instances).toHaveLength(0); });
  it("moves from genuine 100 percent upload to validation and disables cancellation", async () => { render(<FoundationDashboard />); selectVideo(); const request = startUpload(); expect(await screen.findByLabelText("Upload progress")).toHaveValue(50); request.completeBody(); expect(await screen.findByLabelText("Validation in progress")).toBeInTheDocument(); expect(screen.queryByRole("button", { name: "Cancel upload" })).not.toBeInTheDocument(); });
  it("renders real metadata only after the API response succeeds", async () => { render(<FoundationDashboard />); selectVideo(); const request = startUpload(); request.completeBody(); request.respond(201, video); expect(await screen.findByText("Video is ready for the next phase: audio extraction and transcription.")).toBeInTheDocument(); expect(screen.getByText("demo.mp4")).toBeInTheDocument(); });
  it("shows translated ffprobe rejection and request timeout errors", async () => { render(<FoundationDashboard />); selectVideo(); let request = startUpload(); request.completeBody(); request.respond(422, { detail: { code: "corrupt_media" } }); expect(await screen.findByRole("alert")).toHaveTextContent("Media cannot be read."); fireEvent.click(screen.getByRole("button", { name: "Try again" })); request = UploadRequest.instances[1]; request.completeBody(); request.failTimeout(); expect(await screen.findByRole("alert")).toHaveTextContent("took too long"); });
  it("rejects a malformed successful API response instead of stalling", async () => { render(<FoundationDashboard />); selectVideo(); const request = startUpload(); request.completeBody(); request.respond(201, { ok: true }); expect(await screen.findByRole("alert")).toHaveTextContent("invalid upload response"); });
  it("allows cancellation only while the upload body is still transferring", async () => { render(<FoundationDashboard />); selectVideo(); const request = startUpload(); fireEvent.click(screen.getByRole("button", { name: "Cancel upload" })); expect(request.abort).toHaveBeenCalledOnce(); expect(await screen.findByRole("alert")).toHaveTextContent("Upload was cancelled."); });
  it("confirms a real delete action", async () => { render(<FoundationDashboard />); selectVideo(); const request = startUpload(); request.completeBody(); request.respond(201, video); fireEvent.click(await screen.findByRole("button", { name: "Delete video" })); fireEvent.click(screen.getByRole("button", { name: "Delete" })); await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/videos/v1"), { method: "DELETE" })); });
  it("switches Arabic interface to RTL", async () => { render(<FoundationDashboard />); fireEvent.click(screen.getByRole("button", { name: "Arabic" })); expect(screen.getByRole("main")).toHaveAttribute("dir", "rtl"); expect(screen.getByRole("heading", { name: "\u0647\u0648\u0643 \u0643\u062a" })).toBeInTheDocument(); });
});
