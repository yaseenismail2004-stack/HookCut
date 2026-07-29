"""add transcript based clip selection"""

from alembic import op
import sqlalchemy as sa

revision = "20260729_03"
down_revision = "20260729_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("clip_selection_runs",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("video_id", sa.String(36), sa.ForeignKey("video_assets.id"), nullable=False), sa.Column("transcript_id", sa.String(36), sa.ForeignKey("transcripts.id"), nullable=False), sa.Column("job_id", sa.String(36), sa.ForeignKey("processing_jobs.id"), nullable=False, unique=True),
        sa.Column("requested_clip_count", sa.Integer(), nullable=False), sa.Column("platform", sa.String(16), nullable=False), sa.Column("duration_mode", sa.String(16), nullable=False), sa.Column("minimum_duration_seconds", sa.Float(), nullable=False), sa.Column("maximum_duration_seconds", sa.Float(), nullable=False), sa.Column("selection_mode", sa.String(32), nullable=False), sa.Column("diversity_mode", sa.String(32), nullable=False), sa.Column("provider", sa.String(32), nullable=False), sa.Column("model", sa.String(128)), sa.Column("estimated_cost_usd", sa.Float()), sa.Column("actual_cost_usd", sa.Float()), sa.Column("candidate_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("selected_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("reserve_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("rejected_count", sa.Integer(), nullable=False, server_default="0"), sa.Column("status", sa.String(32), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_clip_selection_runs_video_id", "clip_selection_runs", ["video_id"])
    op.create_index("ix_clip_selection_runs_transcript_id", "clip_selection_runs", ["transcript_id"])
    op.create_table("clip_candidates",
        sa.Column("id", sa.String(36), primary_key=True), sa.Column("selection_run_id", sa.String(36), sa.ForeignKey("clip_selection_runs.id"), nullable=False), sa.Column("video_id", sa.String(36), sa.ForeignKey("video_assets.id"), nullable=False), sa.Column("transcript_id", sa.String(36), sa.ForeignKey("transcripts.id"), nullable=False), sa.Column("start_seconds", sa.Float(), nullable=False), sa.Column("end_seconds", sa.Float(), nullable=False), sa.Column("duration_seconds", sa.Float(), nullable=False), sa.Column("timestamp_precision", sa.String(16), nullable=False), sa.Column("transcript_text", sa.Text(), nullable=False), sa.Column("topic", sa.String(256), nullable=False), sa.Column("summary", sa.Text(), nullable=False), sa.Column("hook_type", sa.String(64), nullable=False), sa.Column("hook_text", sa.Text(), nullable=False), sa.Column("hook_score", sa.Float(), nullable=False), sa.Column("hook_reason", sa.Text(), nullable=False), sa.Column("first_1_second_score", sa.Float(), nullable=False), sa.Column("first_3_seconds_score", sa.Float(), nullable=False), sa.Column("first_5_seconds_score", sa.Float(), nullable=False), sa.Column("retention_score", sa.Float(), nullable=False), sa.Column("retention_reason", sa.Text(), nullable=False), sa.Column("standalone_score", sa.Float(), nullable=False), sa.Column("usefulness_score", sa.Float(), nullable=False), sa.Column("entertainment_score", sa.Float(), nullable=False), sa.Column("emotional_impact_score", sa.Float(), nullable=False), sa.Column("share_potential_score", sa.Float(), nullable=False), sa.Column("save_potential_score", sa.Float(), nullable=False), sa.Column("comment_potential_score", sa.Float(), nullable=False), sa.Column("loop_potential_score", sa.Float(), nullable=False), sa.Column("visual_suitability_score", sa.Float(), nullable=False), sa.Column("viral_potential_score", sa.Float(), nullable=False), sa.Column("confidence_score", sa.Float(), nullable=False), sa.Column("ideal_platform", sa.String(16), nullable=False), sa.Column("target_audience", sa.String(256), nullable=False), sa.Column("likely_viewer_reaction", sa.String(256), nullable=False), sa.Column("suggested_title", sa.String(256), nullable=False), sa.Column("suggested_on_screen_hook", sa.String(256), nullable=False), sa.Column("detected_weaknesses", sa.Text(), nullable=False), sa.Column("boundary_mode", sa.String(32), nullable=False), sa.Column("selection_status", sa.String(32), nullable=False), sa.Column("selection_reason", sa.Text(), nullable=False), sa.Column("rejection_reason", sa.Text()), sa.Column("similarity_group", sa.String(64)), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
    )
    op.create_index("ix_clip_candidates_selection_run_id", "clip_candidates", ["selection_run_id"])
    op.create_index("ix_clip_candidates_video_id", "clip_candidates", ["video_id"])


def downgrade() -> None:
    op.drop_table("clip_candidates")
    op.drop_table("clip_selection_runs")
