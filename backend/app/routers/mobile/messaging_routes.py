from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
import uuid

from app.dependencies import get_db, get_current_user
from sqlalchemy import select, or_, and_, desc
from app.models.messaging import Conversation, Message
from app.services.counter_service import CounterService
from app.services.messaging_service import MessagingService
from app.models.user import User

router = APIRouter()

# DTOs
class MessageCreate(BaseModel):
    listing_id: Optional[str] = None
    conversation_id: Optional[str] = None
    body: str

class MessageResponse(BaseModel):
    id: str
    body: str
    sender_id: str
    created_at: str

class ConversationResponse(BaseModel):
    id: str
    last_message_at: str
    other_user_id: str # Simplified

# Endpoints
@router.post("/send", response_model=MessageResponse)
async def send_message(
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MessagingService(db)
    
    # 1. Resolve Conversation
    if data.conversation_id:
        conversation_id = uuid.UUID(data.conversation_id)
    elif data.listing_id:
        # Start new or get existing
        conv = await service.get_or_create_conversation(uuid.UUID(data.listing_id), current_user.id)
        conversation_id = conv.id
    else:
        raise HTTPException(status_code=400, detail="Missing conversation_id or listing_id")
        
    # 2. Send
    msg = await service.send_message(conversation_id, current_user.id, data.body)
    
    return {
        "id": str(msg.id),
        "body": msg.body,
        "sender_id": str(msg.sender_id),
        "created_at": msg.created_at.isoformat()
    }

@router.get("/inbox", response_model=List[ConversationResponse])
async def get_inbox(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MessagingService(db)
    convs = await service.get_inbox(current_user.id)

    res = []
    for c in convs:
        other = c.seller_id if c.buyer_id == current_user.id else c.buyer_id
        res.append({
            "id": str(c.id),
            "last_message_at": c.last_message_at.isoformat() if c.last_message_at else None,
            "other_user_id": str(other),
        })

    return res


@router.get("/unread-count")
async def get_unread_count(current_user: User = Depends(get_current_user)):
    counter = CounterService()
    count = await counter.get_unread_count(str(current_user.id))
    return {"count": count}

@router.get("/export", response_model=List[dict])
async def export_messages(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GDPR Compliant Message Export
    """
    # Fetch all messages sent or received
    query = select(Message).join(Conversation).where(
        or_(Conversation.buyer_id == current_user.id, Conversation.seller_id == current_user.id)
    ).order_by(Message.created_at)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    return [{
        "id": str(m.id),
        "sender_id": str(m.sender_id),
        "body": m.body,
        "created_at": m.created_at.isoformat()
    } for m in messages]


from app.services.ai_chat_service import AIChatService

@router.get("/suggestions")
async def get_suggestions(last_message: str):
    """
    Standalone endpoint to get smart replies
    """
    service = AIChatService()
    return {"suggestions": service.generate_smart_replies(last_message)}
