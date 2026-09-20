import pytest
from backend.systems.dispute_intelligence.system import dispute_intelligence_system
from backend.models.findings import DisputeAssessment


@pytest.mark.asyncio
async def test_dispute_intelligence_simulation(test_contract_text, db_session):
    """Verifies Dispute Intelligence multi-perspective simulation and scenario generation."""
    assessment = await dispute_intelligence_system.analyze_disputes(
        contract=test_contract_text,
        contract_id="TEST-DISP-001",
        party_a_name="Acme Global",
        party_b_name="NovaCloud",
        db_session=db_session
    )

    assert isinstance(assessment, DisputeAssessment)
    assert assessment.contract_id == "TEST-DISP-001"
    assert len(assessment.scenarios) > 0

    for s in assessment.scenarios:
        assert s.clause_text != ""
        assert s.party_a_interpretation != ""
        assert s.party_b_interpretation != ""
        assert s.simulated_dispute_narrative != ""
        assert s.resolution_strategy != ""
