import pytest
import uuid
from backend.integrations.fastn_client import fastn_client, mask_secrets
from backend.director.coordinator import cas_director
from backend.events.bus import event_bus
from backend.memory.cas_memory import cas_memory


@pytest.mark.asyncio
async def test_fastn_workflow_catalog_complete():
    """Verifies that all 10 specialized workflows are registered in the Fastn catalog."""
    catalog = fastn_client.get_workflow_catalog()
    assert len(catalog) == 10

    slugs = [wf["slug"] for wf in catalog]
    expected_slugs = [
        "cas-contract-intake",
        "cas-risk-escalation",
        "cas-approval-dispatch",
        "cas-obligation-sync",
        "cas-renewal-monitor",
        "cas-compliance-escalation",
        "cas-negotiation-update",
        "cas-deadline-escalation",
        "cas-dispute-escalation",
        "cas-decision-archive",
    ]
    for expected in expected_slugs:
        assert expected in slugs

    # Verify direction attributes
    inbound_wfs = [wf for wf in catalog if wf.get("direction") == "INBOUND"]
    outbound_wfs = [wf for wf in catalog if wf.get("direction") == "OUTBOUND"]
    assert len(inbound_wfs) >= 1
    assert len(outbound_wfs) >= 5


@pytest.mark.asyncio
async def test_fastn_compliance_escalation_workflow():
    """Verifies execution of the new cas-compliance-escalation workflow."""
    res = await fastn_client.execute_compliance_escalation(
        contract_id="CTR-TEST-COMP-01",
        policy_name="GDPR Standard Policy",
        violations_count=2,
        violations=[
            {"policy": "Sub-processor audit", "severity": "CRITICAL", "description": "Missing audit rights."},
            {"policy": "Data retention limit", "severity": "HIGH", "description": "Undefined retention period."}
        ]
    )
    assert res["workflow"] == "cas-compliance-escalation"
    assert res["status"] == "DISPATCHED"
    assert res["violationsCount"] == 2
    assert "escalationRecord" in res


@pytest.mark.asyncio
async def test_fastn_negotiation_update_workflow():
    """Verifies execution of the new cas-negotiation-update workflow."""
    res = await fastn_client.execute_negotiation_update(
        contract_id="CTR-TEST-NEG-01",
        positions=[
            {
                "clause": "Section 8.2",
                "status": "COUNTER_OFFERED",
                "originalTerm": "Unilateral cap",
                "proposedRedline": "Mutual $240,000 cap",
                "rationale": "Symmetry requirement"
            }
        ],
        channel="#contract-negotiations"
    )
    assert res["workflow"] == "cas-negotiation-update"
    assert res["status"] == "DISPATCHED"
    assert res["positionsCount"] == 1


@pytest.mark.asyncio
async def test_fastn_dispute_escalation_workflow():
    """Verifies execution of the new cas-dispute-escalation workflow."""
    res = await fastn_client.execute_dispute_escalation(
        contract_id="CTR-TEST-DISP-01",
        dispute_risk="HIGH",
        ambiguities=["Conflicting SLA calculation formulas in Section 4 vs Section 14."],
        counterparty_stance="Counterparty will claim upstream host downtime exempts SLA remedies.",
        recommended_action="Draft redline harmonizing remedy clauses."
    )
    assert res["workflow"] == "cas-dispute-escalation"
    assert res["status"] == "DISPATCHED"
    assert res["disputeRisk"] == "HIGH"


@pytest.mark.asyncio
async def test_fastn_decision_archive_workflow():
    """Verifies execution of the new cas-decision-archive workflow."""
    res = await fastn_client.execute_decision_archive(
        contract_id="CTR-TEST-ARC-01",
        decision="APPROVED",
        decision_maker="General Counsel",
        society="CAS_FEDERATION",
        reason="Approved bilateral compromise terms.",
        evidence="Risk score reduced to 0.22 under mutual indemnity caps.",
        resulting_action="EXECUTE_SIGNATURE"
    )
    assert res["workflow"] == "cas-decision-archive"
    assert res["status"] == "ARCHIVED"
    assert res["decision"] == "APPROVED"
    assert "airtablePersistence" in res["archiveRecord"]
    assert "googleDriveArchive" in res["archiveRecord"]


@pytest.mark.asyncio
async def test_fastn_inbound_approval_handling():
    """Verifies bidirectional flow: Inbound Approval Webhook -> CAS Director -> Memory -> Downstream Activation."""
    test_eid = f"EVT-APPROVE-{uuid.uuid4().hex[:6]}"
    res = await cas_director.handle_inbound_fastn_event(
        payload={
            "contractId": "CTR-TEST-FLOW-01",
            "decision": "APPROVED",
            "reviewerId": "general_counsel@acme.com",
            "decisionNotes": "Approved redline terms via Fastn Slack webhook interaction."
        },
        event_type="APPROVAL_DECISION",
        event_id=test_eid
    )

    assert res["status"] == "SUCCESS"
    assert res["contract_id"] == "CTR-TEST-FLOW-01"
    assert res["decision"] == "APPROVED"
    assert "obligation_intelligence" in res["activated_downstream_societies"]
    assert res["lifecycle_state"] == "SIGNED"


