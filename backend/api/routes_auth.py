import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple

from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token as google_id_token
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select, update, delete
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
from backend.database.schema import UserModel, RefreshTokenModel, EmailOTPModel
from backend.core.email_service import send_otp_email, send_verification_email

logger = get_logger("AuthAPI")
router = APIRouter(prefix="/auth", tags=["Authentication"])

REFRESH_COOKIE_NAME = "cas_refresh_token"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: Optional[str] = Field(None, max_length=100)
    remember_me: bool = False


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = False


class RequestOTPRequest(BaseModel):
    email: EmailStr
    purpose: str = Field(default="login", pattern="^(login|register|verification)$")


class VerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=4, max_length=12)
    remember_me: bool = False


class GoogleAuthRequest(BaseModel):
    credential: str = Field(..., min_length=20)  # Google-signed ID token (JWT)


class VerifyEmailRequest(BaseModel):
    token: str
    email: Optional[EmailStr] = None


class OTPDispatchResponse(BaseModel):
    message: str
    email: str
    otp_expires_in_seconds: int
    resend_wait_seconds: int
    resend_count: int


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]
    requires_verification: Optional[bool] = False
    otp_expires_in_seconds: Optional[int] = None
    resend_wait_seconds: Optional[int] = None
    session_expires_in_seconds: int = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _compute_progressive_cooldown(resend_count: int) -> int:
    """
    Computes progressive resend wait time for multiple OTP requests on the same account:
      - 1st request: 120s (2 minutes)
      - 2nd request: 240s (4 minutes)
      - 3rd request: 480s (8 minutes)
      - 4th request: 960s (16 minutes)
      - 5th request: 1920s (32 minutes)
      - 6th request: 3840s (64 minutes)
      - 7th+ request: capped at 7200s (2 hours max)
    """
    exponent = max(0, resend_count - 1)
    cooldown = settings.OTP_INITIAL_COOLDOWN_SECONDS * (2 ** exponent)
    return min(cooldown, settings.OTP_MAX_COOLDOWN_SECONDS)


