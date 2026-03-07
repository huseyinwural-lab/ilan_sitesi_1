from __future__ import annotations

from datetime import datetime, timezone
import enum
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LayoutPageType(str, enum.Enum):
    HOME = "home"
    CATEGORY_L0_L1 = "category_l0_l1"
    SEARCH_LN = "search_ln"
    URGENT_LISTINGS = "urgent_listings"
    CATEGORY_SHOWCASE = "category_showcase"
    LISTING_DETAIL = "listing_detail"
    LISTING_DETAIL_PARAMETERS = "listing_detail_parameters"
    STOREFRONT_PROFILE = "storefront_profile"
    WIZARD_STEP_L0 = "wizard_step_l0"
    WIZARD_STEP_LN = "wizard_step_ln"
    WIZARD_STEP_FORM = "wizard_step_form"
    WIZARD_PREVIEW = "wizard_preview"
    WIZARD_DOPING_PAYMENT = "wizard_doping_payment"
    WIZARD_RESULT = "wizard_result"
    USER_DASHBOARD = "user_dashboard"

    # Legacy/compat page types kept for backward compatibility
    SEARCH_L1 = "search_l1"
    SEARCH_L2 = "search_l2"
    LISTING_CREATE_STEPX = "listing_create_stepX"


class LayoutRevisionStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class LayoutAuditAction(str, enum.Enum):
    CREATE_PAGE = "CREATE_PAGE"
    CREATE_REVISION = "CREATE_REVISION"
    PUBLISH = "PUBLISH"
    ARCHIVE = "ARCHIVE"
    BIND = "BIND"
    UNBIND = "UNBIND"
    UPDATE_SCHEMA = "UPDATE_SCHEMA"


class LayoutPresetEventType(str, enum.Enum):
    APPLY = "apply"
    PUBLISH = "publish"


class LayoutComponentDefinition(Base):
    __tablename__ = "layout_component_definitions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    schema_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        CheckConstraint("jsonb_typeof(schema_json) = 'object'", name="ck_layout_component_schema_json_object"),
    )


