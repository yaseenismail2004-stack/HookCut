# Phase 4 compact Gemini clip-analysis contract

## Purpose

Gemini supplies semantic analysis only. HookCut retains candidate identity, transcript evidence, segment timestamps, duration, storage metadata, and final selection locally.

## Local shortlist

The deterministic local pipeline generates and pre-filters all valid segment-timed candidates. Before any provider request it creates a diverse shortlist of at least `max(requested clip count x 4, 12)` candidates when that many genuinely valid candidates exist. The default request cap is 12; a request that needs more than the configured cap fails locally with an actionable error rather than splitting into additional paid requests.

Shortlisting prioritizes valid duration, standalone completeness, useful opening evidence, complete payoff, lower timeline/text overlap, and topic diversity. Local rejections keep their rejection reason. Valid candidates not sent to Gemini remain `reserve` with a `non_analyzed_reserve` reason.

## Provider input and output

The provider receives only a synthetic-safe candidate identifier and a bounded transcript excerpt. It never receives source media, audio, local paths, timestamps, duration, database IDs, source metadata, or final-selection state.

The provider must return `{ "analyses": [...] }` with exactly one compact semantic analysis per submitted candidate ID. Each analysis contains semantic scores, topic/summary, hook and retention evidence, relative drop points, descriptive text, and Estimated Viral Potential. It must not echo transcript text or canonical timing and must not return selected/reserve/rejected decisions, duplicate groups, or rejection reasons.

## Local canonical join and selection

HookCut rejects unknown, duplicate, or missing candidate IDs. It joins valid semantic analysis to the original local candidate evidence, calculates the canonical viral-potential score from the locked weights, validates relative drop points against the local candidate duration, and never creates word timestamps.

Timeline overlap, Arabic-normalized text overlap, duplicate grouping, diversity mode, selection mode, selected/reserve/rejected status, similarity group, selection reason, and rejection reason are calculated locally. Provider output cannot directly select a clip.

## Compact safety limits

Default limits are configurable through the ignored local API environment:

- 12 candidates per request
- 1,200 transcript characters per candidate
- 4 weaknesses per analysis
- 3 predicted relative drop points per analysis
- 300 characters per reason
- 120 characters per suggested title
- 160 characters per on-screen hook
- 18,000 estimated input characters and 24,000 estimated response characters

The implementation does not cut words mid-token. A candidate that exceeds the transcript-evidence limit fails before a provider request, so the user can change the configured limit or narrow the source deliberately.

## Privacy-safe diagnostics

For invalid future responses, diagnostics contain only parsing source, response character count, one-way response hash, JSON shape/type metadata, object field names, array lengths, and Pydantic validation paths. They never store or log transcript content, provider summaries, titles, raw values, credentials, media details, or local paths.

## Remaining verification

This is a local-only contract redesign. It requires one new explicitly authorized, bounded Gemini verification request before Phase 4 can be marked complete.
