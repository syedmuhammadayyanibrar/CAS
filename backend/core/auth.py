import hashlib
import hmac
import os
import re
import secrets
import time
import uuid
from collections import defaultdict, deque
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List, Deque

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.core.config import settings
from backend.core.logging import get_logger

logger = get_logger("CASAuth")

ph = PasswordHasher()
security_scheme = HTTPBearer(auto_error=False)

ROLE_ADMIN = "admin"
ROLE_REVIEWER = "reviewer"
ROLE_GUEST = "guest"
VALID_ROLES = {ROLE_ADMIN, ROLE_REVIEWER, ROLE_GUEST}

_DEFAULT_JWT_SECRET = "cas-super-secret-jwt-key-change-in-production-2026"


def _is_production_like() -> bool:
    return settings.ENVIRONMENT.lower() == "production" or bool(os.getenv("VERCEL"))


def _resolve_jwt_secret() -> str:
    """
    Returns the signing key. In serverless/multi-worker deployments (e.g. Vercel),
    every worker MUST derive the exact same signing key so tokens issued by one
    worker are accepted by all other workers.
    """
    secret = settings.JWT_SECRET
    if secret == _DEFAULT_JWT_SECRET and _is_production_like():
        seed = f"{secret}:{settings.FASTN_ORG_ID}:{settings.GOOGLE_CLIENT_ID}:{os.getenv('VERCEL_PROJECT_ID', 'cas-vercel')}"
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return secret


JWT_SIGNING_KEY = _resolve_jwt_secret()


# ---------------------------------------------------------------------------
# Passwords & token primitives
# ---------------------------------------------------------------------------

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


