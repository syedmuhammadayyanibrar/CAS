import pytest
import os
from backend.systems.compliance_intelligence.system import compliance_intelligence_system
from backend.models.findings import ComplianceReport


@pytest.mark.asyncio
async def test_compliance_intelligence_audit(test_contract_text, db_session):
    """Verifies Compliance Intelligence retrieval, rules, and verification pipeline."""
    policy_path = os.path.join(os.path.dirname(__file__), "../../policies/corporate_compliance_policy.json")
    report = await compliance_intelligence_system.audit_compliance(
        contract=test_contract_text,
        policy_path=policy_path,
        contract_id="TEST-COMP-001",
        db_session=db_session
    )

    assert isinstance(report, ComplianceReport)
    assert report.contract_id == "TEST-COMP-001"
    assert len(report.findings) > 0

    # Ensure findings are grounded in policy rules and evidence
    for f in report.findings:
        assert f.rule_id != ""
        assert f.requirement != ""
        assert f.compliance_status in ("COMPLIANT", "VIOLATION", "AMBIGUOUS", "EXEMPT")
        assert f.recommended_action != ""
