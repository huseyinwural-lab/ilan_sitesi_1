from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.core.security import check_permissions
from app.models.user import User
from app.models.core import AuditLog
from app.schemas.core import AuditLogResponse

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

@router.get("/", response_model=List[AuditLogResponse])
async def get_audit_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    user_id: Optional[str] = None,
    country_scope: Optional[str] = None,
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin", "finance"]))
):
    query = select(AuditLog)
    
    if action:
        query = query.where(AuditLog.action == action)
    
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    
    if country_scope:
        query = query.where(AuditLog.country_scope == country_scope)
    
    if from_date:
        query = query.where(AuditLog.created_at >= from_date)
    
    if to_date:
        query = query.where(AuditLog.created_at <= to_date)
    
    query = query.order_by(desc(AuditLog.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/actions")
async def get_audit_actions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    """Get distinct action types"""
    return {
        "actions": ["CREATE", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "TOGGLE", "SUSPEND", "ACTIVATE", "APPROVE", "REJECT"]
    }

@router.get("/resource-types")
async def get_resource_types(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "country_admin"]))
):
    """Get distinct resource types"""
    return {
        "resource_types": ["user", "feature_flag", "country", "category", "listing", "dealer", "invoice", "premium"]
    }
