import pytest
import os
from backend.director.coordinator import cas_director
from backend.models.cas_message import CASMessage
from backend.events.bus import event_bus


@pytest.mark.asyncio
async def test_cas_director_mesh_orchestration(test_contract_text, db_session):
    """Verifies Director dynamic orchestration across all societies and cross-subsystem arbitration."""
    policy_path = os.path.join(os.path.dirname(__file__), "../../policies/corporate_compliance_policy.json")

    mesh_res = await cas_director.orchestrate_mesh(
        contract_text=test_contract_text,
        contract_id="TEST-MESH-001",
        commercial_objective="Cap liability at 12 months, eliminate uncapped indemnity, and secure bilateral termination.",
        policy_path=policy_path,
        db_session=db_session
    )

    assert mesh_res["contract_id"] == "TEST-MESH-001"
    assert "contract_graph" in mesh_res
    assert "risk_report" in mesh_res
    assert "compliance_report" in mesh_res
    assert "negotiation_strategy" in mesh_res
    assert "dispute_assessment" in mesh_res
    assert "director_routing" in mesh_res

    # Verify activated societies
    activated = mesh_res["director_routing"]["activated_societies"]
    assert "contract_intelligence" in activated
    assert "risk_intelligence" in activated
    assert "compliance_intelligence" in activated
    assert "negotiation_intelligence" in activated


@pytest.mark.asyncio
async def test_cas_message_event_bus():
    """Verifies standard CASMessage publication and consumption."""
    received = []

    async def sample_handler(msg: CASMessage):
        received.append(msg)

    event_bus.subscribe("TEST_EVENT", sample_handler)

    test_msg = CASMessage.create(
        contract_id="CTR-BUS-01",
        source_system="risk_intelligence",
        target_system="negotiation_intelligence",
        event_type="TEST_EVENT",
        payload={"alert": "High risk detected on clause 8.2"},
        priority="HIGH"
    )

    await event_bus.publish(test_msg)
    assert len(received) == 1
    assert received[0].event_id == test_msg.event_id
    assert received[0].priority == "HIGH"
