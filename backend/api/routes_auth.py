import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

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
    rate_limit,
    client_ip,
    resolve_signup_role,
)
from backend.database.db import get_db, ensure_db_initialized
from backend.database.schema import UserModel, RefreshTokenModel

from backend.core.email_service import send_verification_email

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


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., min_length=20)  # Google-signed ID token (JWT)


class VerifyEmailRequest(BaseModel):
    token: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    requires_verification: Optional[bool] = False


def _set_refresh_cookie(response: Response, token: str):
    max_age = settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite=settings.COOKIE_SAMESITE,
        max_age=max_age,
        path="/",
    )


def _clear_refresh_cookie(response: Response):
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/",
    )


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Registers a new user and returns access token + sets rotating refresh cookie."""
    rate_limit(f"register:{client_ip(request)}", limit=5, window_seconds=3600)
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

    # Admins come from ADMIN_EMAILS; "first user is admin" is local-dev only
    count_stmt = select(UserModel.id)
    any_user = (await db.execute(count_stmt)).scalars().first()
    role = resolve_signup_role(norm_email, bool(any_user))

    # Generate email confirmation token
    verif_token = f"vtok_{uuid.uuid4().hex}"

    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    new_user = UserModel(
        id=user_id,
        email=norm_email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name or norm_email.split("@")[0],
        role=role,
        is_active=True,
        is_verified=False,
        verification_token=verif_token,
    )
    db.add(new_user)

    # Send verification email dispatch
    send_verification_email(new_user.email, verif_token, new_user.full_name)

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
    logger.info(f"User registered successfully: {new_user.email} (Role: {new_user.role}, Verification: Pending)")

    return AuthResponse(
        access_token=access_token,
        requires_verification=True,
        user={
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.full_name,
            "role": new_user.role,
            "is_verified": False,
        },
    )


@router.post("/login", response_model=AuthResponse)
async def login(
    data: LoginRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticates credentials, returns access token, sets rotating refresh cookie."""
    norm_email = data.email.strip().lower()
    # Brute-force protection: per (IP, account) and per account across IPs
    rate_limit(f"login:{client_ip(request)}:{norm_email}", limit=10, window_seconds=900)
    rate_limit(f"login-acct:{norm_email}", limit=30, window_seconds=900)
    await ensure_db_initialized()

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
async def guest_login(request: Request):
    """Issues an unauthenticated temporary guest session (read-only exploration)."""
    rate_limit(f"guest:{client_ip(request)}", limit=30, window_seconds=3600)
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


@router.post("/verify-email")
async def verify_email(data: VerifyEmailRequest, db: AsyncSession = Depends(get_db)):
    """Verifies a user's email address given the unique confirmation token."""
    await ensure_db_initialized()
    stmt = select(UserModel).where(UserModel.verification_token == data.token)
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired email confirmation link.",
        )
    user.is_verified = True
    user.verification_token = None
    await db.commit()
    logger.info(f"User email confirmed: {user.email}")
    return {"message": "Email address verified successfully. You may now access all features.", "verified": True}


@router.post("/resend-verification")
async def resend_verification(email: EmailStr, request: Request, db: AsyncSession = Depends(get_db)):
    """Re-sends an email confirmation link if the account is unverified."""
    rate_limit(f"resend:{client_ip(request)}", limit=5, window_seconds=3600)
    rate_limit(f"resend-acct:{email.strip().lower()}", limit=3, window_seconds=3600)
    await ensure_db_initialized()
    stmt = select(UserModel).where(UserModel.email == email.strip().lower())
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        return {"message": "If an account exists with this email, a verification link has been sent."}
    if user.is_verified:
        return {"message": "Account is already verified."}

    verif_token = f"vtok_{uuid.uuid4().hex}"
    user.verification_token = verif_token
    await db.commit()
    send_verification_email(user.email, verif_token, user.full_name)
    return {"message": "Verification email sent. Please check your inbox."}


@router.get("/config")
async def auth_public_config():
    """Public client configuration (the Google OAuth client ID is not a secret)."""
    return {"google_client_id": settings.GOOGLE_CLIENT_ID}


@router.post("/google", response_model=AuthResponse)
async def google_auth(
    data: GoogleAuthRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Signs in / signs up with a Google ID token. The token's signature, expiry,
    issuer and audience (our GOOGLE_CLIENT_ID) are verified cryptographically;
    nothing client-supplied other than the signed token is trusted.
    """
    rate_limit(f"google:{client_ip(request)}", limit=20, window_seconds=900)

    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Google sign-in is not configured on this server.",
        )

    try:
        info = await run_in_threadpool(
            google_id_token.verify_oauth2_token,
            data.credential,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google credential.",
        )

    target_email = (info.get("email") or "").strip().lower()
    if not target_email or not info.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google account email is not verified.",
        )
    target_name = info.get("name") or target_email.split("@")[0]

    await ensure_db_initialized()

    # Check if user exists
    stmt = select(UserModel).where(UserModel.email == target_email)
    user = (await db.execute(stmt)).scalars().first()

    if not user:
        any_user = (await db.execute(select(UserModel.id))).scalars().first()
        user = UserModel(
            id=f"usr_g_{uuid.uuid4().hex[:10]}",
            email=target_email,
            hashed_password=hash_password(secrets.token_urlsafe(32)),
            full_name=target_name,
            role=resolve_signup_role(target_email, bool(any_user)),
            is_active=True,
            is_verified=True,  # Google verified this email address
        )
        db.add(user)
    else:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact support.",
            )
        user.is_verified = True

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
    logger.info(f"Google authentication successful for user: {user.email}")

    return AuthResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role,
            "is_verified": True,
        },
    )
