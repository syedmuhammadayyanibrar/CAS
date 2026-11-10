import os
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.database.db import get_db
from backend.database.schema import UserModel, RefreshTokenModel

ph = PasswordHasher()
security_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    """Hashes a password using Argon2id."""
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2id hash."""
    try:
        return ph.verify(hashed_password, plain_password)
    except (VerifyMismatchError, VerificationError):
        return False


def hash_token(token: str) -> str:
    """Creates a SHA-256 hash of a token for secure database storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    full_name: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed JWT access token."""
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "name": full_name or email.split("@")[0],
        "jti": str(uuid.uuid4()),
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_guest_token() -> str:
    """Creates a short-lived access token with role 'guest'."""
    guest_id = f"guest-{uuid.uuid4().hex[:8]}"
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.JWT_GUEST_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": guest_id,
        "email": f"{guest_id}@cas.local",
        "role": "guest",
        "name": "Guest Reviewer",
        "jti": str(uuid.uuid4()),
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token() -> str:
    """Generates an opaque cryptographically secure refresh token string."""
    return uuid.uuid4().hex + uuid.uuid4().hex


def decode_access_token(token: str) -> Dict[str, Any]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """Dependency that extracts and validates the JWT payload from Bearer token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return decode_access_token(credentials.credentials)


async def get_optional_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[Dict[str, Any]]:
    """Dependency that extracts JWT payload if present, or returns None."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return decode_access_token(credentials.credentials)
    except HTTPException:
        return None


def require_roles(allowed_roles: List[str]):
    """Role-based access control dependency factory."""
    async def role_checker(payload: Dict[str, Any] = Depends(get_current_user_payload)) -> Dict[str, Any]:
        user_role = payload.get("role")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Requires one of roles: {', '.join(allowed_roles)} (current: {user_role})",
            )
        return payload
    return role_checker


def forbid_guest(payload: Dict[str, Any] = Depends(get_current_user_payload)) -> Dict[str, Any]:
    """Enforces that guest users cannot perform mutating or sensitive operations."""
    if payload.get("role") == "guest":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest mode is read-only. Please create an account or sign in to perform this action.",
        )
    return payload