@pytest.mark.asyncio
async def test_fastn_inbound_negotiation_handling():
    """Verifies bidirectional flow: Inbound Counterparty Redline -> Director Re-Routing -> Dynamic Strategy Update."""
    test_eid = f"EVT-REDLINE-{uuid.uuid4().hex[:6]}"
    res = await cas_director.handle_inbound_fastn_event(
        payload={
            "contractId": "CTR-TEST-FLOW-02",
            "clauseReference": "Section 8.2 Limitation of Liability",
            "counterpartyProposal": "Mutual aggregate cap of $240,000 accepted.",
            "concessionOffered": "Withdrew unilateral liability shield."
        },
        event_type="COUNTERPARTY_PROPOSAL",
        event_id=test_eid
    )

    assert res["status"] == "SUCCESS"
    assert res["contract_id"] == "CTR-TEST-FLOW-02"
    assert "negotiation_posture" in res
    assert res["negotiation_posture"]["status"] == "RE_EVALUATED"
    assert "fastn_broadcast" in res


@pytest.mark.asyncio
async def test_fastn_idempotency_protection():
    """Verifies that duplicate Fastn events are safely deduplicated and not reprocessed."""
    duplicate_eid = f"EVT-IDEMPOTENT-{uuid.uuid4().hex[:8]}"

    # First call - should process successfully
    res1 = await cas_director.handle_inbound_fastn_event(
        payload={
            "contractId": "CTR-TEST-IDEM-01",
            "decision": "APPROVED",
            "reviewerId": "lead@org.com",
            "notes": "First submission"
        },
        event_type="APPROVAL_DECISION",
        event_id=duplicate_eid
    )
    assert res1["status"] == "SUCCESS"

    # Second call with the same event_id - should be blocked by idempotency
    res2 = await cas_director.handle_inbound_fastn_event(
        payload={
            "contractId": "CTR-TEST-IDEM-01",
            "decision": "APPROVED",
            "reviewerId": "lead@org.com",
            "notes": "Duplicate retry from webhook failure"
        },
        event_type="APPROVAL_DECISION",
        event_id=duplicate_eid
    )
    assert res2["status"] == "DUPLICATE_IGNORED"
    assert res2["event_id"] == duplicate_eid


@pytest.mark.asyncio
async def test_fastn_execution_tracing_and_credential_masking():
    """Verifies live execution trace recording and recursive credential masking."""
    # Test secret masking function
    sensitive_data = {
        "api_key": "sec_live_938173491823",
        "client_token": "tok_xyz_secret_999",
        "nested": {
            "auth_password": "super_secret_pw",
            "normal_field": "public_contract_text"
        }
    }
    masked = mask_secrets(sensitive_data)
    assert masked["api_key"] == "***"
    assert masked["client_token"] == "***"
    assert masked["nested"]["auth_password"] == "***"
    assert masked["nested"]["normal_field"] == "public_contract_text"

    # Test trace query
    traces = await fastn_client.get_recent_executions(limit=10)
    assert isinstance(traces, list)
    assert len(traces) > 0
    # Every trace must have standard telemetry fields
    for t in traces[:5]:
        assert "workflow_slug" in t
        assert "direction" in t
        assert "status" in t
        assert "connector" in t


@pytest.mark.asyncio
async def test_fastn_trigger_inbound_methods():
    """Verifies trigger_inbound_negotiation and trigger_inbound_approval helper methods."""
    neg_res = await fastn_client.trigger_inbound_negotiation(
        contract_id="CTR-TEST-INBOUND-01",
        clause_reference="Section 8.2 Limitation of Liability",
        counterparty_proposal="Bilateral 12-month trailing fee cap ($240,000).",
        concession_offered="Withdrew unilateral cap requirement."
    )
    assert neg_res["workflow"] == "cas-inbound-negotiation"
    assert neg_res["contractId"] == "CTR-TEST-INBOUND-01"
    assert "counterpartyProposal" in neg_res

    appr_res = await fastn_client.trigger_inbound_approval(
        contract_id="CTR-TEST-INBOUND-02",
        decision="APPROVED",
        reviewer_id="legal_counsel@enterprise.com",
        decision_notes="Approved redlines."
    )
    assert appr_res["workflow"] == "cas-inbound-approval"
    assert appr_res["decision"] == "APPROVED"
    assert appr_res["reviewerId"] == "legal_counsel@enterprise.com"

