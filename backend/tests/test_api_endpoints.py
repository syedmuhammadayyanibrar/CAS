import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.mark.asyncio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert "Fastn" in data["nervous_system"]
    assert len(data["active_societies"]) == 6


@pytest.mark.asyncio
async def test_standalone_contract_intelligence_endpoint(test_contract_text):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
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
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
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
