# Processing job state machine

`transcription` jobs are durable SQLite records. Valid states are `queued`, `validating_source`, `extracting_audio`, `audio_ready`, `estimating_cost`, `awaiting_cost_approval`, `transcribing`, `saving_transcript`, `completed`, `failed`, and `cancelled`.

The local worker claims one queued job at a time. It validates the ready source, extracts normalized mono 16 kHz FLAC, estimates cost, waits for explicit approval when needed, calls the configured provider, stores the transcript, and marks the job complete only after storage succeeds. A restart converts an in-flight state to `failed` with `worker_interrupted`, which can be retried once. Invalid transitions are rejected.

Cancellation is immediate for queued or approval-waiting jobs. During extraction the worker observes cancellation; during provider work it discards a late result and records `cancelled`.
