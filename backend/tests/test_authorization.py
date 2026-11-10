import time

import jwt
import pytest
from httpx import AsyncClient, ASGITransport

from backend.api import routes_auth
from backend.core import auth as auth_module
from backend.core.auth import (
    ROLE_ADMIN,
    ROLE_GUEST,
    ROLE_REVIEWER,
    compute_webhook_signature,
    create_access_token,
    create_guest_token,
    decode_access_token,
    is_allowed,
    reset_rate_limits,
)
from backend.core.config import settings
from backend.main import app
from backend.tests.helpers import auth_headers
from fastapi import HTTPException


@pytest.fixture(autouse=True)
def _clean_rate_limits():
    reset_rate_limits()
    yield
    reset_rate_limits()


def client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------- authentication

PROTECTED_GETS = [
    "/dashboard/summary",
    "/contracts",
    "/evaluation/summary",
    "/reviews",
    "/audit",
    "/memory",
    "/automations",
    "/api/dashboard/summary",
    "/api/contracts",
]


@pytest.mark.asyncio
@pytest.mark.parametrize("path", PROTECTED_GETS)
async def test_protected_routes_reject_anonymous_requests(path):
    async with client() as ac:
        res = await ac.get(path)
    assert res.status_code == 401, path
    assert res.headers.get("www-authenticate") == "Bearer"


@pytest.mark.asyncio
async def test_protected_mutations_reject_anonymous_requests():
    async with client() as ac:
        for path in ("/contracts", "/mesh/analyze", "/evaluation/run", "/demo/reset"):
            res = await ac.post(path, json={})
            assert res.status_code == 401, path


def _forge(claims: dict, key: str = settings.JWT_SECRET, alg: str = "HS256") -> str:
    return jwt.encode(claims, key, algorithm=alg)


def _valid_claims(**overrides) -> dict:
    now = int(time.time())
    claims = {
        "sub": "u1", "email": "u1@example.com", "role": "admin", "type": "access",
        "iss": settings.JWT_ISSUER, "iat": now, "exp": now + 600, "jti": "x",
    }
    claims.update(overrides)
    return claims


