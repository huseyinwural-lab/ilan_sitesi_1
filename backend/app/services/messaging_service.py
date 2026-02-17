from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_, desc
from datetime import datetime, timezone, timedelta
from app.models.messaging import Conversation, Message
from app.models.moderation import Listing
from fastapi import HTTPException
import uuid

from app.services.counter_service import CounterService
from app.services.notification_service import NotificationService
from app.services.ai_chat_service import AIChatService

class MessagingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.counter_service = CounterService() 
        self.notification_service = NotificationService(db)
        self.ai_service = AIChatService()

    # ... get_or_create_conversation ...

    async def send_message(self, conversation_id: uuid.UUID, sender_id: uuid.UUID, body: str) -> Message:
        # 1. AI Safety Check (Pre-process)
        safety = self.ai_service.check_safety(body)
        if not safety["safe"]:
            raise HTTPException(status_code=400, detail=f"Message blocked: {safety['reason']}")

        # 2. Check Conversation
        conversation = await self.db.get(Conversation, conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
            
        if conversation.status == "blocked":
             raise HTTPException(status_code=403, detail="Conversation is blocked")
             
        # 3. Create Message
        msg = Message(
            conversation_id=conversation_id,
            sender_id=sender_id,
            body=body
        )
        self.db.add(msg)
        
        # 4. Update Timestamp
        conversation.last_message_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        
        # 5. Post-Process (Realtime & Notification)
        recipient_id = conversation.buyer_id if conversation.seller_id == sender_id else conversation.seller_id
        
        # Increment Unread Counter
        await self.counter_service.increment_unread(str(recipient_id))
        
        # Send Push
        await self.notification_service.send_push(
            user_id=recipient_id,
            title="Yeni Mesaj 💬",
            body=body[:50] + "..." if len(body) > 50 else body,
            data={
                "type": "chat", 
                "conversation_id": str(conversation_id),
                "suggestions": self.ai_service.generate_smart_replies(body) # Piggyback suggestions
            }
        )
        
        return msg

    async def get_inbox(self, user_id: uuid.UUID, limit: int = 20) -> list:
        # Join Listing to check premium status
        # Sort by: Highlighted DESC, Listing Premium DESC, Time DESC
        query = select(Conversation, Listing.is_premium).join(Listing, Conversation.listing_id == Listing.id).where(
            or_(Conversation.buyer_id == user_id, Conversation.seller_id == user_id)
        ).order_by(
            desc(Conversation.is_highlighted),
            desc(Listing.is_premium),
            desc(Conversation.last_message_at)
        ).limit(limit)
        
        result = await self.db.execute(query)
        # Result is (Conversation, is_premium) tuple
        return [row[0] for row in result.all()]
