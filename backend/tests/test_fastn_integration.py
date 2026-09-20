import pytest
from backend.integrations.fastn_client import fastn_client
from backend.integrations.adapters import SlackAdapter, GoogleCalendarAdapter


@pytest.mark.asyncio
async def test_fastn_risk_escalation_workflow():
    """Verifies execution of the Fastn cas-risk-escalation workflow."""
    res = await fastn_client.execute_risk_escalation(
        contract_id="TEST-CTR-FASTN",
        severity="CRITICAL",
        risky_clause="Section 8.2 Asymmetric Cap",
        consequence="Unlimited Customer exposure with 1-month Vendor shield",
        evidence="Verbatim quote from Section 8.2"
    )

    assert res["workflow"] == "cas-risk-escalation"
    assert res["status"] == "DISPATCHED"
    assert res["payload"]["severity"] == "CRITICAL"


@pytest.mark.asyncio
async def test_fastn_obligation_sync_workflow():
    """Verifies execution of the Fastn cas-obligation-sync workflow."""
    obligations = [
        {"title": "Net 30 Payment", "party": "Customer", "dueDate": "2026-10-31", "type": "PAYMENT", "noticeDays": 7}
    ]
    res = await fastn_client.execute_obligation_sync(
        contract_id="TEST-CTR-FASTN",
        obligations=obligations
    )

    assert res["workflow"] == "cas-obligation-sync"
    assert res["status"] == "DISPATCHED"
    assert res["synced_count"] == 1


@pytest.mark.asyncio
async def test_fastn_slack_adapter():
    """Verifies SlackAdapter mediated via Fastn."""
    res = await SlackAdapter.post_risk_alert(
        contract_id="TEST-SLACK-01",
        severity="HIGH",
        clause="Section 10 Indemnity",
        consequence="Uncapped liability",
        evidence="Section 10 text"
    )
    assert res["workflow"] == "cas-risk-escalation"