@pytest.mark.asyncio
@pytest.mark.parametrize("name,token", [
    ("wrong signing key", _forge(_valid_claims(), key="not-the-real-secret-not-the-real-secret")),
    ("expired", _forge(_valid_claims(exp=int(time.time()) - 10), key=auth_module.JWT_SIGNING_KEY)),
    ("wrong issuer", _forge(_valid_claims(iss="someone-else"), key=auth_module.JWT_SIGNING_KEY)),
    ("missing issuer", _forge({k: v for k, v in _valid_claims().items() if k != "iss"}, key=auth_module.JWT_SIGNING_KEY)),
    ("refresh type", _forge(_valid_claims(type="refresh"), key=auth_module.JWT_SIGNING_KEY)),
    ("unknown role", _forge(_valid_claims(role="superuser"), key=auth_module.JWT_SIGNING_KEY)),
    ("alg none", jwt.encode(_valid_claims(), key=None, algorithm="none")),
    ("garbage", "not.a.jwt"),
])
async def test_invalid_tokens_are_rejected(name, token):
    async with client() as ac:
        res = await ac.get("/dashboard/summary", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 401, name


def test_access_token_claims_and_lifetime():
    payload = decode_access_token(create_access_token("u1", "u1@example.com", ROLE_REVIEWER))
    assert payload["iss"] == settings.JWT_ISSUER
    assert payload["type"] == "access"
    assert payload["exp"] - payload["iat"] == settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    assert settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES <= 15


# ---------------------------------------------------------------- authorization (RBAC)

@pytest.mark.parametrize("method,path,role,expected", [
    # admin & reviewer: everything except admin-only operations
    ("GET", "/contracts", ROLE_REVIEWER, True),
    ("POST", "/contracts", ROLE_REVIEWER, True),
    ("POST", "/reviews/1/resolve", ROLE_REVIEWER, True),
    ("POST", "/evaluation/run", ROLE_REVIEWER, False),
    ("POST", "/evaluation/run/CASE-001", ROLE_REVIEWER, False),
    ("POST", "/evaluation/run", ROLE_ADMIN, True),
    ("POST", "/api/evaluation/run", ROLE_REVIEWER, False),
    ("GET", "/evaluation/summary", ROLE_REVIEWER, True),
    # guest: read-only on demo-safe areas, sandbox writes on /demo only
    ("GET", "/dashboard/summary", ROLE_GUEST, True),
    ("GET", "/evaluation/summary", ROLE_GUEST, True),
    ("GET", "/demo/state", ROLE_GUEST, True),
    ("POST", "/demo/run-step", ROLE_GUEST, True),
    ("POST", "/demo/reset", ROLE_GUEST, True),
    ("GET", "/contracts", ROLE_GUEST, False),
    ("GET", "/contracts/CTR-REAL-1", ROLE_GUEST, False),
    ("GET", "/contracts/CTR-DEMO-2026-SAAS", ROLE_GUEST, True),
    ("POST", "/contracts", ROLE_GUEST, False),
    ("POST", "/contracts/CTR-1/analyze", ROLE_GUEST, False),
    ("POST", "/contracts/CTR-1/ask", ROLE_GUEST, False),
    ("POST", "/reviews/1/resolve", ROLE_GUEST, False),
    ("POST", "/evaluation/run", ROLE_GUEST, False),
    ("POST", "/mesh/analyze", ROLE_GUEST, False),
    ("POST", "/automations/x/execute", ROLE_GUEST, False),
    ("GET", "/audit", ROLE_GUEST, False),
    ("GET", "/memory", ROLE_GUEST, False),
    ("GET", "/reviews", ROLE_GUEST, False),
    ("DELETE", "/dashboard/summary", ROLE_GUEST, False),
    # unknown / missing roles never pass
    ("GET", "/dashboard/summary", "superuser", False),
    ("GET", "/dashboard/summary", None, False),
])
def test_rbac_policy(method, path, role, expected):
    assert is_allowed(method, path, role) is expected


@pytest.mark.asyncio
async def test_guest_is_blocked_from_real_data_and_mutations_over_http():
    guest = {"Authorization": f"Bearer {create_guest_token()}"}
    async with client() as ac:
        assert (await ac.get("/dashboard/summary", headers=guest)).status_code == 200
        for method, path in [
            ("GET", "/contracts"), ("GET", "/audit"), ("GET", "/memory"),
            ("POST", "/contracts"), ("POST", "/evaluation/run"), ("POST", "/mesh/analyze"),
        ]:
            res = await ac.request(method, path, headers=guest, json={} if method == "POST" else None)
            assert res.status_code == 403, f"{method} {path}"


@pytest.mark.asyncio
async def test_reviewer_cannot_run_evaluations_but_admin_passes_authorization():
    async with client() as ac:
        res = await ac.post("/evaluation/run", headers=auth_headers(ROLE_REVIEWER))
        assert res.status_code == 403
        # Admin is authorized (we only assert it is not an auth failure; we don't run the benchmark here).
        assert is_allowed("POST", "/evaluation/run", ROLE_ADMIN)


@pytest.mark.asyncio
async def test_authenticated_reviewer_can_use_protected_routes():
    async with client() as ac:
        res = await ac.get("/dashboard/summary", headers=auth_headers(ROLE_REVIEWER))
    assert res.status_code == 200


# ---------------------------------------------------------------- webhook HMAC

@pytest.mark.asyncio
async def test_webhooks_require_valid_hmac_when_secret_configured(monkeypatch):
    monkeypatch.setattr(settings, "FASTN_WEBHOOK_SECRET", "s3cret-for-tests")
    body = b"{}"
    async with client() as ac:
        missing = await ac.post("/webhooks/fastn/renewal-alert", content=body)
        wrong = await ac.post(
            "/webhooks/fastn/renewal-alert", content=body, headers={"X-Fastn-Signature": "deadbeef"}
        )
        good_sig = compute_webhook_signature("s3cret-for-tests", body)
        passed = await ac.post(
            "/webhooks/fastn/renewal-alert", content=body,
            headers={"X-Fastn-Signature": f"sha256={good_sig}", "Content-Type": "application/json"},
        )
    assert missing.status_code == 401
    assert wrong.status_code == 401
    assert passed.status_code != 401  # signature accepted; payload validation is the handler's concern


@pytest.mark.asyncio
async def test_webhooks_do_not_accept_user_jwts_as_a_substitute(monkeypatch):
    monkeypatch.setattr(settings, "FASTN_WEBHOOK_SECRET", "s3cret-for-tests")
    async with client() as ac:
        res = await ac.post("/webhooks/fastn/renewal-alert", content=b"{}", headers=auth_headers(ROLE_ADMIN))
    assert res.status_code == 401


# ---------------------------------------------------------------- google sign-in

@pytest.mark.asyncio
async def test_google_login_rejects_unsigned_email_payload(monkeypatch):
    """Regression: the endpoint must never trust a client-supplied email."""
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "client-id.apps.googleusercontent.com")
    async with client() as ac:
        res = await ac.post("/api/auth/google", json={"email": "admin@victim.com", "name": "Admin"})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_google_login_not_configured_returns_501(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", None)
    async with client() as ac:
        res = await ac.post("/api/auth/google", json={"credential": "x" * 40})
    assert res.status_code == 501


@pytest.mark.asyncio
async def test_google_login_rejects_invalid_token(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "client-id.apps.googleusercontent.com")

    def boom(*args, **kwargs):
        raise ValueError("bad token")

    monkeypatch.setattr(routes_auth.google_id_token, "verify_oauth2_token", boom)
    async with client() as ac:
        res = await ac.post("/api/auth/google", json={"credential": "x" * 40})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_google_login_rejects_unverified_google_email(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "client-id.apps.googleusercontent.com")
    monkeypatch.setattr(
        routes_auth.google_id_token, "verify_oauth2_token",
        lambda *a, **k: {"email": "u@gmail.com", "email_verified": False},
    )
    async with client() as ac:
        res = await ac.post("/api/auth/google", json={"credential": "x" * 40})
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_google_login_with_valid_verified_token_issues_session(monkeypatch):
    captured = {}

    def fake_verify(token, request, audience):
        captured["audience"] = audience
        return {"email": "Person@Gmail.com", "email_verified": True, "name": "Person"}

    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "client-id.apps.googleusercontent.com")
    monkeypatch.setattr(routes_auth.google_id_token, "verify_oauth2_token", fake_verify)
    async with client() as ac:
        res = await ac.post("/api/auth/google", json={"credential": "x" * 40})
        assert res.status_code == 200
        body = res.json()
        assert captured["audience"] == "client-id.apps.googleusercontent.com"
        assert body["user"]["email"] == "person@gmail.com"
        payload = decode_access_token(body["access_token"])
        assert payload["email"] == "person@gmail.com"
        assert "cas_refresh_token" in res.cookies


