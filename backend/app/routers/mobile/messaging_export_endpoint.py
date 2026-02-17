@router.get("/export", response_model=List[dict])
async def export_messages(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    GDPR Compliant Message Export
    """
    # Fetch all messages sent or received
    # Optimized query: Join Conversation to check participation
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
