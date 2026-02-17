from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, check_permissions
from app.services.risk_engine import RiskEngine
from app.models.user import User

router = APIRouter()

@router.get("/risk-score/{user_id}")
async def get_user_risk(
    user_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions(["super_admin", "moderator"]))
):
    engine = RiskEngine(db)
    score = await engine.calculate_risk_score(user_id)
    action = await engine.enforce_policy(user_id)
    
    return {
        "user_id": user_id,
        "risk_score": score,
        "recommended_action": action
    }
