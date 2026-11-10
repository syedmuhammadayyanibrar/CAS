from backend.core.auth import create_access_token


def auth_headers(role: str = "admin") -> dict:
    """Authorization header carrying a genuine, correctly signed access token."""
    token = create_access_token(
        user_id=f"test-{role}",
        email=f"{role}@example.com",
        role=role,
        full_name=f"Test {role.title()}",
    )
    return {"Authorization": f"Bearer {token}"}
