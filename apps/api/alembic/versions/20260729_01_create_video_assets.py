"""create video assets"""
from alembic import op
import sqlalchemy as sa

revision = "20260729_01"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table("video_assets", sa.Column("id", sa.String(36), primary_key=True), sa.Column("original_filename", sa.String(255), nullable=False), sa.Column("stored_filename", sa.String(255), nullable=False, unique=True), sa.Column("file_size_bytes", sa.Integer(), nullable=False), sa.Column("container", sa.String(64)), sa.Column("duration_seconds", sa.Float()), sa.Column("width", sa.Integer()), sa.Column("height", sa.Integer()), sa.Column("frame_rate", sa.Float()), sa.Column("video_codec", sa.String(64)), sa.Column("audio_codec", sa.String(64)), sa.Column("audio_channels", sa.Integer()), sa.Column("audio_sample_rate", sa.Integer()), sa.Column("status", sa.String(16), nullable=False), sa.Column("validation_error", sa.Text()), sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False))

def downgrade() -> None:
    op.drop_table("video_assets")
