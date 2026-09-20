import pytest
from backend.systems.negotiation_intelligence.system import negotiation_intelligence_system
from backend.models.findings import NegotiationStrategy


@pytest.mark.asyncio
async def test_negotiation_intelligence_standalone(test_contract_text, db_session):
    """Verifies Negotiation Intelligence planner, simulator, and critic pipeline."""
    objective = "Cap liability at 12 months fees, eliminate uncapped indemnity, and ensure mutual 30-day termination."
    strategy = await negotiation_intelligence_system.plan_negotiation(
        contract=test_contract_text,
        objective=objective,
        contract_id="TEST-NEG-001",
        db_session=db_session
    )

    assert isinstance(strategy, NegotiationStrategy)
    assert strategy.contract_id == "TEST-NEG-001"
    assert len(strategy.positions) > 0
    assert len(strategy.negotiation_sequence) > 0

    for pos in strategy.positions:
        assert pos.desired_outcome != ""
        assert pos.red_line != ""
        assert pos.counter_proposal != ""
        assert pos.simulated_counterparty_reaction != ""
