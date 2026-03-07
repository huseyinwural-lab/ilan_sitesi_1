"""create admin revision redirect telemetry events

Revision ID: p79_rev_redirect_events
Revises: p78_preset_run_logs
Create Date: 2026-03-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "p79_rev_redirect_events"
down_revision: Union[str, Sequence[str], None] = "p78_preset_run_logs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS admin_revision_redirect_events (
          id uuid PRIMARY KEY,
          event_name varchar(64) NOT NULL DEFAULT 'admin_revision_redirect',
          revision_id uuid NULL,
          admin_user_id uuid NULL REFERENCES users(id) ON DELETE SET NULL,
          redirect_target varchar(512) NULL,
          redirect_started_at timestamptz NULL,
          redirect_completed_at timestamptz NULL,
          redirect_duration_ms integer NULL,
          status varchar(16) NOT NULL DEFAULT 'success',
          failure_reason varchar(64) NULL,
          created_at timestamptz NOT NULL DEFAULT now(),
          meta_json jsonb NOT NULL DEFAULT '{}'::jsonb,
          CONSTRAINT ck_admin_rev_redirect_event_name_not_empty CHECK (char_length(event_name) > 0),
          CONSTRAINT ck_admin_rev_redirect_status CHECK (status IN ('success','failed')),
          CONSTRAINT ck_admin_rev_redirect_meta_json_object CHECK (jsonb_typeof(meta_json) = 'object')
        )
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_admin_revision_redirect_events_revision_id
        ON admin_revision_redirect_events (revision_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_admin_revision_redirect_events_admin_user_id
        ON admin_revision_redirect_events (admin_user_id)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_admin_revision_redirect_events_status
        ON admin_revision_redirect_events (status)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_admin_revision_redirect_events_failure_reason
        ON admin_revision_redirect_events (failure_reason)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_admin_revision_redirect_events_created_at
        ON admin_revision_redirect_events (created_at)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_admin_rev_redirect_created_status
        ON admin_revision_redirect_events (created_at, status)
        """
    )
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_admin_rev_redirect_failure_reason
        ON admin_revision_redirect_events (failure_reason, created_at)
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS admin_revision_redirect_events")