class LayoutPage(Base):
    __tablename__ = "layout_pages"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    page_type: Mapped[LayoutPageType] = mapped_column(
        Enum(
            LayoutPageType,
            name="layout_page_type",
            native_enum=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
    )
    country: Mapped[str] = mapped_column(String(5), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    category_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )
    title_i18n: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    description_i18n: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    label_i18n: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    revisions: Mapped[list["LayoutRevision"]] = relationship(
        "LayoutRevision",
        back_populates="layout_page",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index(
            "uq_layout_pages_scope",
            "page_type",
            "country",
            "module",
            text("COALESCE(category_id, '00000000-0000-0000-0000-000000000000'::uuid)"),
            unique=True,
        ),
        Index("ix_layout_pages_lookup", "page_type", "country", "module", "category_id"),
    )


class LayoutRevision(Base):
    __tablename__ = "layout_revisions"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    layout_page_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("layout_pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[LayoutRevisionStatus] = mapped_column(
        Enum(
            LayoutRevisionStatus,
            name="layout_revision_status",
            native_enum=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        default=LayoutRevisionStatus.DRAFT,
    )
    payload_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    version: Mapped[int] = mapped_column(Integer, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    layout_page: Mapped["LayoutPage"] = relationship("LayoutPage", back_populates="revisions")

    __table_args__ = (
        CheckConstraint("jsonb_typeof(payload_json) = 'object'", name="ck_layout_revisions_payload_json_object"),
        CheckConstraint(
            "(status = 'published' AND published_at IS NOT NULL) OR (status <> 'published' AND published_at IS NULL)",
            name="ck_layout_revisions_published_at_consistency",
        ),
        Index("ix_layout_revisions_page_status_version", "layout_page_id", "status", "version"),
        Index("uq_layout_revisions_page_version", "layout_page_id", "version", unique=True),
        Index(
            "uq_layout_revisions_single_published",
            "layout_page_id",
            unique=True,
            postgresql_where=text("status = 'published'"),
        ),
        Index(
            "uq_layout_revisions_single_active_live",
            "layout_page_id",
            unique=True,
            postgresql_where=text("status = 'published' AND is_active = true AND is_deleted = false"),
        ),
    )


class LayoutBinding(Base):
    __tablename__ = "layout_bindings"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    country: Mapped[str] = mapped_column(String(5), nullable=False)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    category_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    layout_page_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("layout_pages.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_layout_bindings_layout_page_id", "layout_page_id"),
        Index("ix_layout_bindings_scope", "country", "module", "category_id"),
        Index(
            "uq_layout_bindings_active_scope",
            "country",
            "module",
            "category_id",
            unique=True,
            postgresql_where=text("is_active = true"),
        ),
    )


class LayoutAuditLog(Base):
    __tablename__ = "layout_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[LayoutAuditAction] = mapped_column(
        Enum(
            LayoutAuditAction,
            name="layout_audit_action",
            native_enum=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(128), nullable=False)
    before_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    after_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint("before_json IS NULL OR jsonb_typeof(before_json) = 'object'", name="ck_layout_audit_before_json_object"),
        CheckConstraint("jsonb_typeof(after_json) = 'object'", name="ck_layout_audit_after_json_object"),
        Index("ix_layout_audit_entity_created", "entity_type", "entity_id", "created_at"),
    )


class LayoutPresetEvent(Base):
    __tablename__ = "layout_preset_events"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    layout_page_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("layout_pages.id", ondelete="SET NULL"),
        nullable=True,
    )
    page_type: Mapped[LayoutPageType | None] = mapped_column(
        Enum(
            LayoutPageType,
            name="layout_page_type",
            native_enum=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=True,
    )
    country: Mapped[str | None] = mapped_column(String(5), nullable=True)
    module: Mapped[str | None] = mapped_column(String(64), nullable=True)
    preset_id: Mapped[str] = mapped_column(String(120), nullable=False)
    preset_label: Mapped[str] = mapped_column(String(200), nullable=False)
    persona: Mapped[str] = mapped_column(String(32), nullable=False)
    variant: Mapped[str] = mapped_column(String(16), nullable=False)
    event_type: Mapped[LayoutPresetEventType] = mapped_column(
        Enum(
            LayoutPresetEventType,
            name="layout_preset_event_type",
            native_enum=True,
            values_callable=lambda enum_cls: [item.value for item in enum_cls],
        ),
        nullable=False,
        index=True,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    page: Mapped[LayoutPage | None] = relationship("LayoutPage", lazy="joined")

    __table_args__ = (
        CheckConstraint("char_length(preset_id) > 0", name="ck_layout_preset_events_preset_id_not_empty"),
        CheckConstraint("char_length(persona) > 0", name="ck_layout_preset_events_persona_not_empty"),
        Index("ix_layout_preset_events_grouping", "preset_id", "persona", "variant", "event_type", "created_at"),
        Index("ix_layout_preset_events_scope", "country", "module", "created_at"),
    )


class LayoutPresetRunLog(Base):
    __tablename__ = "layout_preset_run_logs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    executed_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    executed_by_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    executed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    target_countries: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    total_jobs: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    success_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    duration_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="success", index=True)
    module: Mapped[str] = mapped_column(String(64), nullable=False)
    persona: Mapped[str] = mapped_column(String(32), nullable=False)
    variant: Mapped[str] = mapped_column(String(16), nullable=False)
    fail_fast: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    publish_after_seed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    include_extended_templates: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    error_logs_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))

    __table_args__ = (
        CheckConstraint("char_length(module) > 0", name="ck_layout_preset_run_logs_module_not_empty"),
        CheckConstraint("char_length(persona) > 0", name="ck_layout_preset_run_logs_persona_not_empty"),
        CheckConstraint("char_length(variant) > 0", name="ck_layout_preset_run_logs_variant_not_empty"),
        CheckConstraint("jsonb_typeof(target_countries) = 'array'", name="ck_layout_preset_run_logs_target_countries_array"),
        CheckConstraint("jsonb_typeof(summary_json) = 'object'", name="ck_layout_preset_run_logs_summary_json_object"),
        CheckConstraint("jsonb_typeof(error_logs_json) = 'array'", name="ck_layout_preset_run_logs_error_logs_json_array"),
        Index("ix_layout_preset_run_logs_status_executed", "status", "executed_at"),
        Index("ix_layout_preset_run_logs_module_executed", "module", "executed_at"),
    )


