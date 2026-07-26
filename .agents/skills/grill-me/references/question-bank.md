# Grill-Me Question Bank

Select only questions relevant to the proposal. Skip questions already answered by the user or project documentation.

## AI applications

- What decision will the model make or assist with, and what must stay under human control?
- Which provider, model class, latency target, quality threshold, and spend ceiling are acceptable?
- What evaluation set and measurable error rate define acceptable quality?
- What happens when confidence is low, output is unsafe, or the provider is unavailable?

## Video-processing applications

- Are inputs user uploads, authorized imports, or both? What consent and ownership evidence is required?
- What are the maximum duration, resolution, codec, and file size? What clip count and duration are expected?
- Is processing local, cloud-based, or hybrid? What turnaround time is acceptable?
- Which languages and dialects are required, including Arabic, Iraqi Arabic, and English? What transcription and subtitle accuracy is acceptable?
- How should hooks, clip boundaries, duplicate prevention, vertical reframing, face tracking, captions, and export quality work?
- What real download formats, retention period, cleanup job, and failure/retry behavior are required?

## Short-form social media tools

- Which destinations matter at launch: Instagram Reels, TikTok, YouTube Shorts, or all three?
- What aspect ratios, duration limits, safe areas, caption styles, and platform-specific metadata are required?
- Are exports download-only or will the product publish to platforms? Who authorizes publishing?
- How will duplicate or near-duplicate clips be prevented across one source and across a library?

## Web applications

- Who are the primary users and what is the exact first successful session from landing page to outcome?
- Which browsers, devices, accessibility standard, performance budget, and authentication method are required?
- What data is stored client-side versus server-side, and which actions require authorization or audit logging?
- What deployment environment, domain ownership, monitoring, and incident response are required?

## Local desktop applications

- Which operating systems, hardware profiles, offline capabilities, and local data locations are required?
- What permissions, file-system access, hardware acceleration, updates, crash recovery, and uninstall behavior are acceptable?
- What must remain on-device and what may be sent to external services?

## Paid SaaS products

- What pricing model, free limits, quota rules, billing provider, taxes, refunds, and cancellation behavior are needed?
- How are usage, credits, overages, invoices, and support disputes measured and audited?
- What tenant isolation, admin roles, service levels, and data-export/deletion rights are required?

## Third-party API integrations

- What exact API capabilities, credentials, scopes, rate limits, costs, and terms of use apply?
- Is access read-only or write-capable? Who grants and revokes consent?
- How will token storage, secret rotation, webhooks, retries, idempotency, quotas, outages, and API-version changes be handled?
- What fallback exists if the integration is denied, unavailable, or too costly?
