import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FoundationDashboard } from "./foundation-dashboard";

const healthy = () => new Response(JSON.stringify({ status: "ok", service: "hookcut-api", version: "0.1.0" }), { status: 200 });
const video = { id: "v1", original_filename: "demo.mp4", file_size_bytes: 1024 * 1024, container: "mov,mp4,m4a,3gp,3g2,mj2", duration_seconds: 21, width: 320, height: 240, frame_rate: 30, video_codec: "h264", audio_codec: "aac", status: "ready" };

class UploadRequest {
  static instances: UploadRequest[] = [];
  status = 0; responseText = ""; upload: XMLHttpRequestUpload = {} as XMLHttpRequestUpload;
  open = vi.fn(); send = vi.fn(() => { (this.upload.onprogress as unknown as ((event: ProgressEvent) => void) | null)?.({ lengthComputable: true, loaded: 5, total: 10 } as ProgressEvent); }); abort = vi.fn(() => (this.upload.onabort as unknown as ((event: ProgressEvent) => void) | null)?.(new ProgressEvent("abort")));
  constructor() { UploadRequest.instances.push(this); }
  complete(status: number, body: unknown) { this.status = status; this.responseText = JSON.stringify(body); (this.upload.onload as unknown as ((event: ProgressEvent) => void) | null)?.(new ProgressEvent("load")); (this.upload.onloadend as unknown as ((event: ProgressEvent) => void) | null)?.(new ProgressEvent("loadend")); }
}

describe("FoundationDashboard", () => {
  beforeEach(() => { UploadRequest.instances = []; vi.stubGlobal("fetch", vi.fn().mockResolvedValue(healthy())); vi.stubGlobal("XMLHttpRequest", UploadRequest); });
  afterEach(() => { cleanup(); vi.unstubAllGlobals(); });
  it("shows real connected state and permits retry", async () => { render(<FoundationDashboard />); expect(await screen.findByText("Backend connected")).toBeInTheDocument(); fireEvent.click(screen.getByRole("button", { name: "Retry health check" })); await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2)); });
  it("rejects an unsupported file before upload", async () => { render(<FoundationDashboard />); const input = screen.getByLabelText("Choose video"); fireEvent.change(input, { target: { files: [new File(["x"], "unsafe.txt", { type: "text/plain" })] } }); expect(await screen.findByRole("alert")).toHaveTextContent("Unsupported video format."); expect(UploadRequest.instances).toHaveLength(0); });
  it("starts an actual upload request, reports progress, then renders returned metadata", async () => { render(<FoundationDashboard />); fireEvent.change(screen.getByLabelText("Choose video"), { target: { files: [new File(["x"], "demo.mp4", { type: "video/mp4" })] } }); fireEvent.click(screen.getByRole("button", { name: "Upload and validate" })); expect(await screen.findByLabelText("Upload progress")).toHaveValue(50); UploadRequest.instances[0].complete(201, video); expect(await screen.findByText("Video is ready for the next phase: audio extraction and transcription.")).toBeInTheDocument(); expect(screen.getByText("demo.mp4")).toBeInTheDocument(); });
  it("cancels an in-flight upload", async () => { render(<FoundationDashboard />); fireEvent.change(screen.getByLabelText("Choose video"), { target: { files: [new File(["x"], "demo.mp4", { type: "video/mp4" })] } }); fireEvent.click(screen.getByRole("button", { name: "Upload and validate" })); fireEvent.click(screen.getByRole("button", { name: "Cancel upload" })); expect(await screen.findByRole("alert")).toHaveTextContent("Upload was cancelled."); });
  it("translates backend errors and confirms a real delete action", async () => { render(<FoundationDashboard />); fireEvent.change(screen.getByLabelText("Choose video"), { target: { files: [new File(["x"], "demo.mp4", { type: "video/mp4" })] } }); fireEvent.click(screen.getByRole("button", { name: "Upload and validate" })); UploadRequest.instances[0].complete(422, { detail: { code: "video_too_short" } }); expect(await screen.findByRole("alert")).toHaveTextContent("at least 20 seconds"); fireEvent.click(screen.getByRole("button", { name: "Try again" })); UploadRequest.instances[1].complete(201, video); fireEvent.click(await screen.findByRole("button", { name: "Delete video" })); expect(screen.getByRole("dialog")).toBeInTheDocument(); fireEvent.click(screen.getByRole("button", { name: "Delete" })); await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/videos/v1"), { method: "DELETE" })); });
  it("switches Arabic interface to RTL", async () => { render(<FoundationDashboard />); fireEvent.click(screen.getByRole("button", { name: "العربية" })); expect(screen.getByRole("main")).toHaveAttribute("dir", "rtl"); expect(screen.getByRole("heading", { name: "هوك كت" })).toBeInTheDocument(); });
});