@pytest.mark.asyncio
async def test_auth_config_exposes_only_public_client_id(monkeypatch):
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "abc.apps.googleusercontent.com")
    async with client() as ac:
        res = await ac.get("/api/auth/config")
    assert res.status_code == 200
    assert res.json() == {"google_client_id": "abc.apps.googleusercontent.com"}


# ---------------------------------------------------------------- sessions

@pytest.mark.asyncio
async def test_refresh_token_rotation_and_reuse_detection():
    async with client() as ac:
        reg = await ac.post("/api/auth/register", json={"email": "rot@example.com", "password": "Passw0rd!long"})
        assert reg.status_code == 201
        token_a = reg.cookies.get("cas_refresh_token")
        assert token_a

    async with client() as ac:
        ac.cookies.set("cas_refresh_token", token_a)
        rotated = await ac.post("/api/auth/refresh")
        assert rotated.status_code == 200
        token_b = rotated.cookies.get("cas_refresh_token")
        assert token_b and token_b != token_a

    # Replaying the already-rotated token is treated as theft: the whole family dies.
    async with client() as ac:
        ac.cookies.set("cas_refresh_token", token_a)
        replay = await ac.post("/api/auth/refresh")
        assert replay.status_code == 401

    async with client() as ac:
        ac.cookies.set("cas_refresh_token", token_b)
        legit_now_revoked = await ac.post("/api/auth/refresh")
        assert legit_now_revoked.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token():
    async with client() as ac:
        reg = await ac.post("/api/auth/register", json={"email": "out@example.com", "password": "Passw0rd!long"})
        token = reg.cookies.get("cas_refresh_token")
        await ac.post("/api/auth/logout")

    async with client() as ac:
        ac.cookies.set("cas_refresh_token", token)
        res = await ac.post("/api/auth/refresh")
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_login_is_rate_limited():
    async with client() as ac:
        codes = []
        for _ in range(12):
            res = await ac.post("/api/auth/login", json={"email": "nobody@example.com", "password": "wrong-password"})
            codes.append(res.status_code)
    assert codes[:10] == [401] * 10
    assert 429 in codes[10:]


# ---------------------------------------------------------------- roles at signup

@pytest.mark.asyncio
async def test_admin_role_comes_from_admin_emails_not_signup_order(monkeypatch):
    monkeypatch.setattr(settings, "ADMIN_EMAILS", "boss@example.com")
    async with client() as ac:
        first = await ac.post("/api/auth/register", json={"email": "random@example.com", "password": "Passw0rd!long"})
        boss = await ac.post("/api/auth/register", json={"email": "Boss@example.com", "password": "Passw0rd!long"})
    assert first.json()["user"]["role"] == ROLE_REVIEWER  # being first confers nothing
    assert boss.json()["user"]["role"] == ROLE_ADMIN
