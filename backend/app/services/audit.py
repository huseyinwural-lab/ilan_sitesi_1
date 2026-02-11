from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from uuid import UUID

from app.models.core import AuditLog

async def log_action(
    db: AsyncSession,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    user_id: Optional[UUID] = None,
    user_email: Optional[str] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    metadata: Optional[dict] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    country_scope: Optional[str] = None
):
    """Create an audit log entry"""
    audit_log = AuditLog(
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        user_id=user_id,
        user_email=user_email,
        old_values=old_values,
        new_values=new_values,
        metadata=metadata,
        ip_address=ip_address,
        user_agent=user_agent,
        country_scope=country_scope
    )
    
    db.add(audit_log)
    await db.commit()
    
    return audit_log