async def _issue_account_otp(
    db: AsyncSession,
    email: str,
    full_name: Optional[str],
    purpose: str = "verification",
) -> Tuple[str, int, int, int]:
    """
    Generates a 6-digit OTP with 5-minute validity, enforces the 2-minute initial wait
    and progressive exponential backoff (capped at 2 hours) for repeated requests on
    the same account, persists the hashed OTP, and dispatches it via Resend.
    """
    norm_email = email.strip().lower()
    now_utc = datetime.now(timezone.utc)

    stmt = select(EmailOTPModel).where(EmailOTPModel.email == norm_email)
    otp_rec = (await db.execute(stmt)).scalars().first()

    if otp_rec is not None:
        avail_at = _as_utc(otp_rec.resend_available_at)
        if now_utc < avail_at:
            wait_seconds = max(1, int((avail_at - now_utc).total_seconds() + 0.999))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {wait_seconds} seconds before requesting another OTP code.",
                headers={"Retry-After": str(wait_seconds)},
            )
        # Reset counter if previous OTP record was from more than 24 hours ago
        last_updated = _as_utc(otp_rec.updated_at) if otp_rec.updated_at else now_utc
        if (now_utc - last_updated).total_seconds() > 86400:
            resend_count = 1
        else:
            resend_count = (otp_rec.resend_count or 1) + 1
    else:
        resend_count = 1

    cooldown_seconds = _compute_progressive_cooldown(resend_count)
    expire_seconds = settings.OTP_EXPIRE_SECONDS  # 300s = 5 minutes
    otp_code = f"{secrets.randbelow(900000) + 100000:06d}"
    otp_hashed = hash_token(otp_code)

    expires_at = now_utc + timedelta(seconds=expire_seconds)
    resend_available_at = now_utc + timedelta(seconds=cooldown_seconds)

    if otp_rec is None:
        otp_rec = EmailOTPModel(
            email=norm_email,
            otp_hash=otp_hashed,
            purpose=purpose,
            expires_at=expires_at,
            resend_available_at=resend_available_at,
            resend_count=resend_count,
            failed_attempts=0,
            updated_at=now_utc,
        )
        db.add(otp_rec)
    else:
        otp_rec.otp_hash = otp_hashed
        otp_rec.purpose = purpose
        otp_rec.expires_at = expires_at
        otp_rec.resend_available_at = resend_available_at
        otp_rec.resend_count = resend_count
        otp_rec.failed_attempts = 0
        otp_rec.updated_at = now_utc

    send_otp_email(
        to_email=norm_email,
        otp_code=otp_code,
        full_name=full_name,
        purpose=purpose,
        valid_minutes=max(1, expire_seconds // 60),
    )

    return otp_code, expire_seconds, cooldown_seconds, resend_count


def _set_refresh_cookie(response: Response, token: str, expire_days: Optional[int] = None):
    days = expire_days if expire_days is not None else settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    max_age = days * 24 * 60 * 60
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


def _issue_session_tokens(
    db: AsyncSession,
    response: Response,
    user: UserModel,
    remember_me: bool = False,
    family_id: Optional[str] = None,
) -> str:
    """Issues a short-lived signed JWT access token and a rotating HttpOnly refresh cookie."""
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
        full_name=user.full_name,
    )
    expire_days = (
        settings.JWT_REMEMBER_ME_DAYS
        if remember_me
        else settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    raw_refresh = create_refresh_token()
    refresh_rec = RefreshTokenModel(
        token_hash=hash_token(raw_refresh),
        user_id=user.id,
        family_id=family_id or uuid.uuid4().hex,
        is_revoked=False,
        expires_at=datetime.now(timezone.utc) + timedelta(days=expire_days),
    )
    db.add(refresh_rec)
    _set_refresh_cookie(response, raw_refresh, expire_days=expire_days)
    return access_token


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Registers a new user, sends a 6-digit OTP via Resend (valid 5 minutes, 2-minute initial
    resend cooldown), and returns the initial session + verification metadata.
    """
    rate_limit(f"register:{client_ip(request)}", limit=10, window_seconds=3600)
    await ensure_db_initialized()
    norm_email = data.email.strip().lower()

    stmt = select(UserModel).where(UserModel.email == norm_email)
    existing = (await db.execute(stmt)).scalars().first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        )

    count_stmt = select(UserModel.id)
    any_user = (await db.execute(count_stmt)).scalars().first()
    role = resolve_signup_role(norm_email, bool(any_user))

    user_id = f"usr_{uuid.uuid4().hex[:12]}"
    new_user = UserModel(
        id=user_id,
        email=norm_email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name or norm_email.split("@")[0],
        role=role,
        is_active=True,
        is_verified=False,
        verification_token=None,
    )
    db.add(new_user)

    otp_code, expire_seconds, cooldown_seconds, _ = await _issue_account_otp(
        db=db,
        email=new_user.email,
        full_name=new_user.full_name,
        purpose="register",
    )
    new_user.verification_token = otp_code

    access_token = _issue_session_tokens(
        db=db,
        response=response,
        user=new_user,
        remember_me=data.remember_me,
    )
    await db.commit()

    logger.info(f"User registered & OTP dispatched: {new_user.email} (Role: {new_user.role})")

    return AuthResponse(
        access_token=access_token,
        requires_verification=True,
        otp_expires_in_seconds=expire_seconds,
        resend_wait_seconds=cooldown_seconds,
        user={
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.full_name,
            "role": new_user.role,
            "is_verified": False,
        },
    )


@router.post("/request-otp", response_model=OTPDispatchResponse)
async def request_otp(
    data: RequestOTPRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Sends or resends a 6-digit OTP via Resend for email login or account verification.
    Enforces a 2-minute initial wait and progressive exponential backoff (4m, 8m, 16m, 32m,
    64m, up to a 2-hour maximum) for repeated requests on the same account.
    """
    rate_limit(f"otp-ip:{client_ip(request)}", limit=25, window_seconds=3600)
    await ensure_db_initialized()
    norm_email = data.email.strip().lower()

    stmt = select(UserModel).where(UserModel.email == norm_email)
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No account found with this email address. Please register first.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support.",
        )

    otp_code, expire_seconds, cooldown_seconds, resend_count = await _issue_account_otp(
        db=db,
        email=user.email,
        full_name=user.full_name,
        purpose=data.purpose,
    )
    user.verification_token = otp_code
    await db.commit()

    return OTPDispatchResponse(
        message="A 6-digit verification code has been sent to your email.",
        email=user.email,
        otp_expires_in_seconds=expire_seconds,
        resend_wait_seconds=cooldown_seconds,
        resend_count=resend_count,
    )


