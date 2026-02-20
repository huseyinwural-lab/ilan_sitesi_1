import os
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.application import Application
from app.models.user import User as SqlUser


def resolve_applications_provider(mongo_enabled: bool) -> str:
    provider = os.environ.get("APPLICATIONS_PROVIDER")
    if provider:
        return provider.lower()
    return "mongo" if mongo_enabled else "sql"


class ApplicationsRepository:
    async def create_application(self, payload: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    async def list_applications(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError

    async def assign_application(self, application_id: str, assigned_to: Optional[str]) -> Dict[str, Any]:
        raise NotImplementedError

    async def update_status(self, application_id: str, status: str, decision_reason: Optional[str]) -> Dict[str, Any]:
        raise NotImplementedError


class SqlApplicationsRepository(ApplicationsRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_application(self, payload: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        application_uuid = uuid.uuid4()
        now = datetime.now(timezone.utc)
        user_id_raw = current_user.get("id")
        user_uuid = uuid.UUID(str(user_id_raw)) if user_id_raw else None

        application = Application(
            id=application_uuid,
            application_id=str(application_uuid),
            user_id=user_uuid,
            application_type=payload["application_type"],
            category=payload["category"],
            subject=payload["subject"],
            description=payload["description"],
            attachments=payload.get("attachments") or None,
            extra_data=payload.get("extra_data") or None,
            status=payload.get("status", "pending"),
            priority=payload.get("priority", "medium"),
            assigned_to=None,
            decision_reason=None,
            created_at=now,
            updated_at=now,
        )
        self.session.add(application)
        await self.session.commit()
        return {"application_id": str(application.application_id), "id": str(application.id)}

    async def list_applications(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        application_type = filters["application_type"]
        page = filters.get("page", 1)
        limit = filters.get("limit", 25)
        status = filters.get("status")
        priority = filters.get("priority")
        category = filters.get("category")
        search = filters.get("search")
        country = filters.get("country")
        start_date = filters.get("start_date")
        end_date = filters.get("end_date")

        query = select(Application).where(Application.application_type == application_type)

        if status:
            query = query.where(Application.status == status)
        if priority:
            query = query.where(Application.priority == priority)
        if category:
            query = query.where(Application.category == category)

        user_ids_filter = None
        if search or country:
            user_query = select(SqlUser)
            if search:
                search_value = f"%{search}%"
                user_query = user_query.where(
                    SqlUser.full_name.ilike(search_value) | SqlUser.email.ilike(search_value)
                )
            if country:
                user_query = user_query.where(SqlUser.country_code == country)
            users_res = await self.session.execute(user_query)
            users = users_res.scalars().all()
            user_ids_filter = {user.id for user in users}
            if user_ids_filter:
                query = query.where(Application.user_id.in_(user_ids_filter))
            else:
                return {"items": [], "total_count": 0, "page": page, "limit": limit, "total_pages": 1}

        if start_date or end_date:
            date_filter = []
            if start_date:
                start_dt = datetime.fromisoformat(start_date)
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=timezone.utc)
                if len(start_date) == 10:
                    start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                date_filter.append(Application.created_at >= start_dt)
            if end_date:
                end_dt = datetime.fromisoformat(end_date)
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone.utc)
                if len(end_date) == 10:
                    end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=0)
                date_filter.append(Application.created_at <= end_dt)
            for clause in date_filter:
                query = query.where(clause)

        safe_page = max(page, 1)
        safe_limit = min(max(limit, 1), 200)
        offset = (safe_page - 1) * safe_limit

        total_count = await self.session.scalar(select(func.count()).select_from(query.subquery())) or 0
        result = await self.session.execute(
            query.order_by(Application.created_at.desc()).offset(offset).limit(safe_limit)
        )
        rows = result.scalars().all()

        user_ids = {row.user_id for row in rows if row.user_id}
        assigned_ids = {row.assigned_to for row in rows if row.assigned_to}
        combined_ids = {uid for uid in user_ids | assigned_ids if uid}
        user_map: Dict[uuid.UUID, SqlUser] = {}
        if combined_ids:
            users_res = await self.session.execute(select(SqlUser).where(SqlUser.id.in_(list(combined_ids))))
            for user in users_res.scalars().all():
                user_map[user.id] = user

        items = []
        for row in rows:
            applicant = user_map.get(row.user_id)
            assigned = user_map.get(row.assigned_to) if row.assigned_to else None
            applicant_name = None
            applicant_email = None
            applicant_country = None
            if applicant:
                applicant_name = applicant.full_name or applicant.email
                applicant_email = applicant.email
                applicant_country = applicant.country_code

            items.append(
                {
                    "id": str(row.id),
                    "application_id": row.application_id,
                    "application_type": row.application_type,
                    "category": row.category,
                    "subject": row.subject,
                    "description": row.description,
                    "status": row.status,
                    "priority": row.priority,
                    "decision_reason": row.decision_reason,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "updated_at": row.updated_at.isoformat() if row.updated_at else None,
                    "user": {
                        "id": str(row.user_id) if row.user_id else None,
                        "name": applicant_name or "-",
                        "email": applicant_email or "-",
                        "country": applicant_country or "-",
                    },
                    "assigned_to": {
                        "id": str(assigned.id),
                        "name": assigned.full_name or assigned.email,
                        "email": assigned.email,
                    } if assigned else None,
                }
            )

        total_pages = max(1, (total_count + safe_limit - 1) // safe_limit)
        return {
            "items": items,
            "total_count": total_count,
            "page": safe_page,
            "limit": safe_limit,
            "total_pages": total_pages,
        }

    async def assign_application(self, application_id: str, assigned_to: Optional[str]) -> Dict[str, Any]:
        try:
            application_uuid = uuid.UUID(application_id)
        except ValueError:
            raise ValueError("Invalid application id")
        result = await self.session.execute(select(Application).where(Application.id == application_uuid))
        application = result.scalar_one_or_none()
        if not application:
            raise ValueError("Application not found")
        assigned_uuid = uuid.UUID(assigned_to) if assigned_to else None
        application.assigned_to = assigned_uuid
        application.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return {"ok": True}

    async def update_status(self, application_id: str, status: str, decision_reason: Optional[str]) -> Dict[str, Any]:
        try:
            application_uuid = uuid.UUID(application_id)
        except ValueError:
            raise ValueError("Invalid application id")
        result = await self.session.execute(select(Application).where(Application.id == application_uuid))
        application = result.scalar_one_or_none()
        if not application:
            raise ValueError("Application not found")
        application.status = status
        application.decision_reason = decision_reason
        application.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        return {"ok": True, "status": status}


class MongoApplicationsRepository(ApplicationsRepository):
    def __init__(self, db):
        self.db = db

    async def create_application(self, payload: Dict[str, Any], current_user: Dict[str, Any]) -> Dict[str, Any]:
        application_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        doc = {
            "id": application_id,
            "application_id": application_id,
            "user_id": current_user.get("id"),
            "application_type": payload["application_type"],
            "category": payload["category"],
            "subject": payload["subject"],
            "description": payload["description"],
            "attachments": payload.get("attachments") or [],
            "status": payload.get("status", "pending"),
            "priority": payload.get("priority", "medium"),
            "assigned_to": None,
            "decision_reason": None,
            "created_at": now_iso,
            "updated_at": now_iso,
            "applicant_name": current_user.get("full_name") or current_user.get("email"),
            "applicant_company_name": current_user.get("company_name"),
            "applicant_email": current_user.get("email"),
            "applicant_country": current_user.get("country_code"),
            "extra_data": payload.get("extra_data") or {},
        }
        await self.db.support_applications.insert_one(doc)
        return {"application_id": application_id}

    async def list_applications(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        query: Dict[str, Any] = {"application_type": filters["application_type"]}
        if filters.get("category"):
            query["category"] = filters["category"]
        if filters.get("status"):
            query["status"] = filters["status"]
        if filters.get("priority"):
            query["priority"] = filters["priority"]
        if filters.get("country"):
            query["applicant_country"] = filters["country"]

        if filters.get("start_date") or filters.get("end_date"):
            date_filter: Dict[str, Any] = {}
            start_date = filters.get("start_date")
            end_date = filters.get("end_date")
            try:
                if start_date:
                    start_dt = datetime.fromisoformat(start_date)
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=timezone.utc)
                    if len(start_date) == 10:
                        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    date_filter["$gte"] = start_dt.isoformat()
                if end_date:
                    end_dt = datetime.fromisoformat(end_date)
                    if end_dt.tzinfo is None:
                        end_dt = end_dt.replace(tzinfo=timezone.utc)
                    if len(end_date) == 10:
                        end_dt = end_dt.replace(hour=23, minute=59, second=59, microsecond=0)
                    date_filter["$lte"] = end_dt.isoformat()
            except ValueError:
                date_filter = {}
            if date_filter:
                query["created_at"] = date_filter

        if filters.get("search"):
            safe_search = re.escape(filters["search"])
            query["$or"] = [
                {"applicant_name": {"$regex": safe_search, "$options": "i"}},
                {"applicant_company_name": {"$regex": safe_search, "$options": "i"}},
                {"applicant_email": {"$regex": safe_search, "$options": "i"}},
            ]

        safe_page = max(filters.get("page", 1), 1)
        safe_limit = min(max(filters.get("limit", 25), 1), 200)
        skip = (safe_page - 1) * safe_limit

        total_count = await self.db.support_applications.count_documents(query)
        docs = (
            await self.db.support_applications.find(query, {"_id": 0})
            .sort("created_at", -1)
            .skip(skip)
            .limit(safe_limit)
            .to_list(length=safe_limit)
        )

        items = []
        for doc in docs:
            items.append(
                {
                    "id": doc.get("id"),
                    "application_id": doc.get("application_id"),
                    "application_type": doc.get("application_type"),
                    "category": doc.get("category"),
                    "subject": doc.get("subject"),
                    "description": doc.get("description"),
                    "status": doc.get("status"),
                    "priority": doc.get("priority"),
                    "decision_reason": doc.get("decision_reason"),
                    "created_at": doc.get("created_at"),
                    "updated_at": doc.get("updated_at"),
                    "user": {
                        "id": doc.get("user_id"),
                        "name": doc.get("applicant_company_name") or doc.get("applicant_name") or "-",
                        "email": doc.get("applicant_email") or "-",
                        "country": doc.get("applicant_country") or "-",
                    },
                    "assigned_to": doc.get("assigned_to"),
                }
            )

        total_pages = max(1, (total_count + safe_limit - 1) // safe_limit)
        return {
            "items": items,
            "total_count": total_count,
            "page": safe_page,
            "limit": safe_limit,
            "total_pages": total_pages,
        }

    async def assign_application(self, application_id: str, assigned_to: Optional[str]) -> Dict[str, Any]:
        await self.db.support_applications.update_one(
            {"id": application_id},
            {"$set": {"assigned_to": assigned_to, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        return {"ok": True}

    async def update_status(self, application_id: str, status: str, decision_reason: Optional[str]) -> Dict[str, Any]:
        await self.db.support_applications.update_one(
            {"id": application_id},
            {"$set": {"status": status, "decision_reason": decision_reason, "updated_at": datetime.now(timezone.utc).isoformat()}},
        )
        return {"ok": True, "status": status}