def _encode(payload: Dict[str, Any]) -> str:
    return jwt.encode(payload, JWT_SIGNING_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(
    user_id: str,
    email: str,
    role: str,
    full_name: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Creates a signed JWT access token."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES))
    return _encode({
        "sub": user_id,
        "email": email,
        "role": role,
        "name": full_name or email.split("@")[0],
        "jti": str(uuid.uuid4()),
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "exp": expire,
        "iat": now,
    })


def create_guest_token() -> str:
    """Creates a short-lived access token with role 'guest'."""
    guest_id = f"guest-{uuid.uuid4().hex[:8]}"
    now = datetime.now(timezone.utc)
    return _encode({
        "sub": guest_id,
        "email": f"{guest_id}@cas.local",
        "role": ROLE_GUEST,
        "name": "Guest Reviewer",
        "jti": str(uuid.uuid4()),
        "type": "access",
        "iss": settings.JWT_ISSUER,
        "exp": now + timedelta(minutes=settings.JWT_GUEST_TOKEN_EXPIRE_MINUTES),
        "iat": now,
    })


def create_refresh_token(
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    role: Optional[str] = None,
    full_name: Optional[str] = None,
    family_id: Optional[str] = None,
    expire_days: Optional[int] = None,
    remember_me: bool = False,
) -> str:
    """
    Generates a cryptographically signed refresh token (JWT with type='refresh')
    when user context is provided, or an opaque token otherwise. Using a signed
    refresh token allows serverless workers (with ephemeral per-worker SQLite)
    to validate and rotate sessions across cold starts while still recording
    token hashes in RefreshTokenModel for reuse/revocation checks.
    """
    if not user_id or not email:
        return secrets.token_urlsafe(48)
    now = datetime.now(timezone.utc)
    days = expire_days if expire_days is not None else (
        settings.JWT_REMEMBER_ME_DAYS if remember_me else settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    return _encode({
        "sub": user_id,
        "email": email,
        "role": role or ROLE_REVIEWER,
        "name": full_name or email.split("@")[0],
        "fam": family_id or uuid.uuid4().hex,
        "rem": bool(remember_me),
        "jti": str(uuid.uuid4()),
        "type": "refresh",
        "iss": settings.JWT_ISSUER,
        "exp": now + timedelta(days=days),
        "iat": now,
    })


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodes and validates a signed refresh JWT, returning None if invalid/expired."""
    try:
        payload = jwt.decode(
            token,
            JWT_SIGNING_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "iss"]},
        )
        if payload.get("type") != "refresh":
            return None
        return payload
    except jwt.PyJWTError:
        return None


def encode_signed_state(data: Dict[str, Any], expire_seconds: int = 7200) -> str:
    """Signs a state dictionary (e.g. serverless OTP/account state) with JWT_SIGNING_KEY."""
    now = datetime.now(timezone.utc)
    payload = {
        **data,
        "iss": settings.JWT_ISSUER,
        "iat": now,
        "exp": now + timedelta(seconds=expire_seconds),
    }
    return _encode(payload)


def decode_signed_state(token: Optional[str], expected_type: str) -> Optional[Dict[str, Any]]:
    """Verifies and decodes a signed state token."""
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            JWT_SIGNING_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            options={"require": ["exp", "iat", "iss"]},
        )
        if payload.get("type") != expected_type:
            return None
        return payload
    except jwt.PyJWTError:
        return None


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and strictly validates a JWT access token: signature, pinned
    algorithm, issuer, mandatory claims, token type and a known role.
    """
    unauthorized = lambda detail: HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token,
            JWT_SIGNING_KEY,
            algorithms=[settings.JWT_ALGORITHM],
            issuer=settings.JWT_ISSUER,
            options={"require": ["exp", "iat", "sub", "iss"]},
        )
    except jwt.ExpiredSignatureError:
        raise unauthorized("Token expired")
    except jwt.PyJWTError:
        raise unauthorized("Invalid authentication token")

    if payload.get("type") != "access":
        raise unauthorized("Invalid token type")
    if payload.get("role") not in VALID_ROLES:
        raise unauthorized("Invalid token role")
    return payload


# ---------------------------------------------------------------------------
# Authentication dependencies
# ---------------------------------------------------------------------------

async def get_current_user_payload(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Dict[str, Any]:
    """Authentication: extracts and validates the JWT from the Bearer header."""
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
    """Returns the JWT payload if a valid token is present, otherwise None."""
    if not credentials or not credentials.credentials:
        return None
    try:
        return decode_access_token(credentials.credentials)
    except HTTPException:
        return None


def require_roles(allowed_roles: List[str]):
    """Role-based access control dependency factory for individual routes."""
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
    """Guests are read-only and cannot perform this action."""
    if payload.get("role") == ROLE_GUEST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Guest mode is read-only. Please create an account or sign in to perform this action.",
        )
    return payload


# ---------------------------------------------------------------------------
# Authorization: one central, default-deny RBAC policy
# ---------------------------------------------------------------------------

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# Operations restricted to administrators (expensive benchmark runs).
_ADMIN_ONLY_RULES = [
    ("POST", re.compile(r"^/evaluation/run")),
]

# What a guest may do: explore dashboard, evaluation, demo, upload/inspect/analyze
# contracts, while governance actions (signing, HITL review resolution, audit logs,
# organizational memory, outbound automations, and benchmark runs) require an account.
_GUEST_READ_PREFIXES = (
    "/dashboard",
    "/evaluation",
    "/demo",
    "/contracts",
    "/automations/google-drive/files",
)
_GUEST_WRITE_RULES = [
    ("POST", re.compile(r"^/demo/")),
    ("POST", re.compile(r"^/contracts/?$")),
    ("POST", re.compile(r"^/contracts/(upload-document|extract-text)$")),
    ("POST", re.compile(r"^/contracts/[^/]+/(analyze|ask)$")),
    ("POST", re.compile(r"^/automations/google-drive/import$")),
]


def normalize_path(path: str) -> str:
    """Strips the optional /api mount prefix so one policy covers both mounts."""
    if path == "/api":
        return "/"
    if path.startswith("/api/"):
        return path[4:]
    return path


def is_allowed(method: str, path: str, role: Optional[str]) -> bool:
    """Pure authorization decision for (method, path, role)."""
    if role not in VALID_ROLES:
        return False
    method = method.upper()
    path = normalize_path(path)

    for rule_method, pattern in _ADMIN_ONLY_RULES:
        if method == rule_method and pattern.match(path):
            return role == ROLE_ADMIN

    if role in (ROLE_ADMIN, ROLE_REVIEWER):
        return True

    # Guest
    if method in SAFE_METHODS:
        return path.startswith(_GUEST_READ_PREFIXES)
    return any(method == m and p.match(path) for m, p in _GUEST_WRITE_RULES)


async def authorize(
    request: Request,
    payload: Dict[str, Any] = Depends(get_current_user_payload),
) -> Dict[str, Any]:
    """
    Router-level dependency: authenticates the caller (401) and then enforces
    the central RBAC policy (403). Applied to every protected router.
    """
    if not is_allowed(request.method, request.url.path, payload.get("role")):
        logger.warning(
            f"Authorization denied: {payload.get('email')} ({payload.get('role')}) "
            f"{request.method} {request.url.path}"
        )
        if payload.get("role") == ROLE_GUEST:
            detail = "Guest mode is read-only for this area. Please create an account or sign in."
        else:
            detail = "You do not have permission to perform this action."
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
    request.state.user = payload
    return payload


def resolve_signup_role(email: str, any_user_exists: bool) -> str:
    """
    Admins are designated explicitly via ADMIN_EMAILS. Handing out admin to
    whoever registers first is only allowed in local development, never on a
    public (production-like) deployment.
    """
    admin_emails = {e.strip().lower() for e in settings.ADMIN_EMAILS.split(",") if e.strip()}
    if email.strip().lower() in admin_emails:
        return ROLE_ADMIN
    if not admin_emails and not any_user_exists and not _is_production_like():
        return ROLE_ADMIN
    return ROLE_REVIEWER


# ---------------------------------------------------------------------------
# Inbound webhook authentication (machine-to-machine, no user JWT)
# ---------------------------------------------------------------------------

def compute_webhook_signature(secret: str, body: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


async def verify_webhook_signature(request: Request) -> None:
    """
    Verifies the HMAC-SHA256 signature (X-Fastn-Signature) of inbound Fastn
    webhooks when FASTN_WEBHOOK_SECRET is configured.
    """
    secret = settings.FASTN_WEBHOOK_SECRET
    if not secret:
        if _is_production_like():
            logger.warning("FASTN_WEBHOOK_SECRET is not set: inbound webhooks are unauthenticated.")
        return
    provided = request.headers.get("X-Fastn-Signature", "").removeprefix("sha256=")
    expected = compute_webhook_signature(secret, await request.body())
    if not provided or not hmac.compare_digest(provided, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature")


# ---------------------------------------------------------------------------
# Rate limiting (sliding window, per process)
# ---------------------------------------------------------------------------

_rate_buckets: Dict[str, Deque[float]] = defaultdict(deque)


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(key: str, limit: int, window_seconds: int) -> None:
    """Raises 429 when `key` exceeds `limit` hits within `window_seconds`."""
    now = time.monotonic()
    bucket = _rate_buckets[key]
    while bucket and now - bucket[0] > window_seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        retry_after = max(1, int(window_seconds - (now - bucket[0])))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Please try again later.",
            headers={"Retry-After": str(retry_after)},
        )
    bucket.append(now)


def reset_rate_limits() -> None:
    _rate_buckets.clear()