@router.post("/verify-otp", response_model=AuthResponse)
async def verify_otp(
    data: VerifyOTPRequest,
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """
    Verifies a 6-digit OTP code (valid for 5 minutes) for account verification or
    passwordless email login, resets progressive OTP counters, and issues a live session.
    """
    rate_limit(f"verify-otp-ip:{client_ip(request)}", limit=30, window_seconds=900)
    await ensure_db_initialized()
    norm_email = data.email.strip().lower()
    clean_otp = data.otp.strip()

    user_stmt = select(UserModel).where(UserModel.email == norm_email)
    user = (await db.execute(user_stmt)).scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or verification code.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Please contact support.",
        )

    otp_stmt = select(EmailOTPModel).where(EmailOTPModel.email == norm_email)
    otp_rec = (await db.execute(otp_stmt)).scalars().first()
    if not otp_rec:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification code found. Please request a new OTP.",
        )

    now_utc = datetime.now(timezone.utc)
    if now_utc > _as_utc(otp_rec.expires_at):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired (valid for 5 minutes). Please request a new OTP.",
        )

    if otp_rec.failed_attempts >= settings.OTP_MAX_FAILED_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many incorrect attempts for this code. Please request a new OTP.",
        )

    if not secrets.compare_digest(hash_token(clean_otp), otp_rec.otp_hash):
        otp_rec.failed_attempts += 1
        await db.commit()
        remaining = max(0, settings.OTP_MAX_FAILED_ATTEMPTS - otp_rec.failed_attempts)
        if remaining == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many incorrect attempts. This OTP has been invalidated; please request a new code.",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid verification code. {remaining} attempt(s) remaining.",
        )

    # OTP verified: mark user verified and clear OTP state
    user.is_verified = True
    user.verification_token = None
    await db.delete(otp_rec)

    access_token = _issue_session_tokens(
        db=db,
        response=response,
        user=user,
        remember_me=data.remember_me,
    )
    await db.commit()
    logger.info(f"OTP verified and session issued for {user.email}")

    return AuthResponse(
        access_token=access_token,
        requires_verification=False,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role,
            "is_verified": True,
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

    access_token = _issue_session_tokens(
        db=db,
        response=response,
        user=user,
        remember_me=data.remember_me,
    )
    await db.commit()
    logger.info(f"User login successful: {user.email} (remember_me={data.remember_me})")

    return AuthResponse(
        access_token=access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role,
            "is_verified": bool(user.is_verified),
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

    now_utc = datetime.now(timezone.utc)
    rec_expires = _as_utc(token_record.expires_at)
    if rec_expires < now_utc:
        token_record.is_revoked = True
        await db.commit()
        _clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )

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

    # Preserve remember_me duration if original token had > 8 days lifespan
    rec_created = _as_utc(token_record.created_at) if token_record.created_at else now_utc
    was_remember_me = (rec_expires - rec_created).days > settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS + 1

    token_record.is_revoked = True
    new_access_token = _issue_session_tokens(
        db=db,
        response=response,
        user=user,
        remember_me=was_remember_me,
        family_id=token_record.family_id,
    )
    await db.commit()

    return AuthResponse(
        access_token=new_access_token,
        user={
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role,
            "is_verified": bool(user.is_verified),
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
    """Verifies a user's email address given the OTP or confirmation token."""
    await ensure_db_initialized()
    stmt = select(UserModel).where(UserModel.verification_token == data.token.strip())
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired email verification code.",
        )

    # Also check OTP expiry if an EmailOTPModel exists for this user
    otp_stmt = select(EmailOTPModel).where(EmailOTPModel.email == user.email)
    otp_rec = (await db.execute(otp_stmt)).scalars().first()
    if otp_rec:
        if datetime.now(timezone.utc) > _as_utc(otp_rec.expires_at):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code has expired (valid for 5 minutes). Please request a new OTP.",
            )
        await db.delete(otp_rec)

    user.is_verified = True
    user.verification_token = None
    await db.commit()
    logger.info(f"User email confirmed: {user.email}")
    return {"message": "Email address verified successfully. You may now access all features.", "verified": True}


@router.post("/resend-verification")
async def resend_verification(email: EmailStr, request: Request, db: AsyncSession = Depends(get_db)):
    """Re-sends a 6-digit verification OTP with progressive cooldown enforcement."""
    rate_limit(f"resend:{client_ip(request)}", limit=20, window_seconds=3600)
    await ensure_db_initialized()
    norm_email = email.strip().lower()
    stmt = select(UserModel).where(UserModel.email == norm_email)
    user = (await db.execute(stmt)).scalars().first()
    if not user:
        return {"message": "If an account exists with this email, a verification code has been sent."}
    if user.is_verified:
        return {"message": "Account is already verified."}

    otp_code, expire_seconds, cooldown_seconds, resend_count = await _issue_account_otp(
        db=db,
        email=user.email,
        full_name=user.full_name,
        purpose="register",
    )
    user.verification_token = otp_code
    await db.commit()
    return {
        "message": "Verification OTP sent. Please check your inbox.",
        "otp_expires_in_seconds": expire_seconds,
        "resend_wait_seconds": cooldown_seconds,
        "resend_count": resend_count,
    }


@router.get("/config")
async def auth_public_config():
    """Public client configuration (Google OAuth client ID and OTP timing rules)."""
    return {
        "google_client_id": settings.GOOGLE_CLIENT_ID,
        "otp_expire_seconds": settings.OTP_EXPIRE_SECONDS,
        "otp_initial_cooldown_seconds": settings.OTP_INITIAL_COOLDOWN_SECONDS,
        "otp_max_cooldown_seconds": settings.OTP_MAX_COOLDOWN_SECONDS,
    }


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
            is_verified=True,
        )
        db.add(user)
    else:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact support.",
            )
        user.is_verified = True

    access_token = _issue_session_tokens(
        db=db,
        response=response,
        user=user,
        remember_me=True,
    )
    await db.commit()
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


@router.api_route("/google/callback", methods=["GET", "POST"])
async def google_auth_callback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Handles Google OAuth redirect callback (/auth/google/callback and /api/auth/google/callback).
    Supports Google Identity Services POST form credential or query credential, sets the
    HttpOnly refresh cookie, and redirects the browser to the application root.
    """
    from fastapi.responses import RedirectResponse

    credential = request.query_params.get("credential") or request.query_params.get("id_token")
    if not credential and request.method == "POST":
        try:
            form = await request.form()
            credential = form.get("credential") or form.get("id_token")
        except Exception:
            pass

    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    if credential:
        await google_auth(
            data=GoogleAuthRequest(credential=str(credential)),
            request=request,
            response=redirect,
            db=db,
        )
    return redirect
