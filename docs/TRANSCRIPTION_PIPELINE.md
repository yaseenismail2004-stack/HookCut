# Transcription pipeline

Phase 3 accepts only an existing ready local video. FFmpeg extracts `storage/audio/<random>.flac` with one 16 kHz audio channel. ffprobe validates duration, codec, sample rate, channels, and nonzero size. No local path or stored filename is returned by the API.

The provider interface normalizes language, text, timestamped segments, optional words and confidence, model, usage, and cost. The production provider is OpenAI and is configured only by server-side `OPENAI_API_KEY` and `OPENAI_TRANSCRIPTION_MODEL`. `OPENAI_TRANSCRIPTION_COST_PER_MINUTE_USD` enables an estimate. If no rate is configured, or the estimate exceeds the source-duration-scaled `MAX_AI_COST_PER_VIDEO_HOUR_USD` limit, the job waits for explicit approval.

Endpoints: `POST /api/videos/{video_id}/transcription-jobs`, `GET /api/videos/{video_id}/jobs`, `GET /api/jobs/{job_id}`, `POST /api/jobs/{job_id}/approve-cost`, `POST /api/jobs/{job_id}/cancel`, `POST /api/jobs/{job_id}/retry`, and `GET /api/videos/{video_id}/transcript`.

After successful transcript storage, temporary audio is deleted. Failed incomplete audio is deleted; source uploads are never removed by the worker. OpenAI calls are retried once only for temporary timeout, connection, or rate-limit failures. Provider authentication and model-capability errors are not retried.
