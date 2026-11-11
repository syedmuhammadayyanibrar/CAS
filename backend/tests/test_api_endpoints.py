import pytest
from httpx import AsyncClient, ASGITransport
from backend.tests.helpers import auth_headers
from backend.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=auth_headers("admin")) as ac:
        res = await ac.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert "Fastn" in data["nervous_system"]
    assert len(data["active_societies"]) == 6


@pytest.mark.asyncio
async def test_standalone_contract_intelligence_endpoint(test_contract_text):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=auth_headers("admin")) as ac:
        res = await ac.post("/systems/contract-intelligence/analyze", json={
            "contract_text": test_contract_text[:1000],
            "contract_id": "CTR-API-01"
        })
    assert res.status_code == 200
    data = res.json()
    assert data["contract_id"] == "CTR-API-01"
    assert "clauses" in data
    assert "parties" in data


@pytest.mark.asyncio
async def test_mesh_analyze_endpoint(test_contract_text):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers=auth_headers("admin")) as ac:
        res = await ac.post("/mesh/analyze", json={
            "contract_text": test_contract_text[:1000],
            "contract_id": "CTR-API-MESH"
        })
    assert res.status_code == 200
    data = res.json()
    assert data["contract_id"] == "CTR-API-MESH"
    assert "director_routing" in data
    assert "risk_report" in data
    assert "compliance_report" in data


@pytest.mark.asyncio
async def test_browser_spa_refresh_and_back_routes():
    """Browser navigation/refresh requests (Accept: text/html) on SPA paths must serve index.html, not 401/404."""
    transport = ASGITransport(app=app)
    browser_headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
    }
    spa_routes = [
        "/",
        "/contracts",
        "/contracts/CTR-2026-001",
        "/approvals",
        "/societies",
        "/automations",
        "/memory",
        "/demo",
        "/evaluation",
        "/login",
        "/ui/contracts/CTR-2026-001",
    ]
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        for route in spa_routes:
            res = await ac.get(route, headers=browser_headers)
            assert res.status_code == 200, f"Expected 200 HTML on {route}, got {res.status_code}"
            assert "text/html" in res.headers.get("content-type", ""), f"Expected HTML content-type on {route}"
            assert "<div id=\"root\">" in res.text

