"""add durable transcription pipeline"""

from alembic import op
import sqlalchemy as sa

revision = "20260729_02"
down_revision = "20260729_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("processing_jobs",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("video_assets.id"), nullable=False),
        sa.Column("job_type", sa.String(32), nullable=False), sa.Column("state", sa.String(32), nullable=False), sa.Column("progress_percent", sa.Float()), sa.Column("current_stage", sa.String(64), nullable=False),
        sa.Column("language_mode", sa.String(8), nullable=False), sa.Column("transcription_provider", sa.String(32), nullable=False), sa.Column("transcription_model", sa.String(128)), sa.Column("estimated_cost_usd", sa.Float()), sa.Column("actual_cost_usd", sa.Float()),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("max_retries", sa.Integer(), nullable=False, server_default="1"), sa.Column("cancellation_requested", sa.Boolean(), nullable=False, server_default=sa.false()), sa.Column("cost_approved", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("error_code", sa.String(64)), sa.Column("error_message", sa.String(512)), sa.Column("started_at", sa.DateTime(timezone=True)), sa.Column("completed_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_processing_jobs_video_id", "processing_jobs", ["video_id"])
    op.create_index("ix_processing_jobs_state", "processing_jobs", ["state"])
    op.create_table("audio_artifacts",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("video_assets.id"), nullable=False), sa.Column("job_id", sa.String(36), sa.ForeignKey("processing_jobs.id"), nullable=False), sa.Column("stored_filename", sa.String(255), nullable=False, unique=True), sa.Column("duration_seconds", sa.Float()), sa.Column("codec", sa.String(64)), sa.Column("sample_rate", sa.Integer()), sa.Column("channels", sa.Integer()), sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"), sa.Column("status", sa.String(16), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("deleted_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_audio_artifacts_video_id", "audio_artifacts", ["video_id"])
    op.create_index("ix_audio_artifacts_job_id", "audio_artifacts", ["job_id"])
    op.create_table("transcripts",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("video_assets.id"), nullable=False), sa.Column("job_id", sa.String(36), sa.ForeignKey("processing_jobs.id"), nullable=False, unique=True), sa.Column("provider", sa.String(32), nullable=False), sa.Column("model", sa.String(128), nullable=False), sa.Column("detected_language", sa.String(32)), sa.Column("language_confidence", sa.Float()), sa.Column("full_text", sa.Text(), nullable=False), sa.Column("duration_seconds", sa.Float(), nullable=False), sa.Column("status", sa.String(16), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_transcripts_video_id", "transcripts", ["video_id"])
    op.create_table("transcript_segments", sa.Column("id", sa.String(36), primary_key=True), sa.Column("transcript_id", sa.String(36), sa.ForeignKey("transcripts.id"), nullable=False), sa.Column("segment_index", sa.Integer(), nullable=False), sa.Column("start_seconds", sa.Float(), nullable=False), sa.Column("end_seconds", sa.Float(), nullable=False), sa.Column("text", sa.Text(), nullable=False), sa.Column("confidence", sa.Float()))
    op.create_index("ix_transcript_segments_transcript_id", "transcript_segments", ["transcript_id"])
    op.create_table("transcript_words", sa.Column("id", sa.String(36), primary_key=True), sa.Column("transcript_id", sa.String(36), sa.ForeignKey("transcripts.id"), nullable=False), sa.Column("segment_id", sa.String(36), sa.ForeignKey("transcript_segments.id")), sa.Column("word_index", sa.Integer(), nullable=False), sa.Column("start_seconds", sa.Float(), nullable=False), sa.Column("end_seconds", sa.Float(), nullable=False), sa.Column("text", sa.String(512), nullable=False), sa.Column("confidence", sa.Float()))
    op.create_index("ix_transcript_words_transcript_id", "transcript_words", ["transcript_id"])


def downgrade() -> None:
    op.drop_table("transcript_words")
    op.drop_table("transcript_segments")
    op.drop_table("transcripts")
    op.drop_table("audio_artifacts")
    op.drop_table("processing_jobs")
