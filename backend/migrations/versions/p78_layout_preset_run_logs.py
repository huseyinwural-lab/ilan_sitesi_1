"""create layout preset run logs table

Revision ID: p78_preset_run_logs
Revises: p77_active_live_idx
Create Date: 2026-03-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "p78_preset_run_logs"
down_revision: Union[str, Sequence[str], None] = "p77_active_live_idx"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS layout_preset_run_logs (
          id uuid PRIMARY KEY,
          executed_by uuid NULL REFERENCES users(id) ON DELETE SET NULL,
          executed_by_email varchar(255) NULL,
          executed_at timestamptz NOT NULL DEFAULT now(),
          target_countries jsonb NOT NULL DEFAULT '[]'::jsonb,
          total_jobs integer NOT NULL DEFAULT 0,
          success_count integer NOT NULL DEFAULT 0,
          failure_count integer NOT NULL DEFAULT 0,
          duration_ms integer NOT NULL DEFAULT 0,
          status varchar(24) NOT NULL DEFAULT 'success',
          module varchar(64) NOT NULL,
          persona varchar(32) NOT NULL,
          variant varchar(16) NOT NULL,
          fail_fast boolean NOT NULL DEFAULT true,
          publish_after_seed boolean NOT NULL DEFAULT true,
          include_extended_templates boolean NOT NULL DEFAULT false,
          summary_json jsonb NOT NULL DEFAULT '{}'::jsonb,
          error_logs_json jsonb NOT NULL DEFAULT '[]'::jsonb,
          CONSTRAINT ck_layout_preset_run_logs_module_not_empty CHECK (char_length(module) > 0),
          CONSTRAINT ck_layout_preset_run_logs_persona_not_empty CHECK (char_length(persona) > 0),
          CONSTRAINT ck_layout_preset_run_logs_variant_not_empty CHECK (char_length(variant) > 0),
          CONSTRAINT ck_layout_preset_run_logs_target_countries_array CHECK (jsonb_typeof(target_countries) = 'array'),
          CONSTRAINT ck_layout_preset_run_logs_summary_json_object CHECK (jsonb_typeof(summary_json) = 'object'),
          CONSTRAINT ck_layout_preset_run_logs_error_logs_json_array CHECK (jsonb_typeof(error_logs_json) = 'array')
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_layout_preset_run_logs_executed_by
        ON layout_preset_run_logs (executed_by)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_layout_preset_run_logs_executed_at
        ON layout_preset_run_logs (executed_at)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_layout_preset_run_logs_status
        ON layout_preset_run_logs (status)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_layout_preset_run_logs_status_executed
        ON layout_preset_run_logs (status, executed_at)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_layout_preset_run_logs_module_executed
        ON layout_preset_run_logs (module, executed_at)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS layout_preset_run_logs")