class AdminRevisionRedirectEvent(Base):
    __tablename__ = "admin_revision_redirect_events"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_name: Mapped[str] = mapped_column(String(64), nullable=False, default="admin_revision_redirect", index=True)
    revision_id: Mapped[uuid.UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    admin_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    redirect_target: Mapped[str | None] = mapped_column(String(512), nullable=True)
    redirect_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    redirect_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    redirect_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="success", index=True)
    failure_reason: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    meta_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        CheckConstraint("char_length(event_name) > 0", name="ck_admin_rev_redirect_event_name_not_empty"),
        CheckConstraint("status IN ('success','failed')", name="ck_admin_rev_redirect_status"),
        CheckConstraint("jsonb_typeof(meta_json) = 'object'", name="ck_admin_rev_redirect_meta_json_object"),
        Index("ix_admin_rev_redirect_created_status", "created_at", "status"),
        Index("ix_admin_rev_redirect_failure_reason", "failure_reason", "created_at"),
    )


class LayoutReleaseCleanupAudit(Base):
    __tablename__ = "layout_release_cleanup_audits"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_user_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    retention_window_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    trigger_source: Mapped[str] = mapped_column(String(64), nullable=False, default="admin_panel")
    deleted_artifacts: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    protected_artifacts: Mapped[list] = mapped_column(JSONB, nullable=False, default=list, server_default=text("'[]'::jsonb"))
    dry_run_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        CheckConstraint("retention_window_days >= 1", name="ck_layout_release_cleanup_retention_window_min"),
        CheckConstraint("char_length(trigger_source) > 0", name="ck_layout_release_cleanup_trigger_source_not_empty"),
        CheckConstraint("jsonb_typeof(deleted_artifacts) = 'array'", name="ck_layout_release_cleanup_deleted_array"),
        CheckConstraint("jsonb_typeof(protected_artifacts) = 'array'", name="ck_layout_release_cleanup_protected_array"),
        CheckConstraint("jsonb_typeof(dry_run_json) = 'object'", name="ck_layout_release_cleanup_dry_run_object"),
        Index("ix_layout_release_cleanup_created", "created_at"),
    )


class LayoutPresetExportJob(Base):
    __tablename__ = "layout_preset_export_jobs"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    requested_by: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    requested_by_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    export_scope: Mapped[str] = mapped_column(String(24), nullable=False, default="admin", index=True)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="queued", index=True)
    filters_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    row_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancel_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    meta_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))

    __table_args__ = (
        CheckConstraint("status IN ('queued','running','completed','failed','cancelled')", name="ck_layout_preset_export_job_status"),
        CheckConstraint("export_scope IN ('admin','dealer')", name="ck_layout_preset_export_job_scope"),
        CheckConstraint("row_count >= 0", name="ck_layout_preset_export_job_row_count_non_negative"),
        CheckConstraint("jsonb_typeof(filters_json) = 'object'", name="ck_layout_preset_export_job_filters_object"),
        CheckConstraint("jsonb_typeof(meta_json) = 'object'", name="ck_layout_preset_export_job_meta_object"),
        Index("ix_layout_preset_export_jobs_status_created", "status", "created_at"),
        Index("ix_layout_preset_export_jobs_scope_created", "export_scope", "created_at"),
    )
