from __future__ import annotations

from datetime import datetime, timezone
import uuid

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.layout_builder import (
    LayoutAuditAction,
    LayoutAuditLog,
    LayoutBinding,
    LayoutComponentDefinition,
    LayoutPage,
    LayoutPageType,
    LayoutRevision,
    LayoutRevisionStatus,
)


async def write_layout_audit_log(
    session: AsyncSession,
    *,
    actor_user_id: str | None,
    action: LayoutAuditAction,
    entity_type: str,
    entity_id: str,
    before_json: dict | None,
    after_json: dict,
    ip: str | None = None,
    user_agent: str | None = None,
) -> LayoutAuditLog:
    row = LayoutAuditLog(
        actor_user_id=_safe_uuid(actor_user_id),
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        before_json=before_json if before_json is not None else {},
        after_json=after_json or {},
        ip=ip,
        user_agent=user_agent,
        created_at=datetime.now(timezone.utc),
    )
    session.add(row)
    await session.flush()
    return row


def _safe_uuid(raw_value: str | None) -> uuid.UUID | None:
    if not raw_value:
        return None
    try:
        return uuid.UUID(str(raw_value))
    except (TypeError, ValueError):
        return None


async def create_or_update_component_definition(
    session: AsyncSession,
    *,
    key: str,
    name: str,
    schema_json: dict,
    is_active: bool,
    actor_user_id: str | None,
) -> LayoutComponentDefinition:
    existing_result = await session.execute(
        select(LayoutComponentDefinition).where(LayoutComponentDefinition.key == key)
    )
    existing = existing_result.scalar_one_or_none()
    now_dt = datetime.now(timezone.utc)

    if existing:
        before = {
            "key": existing.key,
            "name": existing.name,
            "schema_json": existing.schema_json,
            "is_active": existing.is_active,
            "version": int(existing.version),
        }
        existing.name = name
        existing.schema_json = schema_json
        existing.is_active = bool(is_active)
        existing.version = int(existing.version) + 1
        existing.updated_at = now_dt
        await session.flush()
        await write_layout_audit_log(
            session,
            actor_user_id=actor_user_id,
            action=LayoutAuditAction.UPDATE_SCHEMA,
            entity_type="layout_component_definition",
            entity_id=str(existing.id),
            before_json=before,
            after_json={
                "key": existing.key,
                "name": existing.name,
                "schema_json": existing.schema_json,
                "is_active": existing.is_active,
                "version": int(existing.version),
            },
        )
        return existing

    row = LayoutComponentDefinition(
        key=key,
        name=name,
        schema_json=schema_json,
        is_active=bool(is_active),
        version=1,
        created_at=now_dt,
        updated_at=now_dt,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise ValueError("component_key_conflict") from exc

    await write_layout_audit_log(
        session,
        actor_user_id=actor_user_id,
        action=LayoutAuditAction.UPDATE_SCHEMA,
        entity_type="layout_component_definition",
        entity_id=str(row.id),
        before_json=None,
        after_json={
            "key": row.key,
            "name": row.name,
            "schema_json": row.schema_json,
            "is_active": row.is_active,
            "version": int(row.version),
        },
    )
    return row


async def create_layout_page(
    session: AsyncSession,
    *,
    page_type: LayoutPageType,
    country: str,
    module: str,
    category_id: str | None,
    actor_user_id: str | None,
) -> LayoutPage:
    now_dt = datetime.now(timezone.utc)
    row = LayoutPage(
        page_type=page_type,
        country=(country or "").upper(),
        module=(module or "").strip(),
        category_id=_safe_uuid(category_id),
        created_at=now_dt,
        updated_at=now_dt,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise ValueError("layout_page_scope_conflict") from exc

    await write_layout_audit_log(
        session,
        actor_user_id=actor_user_id,
        action=LayoutAuditAction.CREATE_PAGE,
        entity_type="layout_page",
        entity_id=str(row.id),
        before_json=None,
        after_json={
            "page_type": row.page_type.value,
            "country": row.country,
            "module": row.module,
            "category_id": str(row.category_id) if row.category_id else None,
        },
    )
    return row


async def _next_revision_version(session: AsyncSession, layout_page_id: uuid.UUID) -> int:
    result = await session.execute(
        select(func.coalesce(func.max(LayoutRevision.version), 0)).where(LayoutRevision.layout_page_id == layout_page_id)
    )
    max_version = result.scalar_one()
    return int(max_version) + 1


async def create_draft_revision(
    session: AsyncSession,
    *,
    layout_page_id: str,
    payload_json: dict,
    actor_user_id: str | None,
) -> LayoutRevision:
    page_uuid = _safe_uuid(layout_page_id)
    if not page_uuid:
        raise ValueError("invalid_layout_page_id")

    page = await session.get(LayoutPage, page_uuid)
    if not page:
        raise ValueError("layout_page_not_found")

    next_version = await _next_revision_version(session, page_uuid)
    row = LayoutRevision(
        layout_page_id=page_uuid,
        status=LayoutRevisionStatus.DRAFT,
        payload_json=payload_json or {},
        version=next_version,
        created_by=_safe_uuid(actor_user_id),
        created_at=datetime.now(timezone.utc),
    )
    session.add(row)

    try:
        await session.flush()
    except IntegrityError as exc:
        raise ValueError("layout_revision_version_conflict") from exc

    await write_layout_audit_log(
        session,
        actor_user_id=actor_user_id,
        action=LayoutAuditAction.CREATE_REVISION,
        entity_type="layout_revision",
        entity_id=str(row.id),
        before_json=None,
        after_json={
            "layout_page_id": str(row.layout_page_id),
            "status": row.status.value,
            "version": int(row.version),
        },
    )
    return row


async def publish_revision(
    session: AsyncSession,
    *,
    revision_id: str,
    actor_user_id: str | None,
) -> LayoutRevision:
    revision_uuid = _safe_uuid(revision_id)
    if not revision_uuid:
        raise ValueError("invalid_revision_id")

    draft = await session.get(LayoutRevision, revision_uuid)
    if not draft:
        raise ValueError("revision_not_found")

    if draft.status != LayoutRevisionStatus.DRAFT:
        raise ValueError("only_draft_can_be_published")

    now_dt = datetime.now(timezone.utc)
    await session.execute(
        update(LayoutRevision)
        .where(
            and_(
                LayoutRevision.layout_page_id == draft.layout_page_id,
                LayoutRevision.status == LayoutRevisionStatus.PUBLISHED,
            )
        )
        .values(status=LayoutRevisionStatus.ARCHIVED, published_at=None)
    )

    next_version = await _next_revision_version(session, draft.layout_page_id)
    published = LayoutRevision(
        layout_page_id=draft.layout_page_id,
        status=LayoutRevisionStatus.PUBLISHED,
        payload_json=draft.payload_json or {},
        version=next_version,
        published_at=now_dt,
        created_by=_safe_uuid(actor_user_id),
        created_at=now_dt,
    )
    session.add(published)

    try:
        await session.flush()
    except IntegrityError as exc:
        raise ValueError("published_revision_conflict") from exc

    draft.status = LayoutRevisionStatus.ARCHIVED
    draft.published_at = None

    await write_layout_audit_log(
        session,
        actor_user_id=actor_user_id,
        action=LayoutAuditAction.PUBLISH,
        entity_type="layout_revision",
        entity_id=str(published.id),
        before_json={
            "source_revision_id": str(draft.id),
            "source_version": int(draft.version),
        },
        after_json={
            "layout_page_id": str(published.layout_page_id),
            "status": published.status.value,
            "version": int(published.version),
            "published_at": published.published_at.isoformat() if published.published_at else None,
        },
    )
    return published


async def archive_revision(
    session: AsyncSession,
    *,
    revision_id: str,
    actor_user_id: str | None,
) -> LayoutRevision:
    revision_uuid = _safe_uuid(revision_id)
    if not revision_uuid:
        raise ValueError("invalid_revision_id")

    row = await session.get(LayoutRevision, revision_uuid)
    if not row:
        raise ValueError("revision_not_found")

    before = {
        "status": row.status.value,
        "published_at": row.published_at.isoformat() if row.published_at else None,
    }
    row.status = LayoutRevisionStatus.ARCHIVED
    row.published_at = None
    await session.flush()

    await write_layout_audit_log(
        session,
        actor_user_id=actor_user_id,
        action=LayoutAuditAction.ARCHIVE,
        entity_type="layout_revision",
        entity_id=str(row.id),
        before_json=before,
        after_json={
            "status": row.status.value,
            "published_at": row.published_at,
        },
    )
    return row


async def bind_category_to_page(
    session: AsyncSession,
    *,
    country: str,
    module: str,
    category_id: str,
    layout_page_id: str,
    actor_user_id: str | None,
) -> LayoutBinding:
    category_uuid = _safe_uuid(category_id)
    page_uuid = _safe_uuid(layout_page_id)
    if not category_uuid:
        raise ValueError("invalid_category_id")
    if not page_uuid:
        raise ValueError("invalid_layout_page_id")

    page = await session.get(LayoutPage, page_uuid)
    if not page:
        raise ValueError("layout_page_not_found")

    now_dt = datetime.now(timezone.utc)
    await session.execute(
        update(LayoutBinding)
        .where(
            and_(
                LayoutBinding.country == (country or "").upper(),
                LayoutBinding.module == (module or "").strip(),
                LayoutBinding.category_id == category_uuid,
                LayoutBinding.is_active.is_(True),
            )
        )
        .values(is_active=False, updated_at=now_dt)
    )

    row = LayoutBinding(
        country=(country or "").upper(),
        module=(module or "").strip(),
        category_id=category_uuid,
        layout_page_id=page_uuid,
        is_active=True,
        created_at=now_dt,
        updated_at=now_dt,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:
        raise ValueError("active_binding_conflict") from exc

    await write_layout_audit_log(
        session,
        actor_user_id=actor_user_id,
        action=LayoutAuditAction.BIND,
        entity_type="layout_binding",
        entity_id=str(row.id),
        before_json=None,
        after_json={
            "country": row.country,
            "module": row.module,
            "category_id": str(row.category_id),
            "layout_page_id": str(row.layout_page_id),
            "is_active": row.is_active,
        },
    )
    return row


async def unbind_category(
    session: AsyncSession,
    *,
    country: str,
    module: str,
    category_id: str,
    actor_user_id: str | None,
) -> int:
    category_uuid = _safe_uuid(category_id)
    if not category_uuid:
        raise ValueError("invalid_category_id")

    query = (
        update(LayoutBinding)
        .where(
            and_(
                LayoutBinding.country == (country or "").upper(),
                LayoutBinding.module == (module or "").strip(),
                LayoutBinding.category_id == category_uuid,
                LayoutBinding.is_active.is_(True),
            )
        )
        .values(is_active=False, updated_at=datetime.now(timezone.utc))
        .returning(LayoutBinding.id)
    )
    result = await session.execute(query)
    changed_rows = [str(row[0]) for row in result.all()]

    await write_layout_audit_log(
        session,
        actor_user_id=actor_user_id,
        action=LayoutAuditAction.UNBIND,
        entity_type="layout_binding",
        entity_id=category_id,
        before_json={"active_binding_ids": changed_rows},
        after_json={
            "country": (country or "").upper(),
            "module": (module or "").strip(),
            "category_id": category_id,
            "unbound_count": len(changed_rows),
        },
    )
    return len(changed_rows)


async def get_latest_published_revision_for_page(
    session: AsyncSession,
    *,
    layout_page_id: uuid.UUID,
) -> LayoutRevision | None:
    result = await session.execute(
        select(LayoutRevision)
        .where(
            and_(
                LayoutRevision.layout_page_id == layout_page_id,
                LayoutRevision.status == LayoutRevisionStatus.PUBLISHED,
            )
        )
        .order_by(desc(LayoutRevision.version))
        .limit(1)
    )
    return result.scalar_one_or_none()
