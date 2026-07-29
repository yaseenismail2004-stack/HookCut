import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ClipSelectionPanel } from "./clip-selection-panel";

describe("ClipSelectionPanel", () => {
  beforeEach(() => vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
    const url = String(input);
    if (url.endsWith("/latest")) return Promise.resolve(new Response("", { status: 404 }));
    if (url.endsWith("clip-selection-jobs")) return Promise.resolve(new Response(JSON.stringify({ id: "job-1", state: "queued", current_stage: "queued", cost_approval_required: false, error_code: null }), { status: 201 }));
    return Promise.resolve(new Response(JSON.stringify([])));
  })));
  afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

  it("creates a real selection request and exposes segment timing without render controls", async () => {
    render(<ClipSelectionPanel video={{ id: "video-1" }} locale="en" />);
    expect(screen.getByText("Timing is based on transcript segments.")).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Clip count"), { target: { value: "4" } });
    fireEvent.click(screen.getByRole("button", { name: "Analyze clips" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/clip-selection-jobs"), expect.objectContaining({ method: "POST", body: expect.stringContaining('"requested_clip_count":4') })));
    expect(screen.queryByRole("button", { name: /render|download/i })).not.toBeInTheDocument();
  });

  it("restores completed selection results after a refresh from the API boundary", async () => {
    vi.stubGlobal("fetch", vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.endsWith("/latest")) return Promise.resolve(new Response(JSON.stringify({ id: "run-1", job_id: "job-1", status: "completed" }), { status: 200 }));
      if (url.endsWith("/api/jobs/job-1")) return Promise.resolve(new Response(JSON.stringify({ state: "completed", current_stage: "completed", cost_approval_required: false, error_code: null }), { status: 200 }));
      if (url.endsWith("/candidates")) return Promise.resolve(new Response(JSON.stringify([{ id: "candidate-1", start_seconds: 0, end_seconds: 20, duration_seconds: 20, timestamp_precision: "segment", transcript_text: "Neutral synthetic evidence.", hook_type: "useful_promise", hook_score: 50, retention_score: 50, viral_potential_score: 50, confidence_score: 50, ideal_platform: "instagram", suggested_title: "Neutral title", suggested_on_screen_hook: "Neutral hook", selection_reason: "Reserve after local selection.", rejection_reason: null, detected_weaknesses: [], selection_status: "reserve" }]), { status: 200 }));
      return Promise.resolve(new Response("", { status: 404 }));
    }));
    render(<ClipSelectionPanel video={{ id: "video-1" }} locale="en" />);
    await waitFor(() => expect(screen.getByText("Selection complete. Video rendering will be added in the next phase.")).toBeInTheDocument());
    expect(screen.getByText(/Neutral title/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Select manually" })).toBeInTheDocument();
  });
});
