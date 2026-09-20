import pytest
from backend.systems.risk_intelligence.system import risk_intelligence_system
from backend.models.findings import RiskReport


@pytest.mark.asyncio
async def test_risk_intelligence_adversarial_debate(test_contract_text, db_session):
    """Verifies that Risk Intelligence runs the adversarial debate pipeline independently."""
    report = await risk_intelligence_system.analyze_risk(
        contract=test_contract_text,
        contract_id="TEST-RISK-001",
        db_session=db_session
    )

    assert isinstance(report, RiskReport)
    assert report.contract_id == "TEST-RISK-001"
    assert len(report.findings) > 0

    # Ensure counterarguments were produced for findings
    for finding in report.findings:
        assert finding.counter_argument != ""
        assert finding.evidence != ""
        assert finding.suggested_mitigation != ""
        assert finding.net_severity in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
