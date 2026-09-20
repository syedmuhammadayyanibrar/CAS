from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from backend.database.db import get_db
from backend.models.events import FastnWebhookPayload
from backend.models.cas_message import CASMessage
from backend.events.bus import event_bus
from backend.director.coordinator import cas_director
from backend.core.logging import get_logger

logger = get_logger("FastnWebhooks")
router = APIRouter(prefix="/webhooks/fastn", tags=["Fastn Webhooks"])


@router.post("/contract-intake")
async def receive_contract_intake(
    payload: FastnWebhookPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Receives contract upload events from Fastn (Google Drive / Inbound Webhook).
    Dispatches to CAS Director and emits CASMessage.
    """
    logger.info(f"Received Fastn Inbound Contract Intake Webhook for document: {payload.documentName}")

    content = payload.content or "Master Services Agreement between Parties."
    cid = payload.contractId or f"CTR-FASTN-{payload.documentName[:8]}"

    # Publish message to bus
    msg = CASMessage.create(
        contract_id=cid,
        source_system="fastn_webhook",
        target_system="director",
        event_type="CONTRACT_INTAKE",
        payload=payload.model_dump(),
        priority="HIGH"
    )
    await event_bus.publish(msg)

    # Trigger mesh analysis in background or inline
    res = await cas_director.orchestrate_mesh(
        contract_text=content,
        contract_id=cid,
        db_session=db
    )

    return {
        "status": "ACCEPTED",
        "contract_id": cid,
        "director_status": res.get("status"),
        "activated_societies": res.get("director_routing", {}).get("activated_societies", [])
    }


@router.post("/renewal-alert")
async def receive_renewal_alert(payload: Dict[str, Any]):
    """Receives impending renewal notices from the Fastn cas-renewal-monitor workflow."""
    logger.info(f"Received Fastn Renewal Alert Webhook: {payload}")
    cid = payload.get("contractId", "UNKNOWN_CONTRACT")

    msg = CASMessage.create(
        contract_id=cid,
        source_system="fastn_scheduler",
        target_system="director",
        event_type="RENEWAL_WINDOW_OPEN",
        payload=payload,
        priority="HIGH"
    )
    await event_bus.publish(msg)

    return {"status": "ALERT_PROCESSED", "contract_id": cid}


@router.post("/approval")
async def receive_inbound_approval(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Receives Human-In-The-Loop approval/rejection decisions from Fastn Webhooks (Slack/Email).
    Routes into CAS Director to update contract lifecycle, record precedents, and archive decisions.
    """
    logger.info(f"Received Fastn Inbound Approval Webhook: {payload}")
    eid = payload.get("eventId") or payload.get("event_id")
    res = await cas_director.handle_inbound_fastn_event(
        payload=payload,
        event_type="APPROVAL_DECISION",
        event_id=eid,
        db_session=db
    )
    return res


@router.post("/negotiation")
async def receive_inbound_negotiation(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Receives counterparty proposals and redlines from Fastn Webhooks.
    Triggers Negotiation Intelligence re-evaluation and broadcasts counter-terms back through Fastn.
    """
    logger.info(f"Received Fastn Inbound Negotiation Webhook: {payload}")
    eid = payload.get("eventId") or payload.get("event_id")
    res = await cas_director.handle_inbound_fastn_event(
        payload=payload,
        event_type="COUNTERPARTY_PROPOSAL",
        event_id=eid,
        db_session=db
    )
    return res


@router.post("/deadline")
async def receive_inbound_deadline(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Receives obligation deadline changes or milestone delays from Fastn Webhooks.
    Triggers Obligation Intelligence updates and Fastn deadline escalation alerts.
    """
    logger.info(f"Received Fastn Inbound Deadline Webhook: {payload}")
    eid = payload.get("eventId") or payload.get("event_id")
    res = await cas_director.handle_inbound_fastn_event(
        payload=payload,
        event_type="DEADLINE_CHANGE",
        event_id=eid,
        db_session=db
    )
    return res


@router.post("/inbound")
async def receive_generic_inbound(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db)
):
    """
    Generic Fastn Inbound Multiplexer endpoint.
    Extracts event_type from payload, verifies idempotency, and routes to the appropriate society.
    """
    logger.info(f"Received Generic Fastn Inbound Webhook: {payload}")
    event_type = payload.get("eventType") or payload.get("event_type") or "GENERIC_INBOUND"
    eid = payload.get("eventId") or payload.get("event_id")
    res = await cas_director.handle_inbound_fastn_event(
        payload=payload,
        event_type=event_type,
        event_id=eid,
        db_session=db
    )
    return res

