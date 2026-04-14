"""initial schema

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "datasets",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("row_count", sa.BigInteger(), nullable=True),
        sa.Column("column_count", sa.Integer(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("is_baseline", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_datasets_user_id", "datasets", ["user_id"])

    op.create_table(
        "jobs",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dataset_id", UUID(as_uuid=False), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PENDING"),
        sa.Column("pipeline_config", JSONB(), nullable=False, server_default="{}"),
        sa.Column("progress", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_jobs_dataset_id", "jobs", ["dataset_id"])
    op.create_index("ix_jobs_user_id", "jobs", ["user_id"])

    op.create_table(
        "dataset_versions",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("dataset_id", UUID(as_uuid=False), sa.ForeignKey("datasets.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("job_id", UUID(as_uuid=False), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("transform_params", JSONB(), nullable=True),
        sa.Column("quality_score", sa.Numeric(5, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_dataset_versions_dataset_id", "dataset_versions", ["dataset_id"])

    op.create_table(
        "alerts",
        sa.Column("id", UUID(as_uuid=False), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", UUID(as_uuid=False), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("job_id", UUID(as_uuid=False), sa.ForeignKey("jobs.id"), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("is_resolved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index("ix_alerts_user_id", "alerts", ["user_id"])


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("dataset_versions")
    op.drop_table("jobs")
    op.drop_table("datasets")
    op.drop_table("users")
