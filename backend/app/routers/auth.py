import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.dependencies import get_db, get_current_user, _resolve_portal_scope
from app.core.security import (
    verify_password, get_password_hash, create_access_token, 
    create_refresh_token, decode_token
)
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserResponse, UserLogin, TokenResponse, RefreshTokenRequest
)
from app.services.audit import log_action

router = APIRouter(prefix="/auth", tags=["Authentication"])
TOKEN_VERSION = os.environ.get("TOKEN_VERSION", "v2")

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
        country_scope=user_data.country_scope,
        preferred_language=user_data.preferred_language
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    await log_action(
        db=db, 
        action="CREATE", 
        resource_type="user", 
        resource_id=str(user.id),
        new_values={"email": user.email, "role": user.role}
    )
    
    return user

@router.post("/login", response_model=TokenResponse)
async def login(credentials: UserLogin, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == credentials.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    await db.commit()
    
    # Create tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "portal_scope": _resolve_portal_scope(user.role),
        "token_version": TOKEN_VERSION,
    }
    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)
    
    await log_action(
        db=db,
        action="LOGIN",
        resource_type="user",
        resource_id=str(user.id),
        user_id=user.id,
        user_email=user.email,
        ip_address=request.client.host if request.client else None
    )
    
    user_payload = UserResponse.model_validate(user).model_copy(update={"portal_scope": _resolve_portal_scope(user.role)})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=user_payload
    )

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = decode_token(data.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    if payload.get("token_version") != TOKEN_VERSION:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "portal_scope": _resolve_portal_scope(user.role),
        "token_version": TOKEN_VERSION,
    }
    new_access_token = create_access_token(token_data)
    new_refresh_token = create_refresh_token(token_data)
    
    user_payload = UserResponse.model_validate(user).model_copy(update={"portal_scope": _resolve_portal_scope(user.role)})

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        user=user_payload
    )

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    # In a more complete implementation, we'd invalidate the token
    return {"message": "Successfully logged out"}
