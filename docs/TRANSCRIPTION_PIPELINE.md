# Transcription pipeline

Phase 3 accepts only an existing ready local video. FFmpeg extracts `storage/audio/<random>.flac` with one 16 kHz audio channel. ffprobe validates duration, codec, sample rate, channels, and nonzero size. No local path or stored filename is returned by the API.

The provider interface normalizes language, text, timestamped segments, optional words and confidence, model, usage, and cost. Gemini is the primary provider and is configured only by server-side `GEMINI_API_KEY`; it defaults to `gemini-3.6-flash`. Gemini uploads only the temporary FLAC audio, uses the current Gemini Interactions API for structured JSON transcription, rejects malformed or non-monotonic timestamps, and deletes the remote file after the request. If remote deletion cannot be confirmed, the job fails without storing a transcript. OpenAI remains an optional explicit provider through `OPENAI_API_KEY` and `OPENAI_TRANSCRIPTION_MODEL`; there is no automatic provider fallback.

`GEMINI_TRANSCRIPTION_COST_PER_MINUTE_USD` or `OPENAI_TRANSCRIPTION_COST_PER_MINUTE_USD` enables an estimate for its matching provider. If no rate is configured, or the estimate exceeds the source-duration-scaled `MAX_AI_COST_PER_VIDEO_HOUR_USD` limit, the job waits for explicit approval. Gemini Free Tier availability and data handling are controlled by the Google project; do not use it for sensitive media unless the user accepts Google's applicable terms.

Endpoints: `POST /api/videos/{video_id}/transcription-jobs`, `GET /api/videos/{video_id}/jobs`, `GET /api/jobs/{job_id}`, `POST /api/jobs/{job_id}/approve-cost`, `POST /api/jobs/{job_id}/cancel`, `POST /api/jobs/{job_id}/retry`, and `GET /api/videos/{video_id}/transcript`.

After successful transcript storage, temporary audio is deleted. Failed incomplete audio is deleted; source uploads are never removed by the worker. OpenAI calls are retried once only for temporary timeout, connection, or rate-limit failures. Provider authentication and model-capability errors are not retried.
