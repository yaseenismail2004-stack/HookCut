import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { FoundationDashboard } from "./foundation-dashboard";

const healthyResponse = () => new Response(JSON.stringify({ status: "ok", service: "hookcut-api", version: "0.1.0" }), { status: 200 });

describe("FoundationDashboard", () => {
  beforeEach(() => {
    vi.stubGlobal("fetch", vi.fn());
  });

  afterEach(() => {
    cleanup();
    vi.unstubAllGlobals();
  });

  it("renders the foundation screen and connected state from the real health boundary", async () => {
    vi.mocked(fetch).mockResolvedValue(healthyResponse());
    render(<FoundationDashboard />);
    expect(screen.getByRole("heading", { name: "HookCut" })).toBeInTheDocument();
    expect(await screen.findByText("Connected")).toBeInTheDocument();
  });

  it("shows disconnected when the health request fails", async () => {
    vi.mocked(fetch).mockRejectedValue(new Error("offline"));
    render(<FoundationDashboard />);
    expect(await screen.findByText("Disconnected")).toBeInTheDocument();
  });

  it("retries the health request when requested", async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error("offline")).mockResolvedValueOnce(healthyResponse());
    render(<FoundationDashboard />);
    expect(await screen.findByText("Disconnected")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Retry health check" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(await screen.findByText("Connected")).toBeInTheDocument();
  });

  it("switches to Arabic RTL layout", async () => {
    vi.mocked(fetch).mockResolvedValue(healthyResponse());
    render(<FoundationDashboard />);
    fireEvent.click(screen.getByRole("button", { name: "العربية" }));
    expect(screen.getByRole("main")).toHaveAttribute("dir", "rtl");
    expect(screen.getByRole("heading", { name: "هوك كت" })).toBeInTheDocument();
  });
});
