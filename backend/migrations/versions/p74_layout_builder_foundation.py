"""layout builder foundation tables

Revision ID: p74_layout_builder_foundation
Revises: p73_saved_searches
Create Date: 2026-03-04 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op


revision: str = "p74_layout_builder_foundation"
down_revision: Union[str, Sequence[str], None] = "p73_saved_searches"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'layout_page_type') THEN
            CREATE TYPE layout_page_type AS ENUM ('home', 'search_l1', 'search_l2', 'listing_create_stepX');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'layout_revision_status') THEN
            CREATE TYPE layout_revision_status AS ENUM ('draft', 'published', 'archived');
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'layout_audit_action') THEN
            CREATE TYPE layout_audit_action AS ENUM ('CREATE_PAGE', 'CREATE_REVISION', 'PUBLISH', 'ARCHIVE', 'BIND', 'UNBIND', 'UPDATE_SCHEMA');
        END IF;
    END
    $$;
    """)

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS layout_component_definitions (
            id UUID PRIMARY KEY,
            key VARCHAR(128) NOT NULL,
            name VARCHAR(200) NOT NULL,
            schema_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            version INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_layout_component_schema_json_object CHECK (jsonb_typeof(schema_json) = 'object')
        )
        """
    )
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_layout_component_definitions_key ON layout_component_definitions (key)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_layout_component_definitions_active ON layout_component_definitions (is_active)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS layout_pages (
            id UUID PRIMARY KEY,
            page_type layout_page_type NOT NULL,
            country VARCHAR(5) NOT NULL,
            module VARCHAR(64) NOT NULL,
            category_id UUID NULL REFERENCES categories(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_layout_pages_scope
        ON layout_pages (
            page_type,
            country,
            module,
            COALESCE(category_id, '00000000-0000-0000-0000-000000000000'::uuid)
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_layout_pages_lookup ON layout_pages (page_type, country, module, category_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS layout_revisions (
            id UUID PRIMARY KEY,
            layout_page_id UUID NOT NULL REFERENCES layout_pages(id) ON DELETE CASCADE,
            status layout_revision_status NOT NULL DEFAULT 'draft',
            payload_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            version INTEGER NOT NULL,
            published_at TIMESTAMPTZ NULL,
            created_by UUID NULL REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_layout_revisions_payload_json_object CHECK (jsonb_typeof(payload_json) = 'object'),
            CONSTRAINT ck_layout_revisions_published_at_consistency CHECK (
                (status = 'published' AND published_at IS NOT NULL)
                OR (status <> 'published' AND published_at IS NULL)
            )
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_layout_revisions_page_status_version ON layout_revisions (layout_page_id, status, version)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_layout_revisions_page_version ON layout_revisions (layout_page_id, version)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS uq_layout_revisions_single_published ON layout_revisions (layout_page_id) WHERE status = 'published'")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS layout_bindings (
            id UUID PRIMARY KEY,
            country VARCHAR(5) NOT NULL,
            module VARCHAR(64) NOT NULL,
            category_id UUID NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
            layout_page_id UUID NOT NULL REFERENCES layout_pages(id) ON DELETE CASCADE,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_layout_bindings_layout_page_id ON layout_bindings (layout_page_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_layout_bindings_scope ON layout_bindings (country, module, category_id)")
    op.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_layout_bindings_active_scope
        ON layout_bindings (country, module, category_id)
        WHERE is_active = true
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS layout_audit_logs (
            id UUID PRIMARY KEY,
            actor_user_id UUID NULL REFERENCES users(id) ON DELETE SET NULL,
            action layout_audit_action NOT NULL,
            entity_type VARCHAR(64) NOT NULL,
            entity_id VARCHAR(128) NOT NULL,
            before_json JSONB NULL,
            after_json JSONB NOT NULL DEFAULT '{}'::jsonb,
            ip VARCHAR(64) NULL,
            user_agent TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT ck_layout_audit_before_json_object CHECK (before_json IS NULL OR jsonb_typeof(before_json) = 'object'),
            CONSTRAINT ck_layout_audit_after_json_object CHECK (jsonb_typeof(after_json) = 'object')
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_layout_audit_logs_actor_user ON layout_audit_logs (actor_user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_layout_audit_logs_action ON layout_audit_logs (action)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_layout_audit_entity_created ON layout_audit_logs (entity_type, entity_id, created_at)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_layout_audit_entity_created")
    op.execute("DROP INDEX IF EXISTS ix_layout_audit_logs_action")
    op.execute("DROP INDEX IF EXISTS ix_layout_audit_logs_actor_user")
    op.execute("DROP TABLE IF EXISTS layout_audit_logs")

    op.execute("DROP INDEX IF EXISTS uq_layout_bindings_active_scope")
    op.execute("DROP INDEX IF EXISTS ix_layout_bindings_scope")
    op.execute("DROP INDEX IF EXISTS ix_layout_bindings_layout_page_id")
    op.execute("DROP TABLE IF EXISTS layout_bindings")

    op.execute("DROP INDEX IF EXISTS uq_layout_revisions_single_published")
    op.execute("DROP INDEX IF EXISTS uq_layout_revisions_page_version")
    op.execute("DROP INDEX IF EXISTS ix_layout_revisions_page_status_version")
    op.execute("DROP TABLE IF EXISTS layout_revisions")

    op.execute("DROP INDEX IF EXISTS ix_layout_pages_lookup")
    op.execute("DROP INDEX IF EXISTS uq_layout_pages_scope")
    op.execute("DROP TABLE IF EXISTS layout_pages")

    op.execute("DROP INDEX IF EXISTS ix_layout_component_definitions_active")
    op.execute("DROP INDEX IF EXISTS uq_layout_component_definitions_key")
    op.execute("DROP TABLE IF EXISTS layout_component_definitions")

    op.execute("DROP TYPE IF EXISTS layout_audit_action")
    op.execute("DROP TYPE IF EXISTS layout_revision_status")
    op.execute("DROP TYPE IF EXISTS layout_page_type")
