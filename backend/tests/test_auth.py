import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.core.auth import create_access_token, create_guest_token, decode_access_token


@pytest.mark.asyncio
async def test_guest_token_generation_and_decoding():
    token = create_guest_token()
    payload = decode_access_token(token)
    assert payload["role"] == "guest"
    assert payload["email"].endswith("@cas.local")
    assert payload["type"] == "access"


@pytest.mark.asyncio
async def test_access_token_generation_and_decoding():
    token = create_access_token(
        user_id="test_user_1",
        email="lawyer@example.com",
        role="reviewer",
        full_name="Jane Doe",
    )
    payload = decode_access_token(token)
    assert payload["sub"] == "test_user_1"
    assert payload["email"] == "lawyer@example.com"
    assert payload["role"] == "reviewer"
    assert payload["name"] == "Jane Doe"


@pytest.mark.asyncio
async def test_auth_endpoints_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Guest login endpoint
        guest_res = await client.post("/api/auth/guest")
        assert guest_res.status_code == 200
        guest_data = guest_res.json()
        assert "access_token" in guest_data
        assert guest_data["user"]["role"] == "guest"

        # 2. Register endpoint
        reg_payload = {
            "email": "counsel@example.com",
            "password": "SecurePassword123!",
            "full_name": "General Counsel",
        }
        reg_res = await client.post("/api/auth/register", json=reg_payload)
        assert reg_res.status_code == 201
        reg_data = reg_res.json()
        assert "access_token" in reg_data
        assert reg_data["user"]["email"] == "counsel@example.com"
        # First registered user becomes admin
        assert reg_data["user"]["role"] == "admin"
        assert "cas_refresh_token" in reg_res.cookies

        token = reg_data["access_token"]

        # 3. /me endpoint with token
        me_res = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me_res.status_code == 200
        assert me_res.json()["email"] == "counsel@example.com"

        # 4. /me endpoint without token -> 401
        me_unauth = await client.get("/api/auth/me")
        assert me_unauth.status_code == 401

        # 5. Login endpoint
        login_res = await client.post(
            "/api/auth/login",
            json={"email": "counsel@example.com", "password": "SecurePassword123!"},
        )
        assert login_res.status_code == 200
        assert "access_token" in login_res.json()

        # 6. Refresh token rotation
        refresh_res = await client.post("/api/auth/refresh")
        assert refresh_res.status_code == 200
        assert "access_token" in refresh_res.json()

        # 7. Logout
        logout_res = await client.post("/api/auth/logout")
        assert logout_res.status_code == 200


@pytest.mark.asyncio
async def test_guest_forbid_decorator():
    from backend.core.auth import forbid_guest
    from fastapi import HTTPException

    guest_payload = {"role": "guest", "sub": "guest-123"}
    with pytest.raises(HTTPException) as exc_info:
        forbid_guest(guest_payload)
    assert exc_info.value.status_code == 403

    reviewer_payload = {"role": "reviewer", "sub": "rev-123"}
    allowed = forbid_guest(reviewer_payload)
    assert allowed["role"] == "reviewer"
