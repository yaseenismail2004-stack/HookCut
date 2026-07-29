# Live transcription verification

## Status

Verified on 2026-07-29 after resolving the request-format and SDK compatibility issues. The final human-approved Gemini request completed, and the application persisted and retrieved its normalized transcript without documenting source speech content.

## Private-data-safe test record

- Test date: 2026-07-29.
- Source: the human authorized the latest ready local Arabic or Iraqi Arabic source. No filename, path, transcript text, or speech content is recorded here.
- Source duration: 46.5 seconds.
- Provider: Gemini.
- Model: `gemini-3.6-flash`.
- Local extraction result: nonzero mono 16 kHz FLAC audio artifact with a validated 46.5-second duration.
- Provider request result: the final explicitly approved request completed successfully after the local cost-approval gate.
- Transcript segments: 14 persisted and retrieved through the real API after an API restart.
- Word timestamps: unavailable because the successful Gemini response did not provide them; the application did not invent them.
- Temporary-audio policy: the audio artifact record is marked deleted, has a deletion timestamp, and its physical local audio file is absent. No source media was removed.

## Capability and quality observations

The final response detected Arabic and returned timestamped segments. No transcript text is included here, so a formal accuracy percentage, Iraqi Arabic quality judgment, punctuation review, hallucination review, RTL visual inspection, and long-line wrapping are not claimed as live-verified. No formal accuracy percentage is claimed.

## Provider limitation

The legacy request path returned 404 and early Interactions attempts returned 400. The final verified request uses the documented `response_format` wrapper and `google-genai` 2.14.0, which meets the documented Interactions SDK minimum. Safe diagnostics retain only request stage, exception type, and numeric status code, never a secret, file path, audio content, or raw provider response. Future paid or cloud processing remains explicitly user-approved.
