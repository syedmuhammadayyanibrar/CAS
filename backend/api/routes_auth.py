import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.logging import get_logger
from backend.core.auth import (
    hash_password,
    verify_password,
    hash_token,
    create_access_token,
    create_guest_token,
    create_refresh_token,
    get_current_user_payload,
)
from backend.database.db import get_db, ensure_db_initialized
from backend.database.schema import UserModel, RefreshTokenModel

logger = get_logger("AuthAPI")
router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE_NAME = "cas_refresh_token"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]


def _set_refresh_cookie(response: Response, token: str):
    max_age = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=max_age,
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response):
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/auth",
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Registers a new user and returns access token + sets rotating refresh cookie."""
    await ensure_db_initialized()
    norm_email = data.email.strip().lower()

    # Check existing user
    stmt = select(UserModel).where(UserModel.email == norm_email)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    # First registered user is automatically admin, others are reviewers
    count_stmt = select(UserModel.id)
    any_user = (await db.execute(count_stmt)).scalars().first()
    role = "admin" if not any_user else "reviewer"

    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    new_user = UserModel(
        id=user_id,
        email=norm_email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name or norm_email.split("@")[0],
        role=role,
        is_active=True,
    )
    db.add(new_user)

    # Issue tokens
    access_token = create_access_token(
        user_id=new_user.id,
        email=new_user.email,
        role=new_user.role,
        full_name=new_user.full_name,
    )
    raw_refresh = create_refresh_token()
    family_id = uuid.uuid4().hex
    refresh_rec = RefreshTokenModel(
        token_hash=hash_token(raw_refresh),
        user_id=new_user.id,
        family_id=family_id,
        is_revoked=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_rec)
    await db.commit()

    _set_refresh_cookie(response, raw_refresh)
    logger.info(f"User registered successfully: {new_user.email} (Role: {new_user.role})")

    return AuthResponse(
        access_token=access_token,
        user={
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.full_name,
            "role": new_user.role,
        },
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticates credentials, returns access token, sets rotating refresh cookie."""
    await ensure_db_initialized()
    norm_email = data.email.strip().lower()

    stmt = select(UserModel).where(UserModel.email == norm_email)
    user = (await db.execute(stmt)).scalars().first()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support.",
        )

    # Issue tokens
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
    )
    raw_refresh = create_refresh_token()
    family_id = uuid.uuid4().hex
    refresh_rec = RefreshTokenModel(
        token_hash=hash_token(raw_refresh),
        user_id=user.id,
        family_id=family_id,
        is_revoked=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh_rec)
    await db.commit()

    _set_refresh_cookie(response, raw_refresh)
    logger.info(f"User login successful: {user.email}")

    return AuthResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role,
        },
    )


@router.post("/guest", response_model=AuthResponse)
async def guest_login():
    """Issues an unauthenticated temporary guest session (read-only exploration)."""
    guest_token = create_guest_token()
    return AuthResponse(
        access_token=guest_token,
        user={
            "id": "guest",
            "email": "guest@cas.local",
            "name": "Guest Reviewer",
            "role": "guest",
        },
    )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token_endpoint(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Exchanges an active refresh token cookie for a new access token and
    a rotated refresh token. Detects token reuse to revoke compromised sessions.
    """
    await ensure_db_initialized()
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not raw_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found",
        )

    hashed = hash_token(raw_token)
    stmt = select(RefreshTokenModel).where(RefreshTokenModel.token_hash == hashed)
    token_record = (await db.execute(stmt)).scalars().first()

    if not token_record:
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # Reuse detection: if token is already revoked, revoke its entire family!
    if token_record.is_revoked:
        await db.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.family_id == token_record.family_id)
            .values(is_revoked=True)
        )
        await db.commit()
        _clear_refresh_cookie(response)
        logger.warning(f"Detected reuse of revoked refresh token for user {token_record.user_id}! Revoked token family.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session security compromise detected. Please sign in again.",
        )

    # Check expiration
    now_utc = datetime.now(timezone.utc)
    if token_record.expires_at.replace(tzinfo=timezone.utc) < now_utc:
        token_record.is_revoked = True
        await db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

    # Fetch user
    user_stmt = select(UserModel).where(UserModel.id == token_record.user_id)
    user = (await db.execute(user_stmt)).scalars().first()
    if not user or not user.is_active:
        token_record.is_revoked = True
        await db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    # Rotate refresh token: revoke current, issue new with same family_id
    token_record.is_revoked = True

    new_raw_refresh = create_refresh_token()
    new_refresh_rec = RefreshTokenModel(
        token_hash=hash_token(new_raw_refresh),
        user_id=user.id,
        family_id=token_record.family_id,
        is_revoked=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(new_refresh_rec)

    new_access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
    )
    await db.commit()

    _set_refresh_cookie(response, new_raw_refresh)

    return AuthResponse(
        access_token=new_access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role,
        },
    )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Revokes active refresh token and clears cookie."""
    raw_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if raw_token:
        hashed = hash_token(raw_token)
        stmt = select(RefreshTokenModel).where(RefreshTokenModel.token_hash == hashed)
        token_record = (await db.execute(stmt)).scalars().first()
        if token_record:
            token_record.is_revoked = True
            await db.commit()

    _clear_refresh_cookie(response)
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user(payload: Dict[str, Any] = Depends(get_current_user_payload)):
    """Returns profile information for the authenticated token."""
    return {
        "id": payload.get("sub"),
        "email": payload.get("email"),
        "name": payload.get("name"),
        "role": payload.get("role"),
    }
