import pytest
from backend.systems.obligation_intelligence.system import obligation_intelligence_system
from backend.models.findings import ObligationSchedule


@pytest.mark.asyncio
async def test_obligation_intelligence_monitoring(test_contract_text, db_session):
    """Verifies Obligation Intelligence event-driven schedule and monitoring ticks."""
    schedule = await obligation_intelligence_system.register_obligations(
        contract=test_contract_text,
        contract_id="TEST-OBL-001",
        effective_date="2026-10-01",
        db_session=db_session
    )

    assert isinstance(schedule, ObligationSchedule)
    assert schedule.contract_id == "TEST-OBL-001"
    assert schedule.total_obligations > 0

    for item in schedule.items:
        assert item.party != ""
        assert item.title != ""
        assert item.type in ("PAYMENT", "DELIVERABLE", "RENEWAL", "REPORTING", "SLA")
