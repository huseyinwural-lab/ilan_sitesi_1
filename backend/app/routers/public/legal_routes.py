from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import List

from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.legal import LegalConsent

router = APIRouter()

class ConsentRequest(BaseModel):
    country_code: str
    document_type: str
    version: str

@router.post("/consent")
async def accept_consent(
    data: ConsentRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Log user acceptance of legal documents.
    """
    consent = LegalConsent(
        user_id=current_user.id,
        country_code=data.country_code.upper(),
        document_type=data.document_type,
        version=data.version,
        ip_address=request.client.host,
        user_agent=request.headers.get("user-agent")
    )
    db.add(consent)
    await db.commit()
    return {"status": "accepted"}
