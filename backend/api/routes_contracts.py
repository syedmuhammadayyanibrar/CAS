from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
import json
import base64
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from backend.director.execution_tracker import execution_tracker
from backend.core.document_parser import DocumentParser

from backend.database.db import get_db
from backend.database.schema import (
    ContractModel,
    ContractGraphModel,
    RiskReportModel,
    ComplianceReportModel,
    NegotiationStrategyModel,
    ObligationScheduleModel,
    DisputeAssessmentModel,
    HumanReviewModel,
)
from backend.director.coordinator import cas_director
from backend.systems.obligation_intelligence.system import obligation_intelligence_system
from backend.memory.feedback_loops import feedback_loops
from backend.models.hitl import HumanDecision
from backend.core.gemini_service import gemini_service

router = APIRouter(prefix="/contracts", tags=["Contracts Lifecycle"])


class ContractUploadRequest(BaseModel):
    title: Optional[str] = "Untitled Agreement"
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ContractNegotiateRequest(BaseModel):
    objective: str


class AskContractRequest(BaseModel):
    question: str


class DirectExtractRequest(BaseModel):
    filename: str = "document.txt"
    base64_data: Optional[str] = None
    text_content: Optional[str] = None


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_contract(req: ContractUploadRequest, db: AsyncSession = Depends(get_db)):
    """Ingests a new contract document into the CAS repository."""
    import uuid
    cid = f"CTR-{uuid.uuid4().hex[:8].upper()}"
    contract = ContractModel(
        id=cid,
        title=req.title or "Untitled Agreement",
        raw_text=req.content,
        status="INTAKE",
        metadata_json=req.metadata or {}
    )
    db.add(contract)
    await db.commit()
    await db.refresh(contract)
    return {"contract_id": contract.id, "title": contract.title, "status": contract.status}


@router.post("/upload-document", status_code=status.HTTP_200_OK)
async def upload_contract_document(
    file: UploadFile = File(...),
    create_contract: bool = Form(False),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts native document uploads (.docx, .pdf, .txt, .md, .json),
    extracts contract text with structural metadata, and optionally registers
    a new Contract in the CAS repository.
    """
    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    try:
        parsed = DocumentParser.extract_text_from_bytes(file.filename or "uploaded_contract.txt", content_bytes)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Document parsing error: {str(e)}")

    if create_contract:
        import uuid
        cid = f"CTR-{uuid.uuid4().hex[:8].upper()}"
        contract = ContractModel(
            id=cid,
            title=parsed["detected_title"] or "Uploaded Agreement",
            raw_text=parsed["content"],
            status="INTAKE",
            metadata_json={
                "source": "native_upload",
                "filename": parsed["filename"],
                "file_type": parsed["file_type"],
                "word_count": parsed["word_count"],
                "character_count": parsed["character_count"],
                "parties": parsed["detected_parties"],
            }
        )
        db.add(contract)
        await db.commit()
        await db.refresh(contract)
        parsed["contract_id"] = contract.id
        parsed["status"] = contract.status

    return parsed


@router.post("/extract-text", status_code=status.HTTP_200_OK)
async def extract_text_from_payload(req: DirectExtractRequest):
    """Extracts text from base64 document or raw text."""
    if req.base64_data:
        try:
            raw_bytes = base64.b64decode(req.base64_data)
            return DocumentParser.extract_text_from_bytes(req.filename, raw_bytes)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to decode base64 data: {e}")
    elif req.text_content:
        return DocumentParser.extract_text_from_bytes(req.filename, req.text_content.encode("utf-8"))
    raise HTTPException(status_code=400, detail="Provide either base64_data or text_content.")



@router.get("")
async def list_contracts(db: AsyncSession = Depends(get_db)):
    """Lists all contracts managed in the CAS database with risk scores and counterparties."""
    stmt = select(ContractModel).order_by(ContractModel.created_at.desc())
    res = await db.execute(stmt)
    contracts = res.scalars().all()

    items = []
    for c in contracts:
        risk_stmt = (
            select(RiskReportModel)
            .where(RiskReportModel.contract_id == c.id)
            .order_by(desc(RiskReportModel.id))
            .limit(1)
        )
        r_rec = (await db.execute(risk_stmt)).scalars().first()
        party_name = c.metadata_json.get("counterparty") if c.metadata_json else None

        items.append({
            "id": c.id,
            "title": c.title,
            "status": c.status,
            "governing_law": c.governing_law,
            "counterparty": party_name or "Counterparty",
            "risk_score": r_rec.overall_score if r_rec else None,
            "requires_escalation": r_rec.requires_escalation if r_rec else False,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None,
        })
    return items


@router.get("/{contract_id}")
async def get_contract(contract_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves full contract metadata, raw text, and current lifecycle status."""
    contract = await db.get(ContractModel, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")
    
    risk_stmt = (
        select(RiskReportModel)
        .where(RiskReportModel.contract_id == contract_id)
        .order_by(desc(RiskReportModel.id))
        .limit(1)
    )
    risk_rec = (await db.execute(risk_stmt)).scalars().first()

    return {
        "id": contract.id,
        "title": contract.title,
        "status": contract.status,
        "raw_text": contract.raw_text,
        "governing_law": contract.governing_law,
        "effective_date": contract.effective_date,
        "expiration_date": contract.expiration_date,
        "metadata": contract.metadata_json or {},
        "risk_score": risk_rec.overall_score if risk_rec else None,
        "requires_escalation": risk_rec.requires_escalation if risk_rec else False,
        "created_at": contract.created_at.isoformat() if contract.created_at else None,
        "updated_at": contract.updated_at.isoformat() if contract.updated_at else None,
    }


@router.post("/{contract_id}/ask")
async def ask_contract(
    contract_id: str,
    req: AskContractRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Asks CAS a question grounded specifically in this contract's clauses,
    risk findings, compliance status, obligations, and simulated disputes.
    Powered solely by Google Gemini API.
    """
    contract = await db.get(ContractModel, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")

    # Fetch available reports
    graph = (await db.execute(select(ContractGraphModel).where(ContractGraphModel.contract_id == contract_id).order_by(desc(ContractGraphModel.id)).limit(1))).scalars().first()
    risk = (await db.execute(select(RiskReportModel).where(RiskReportModel.contract_id == contract_id).order_by(desc(RiskReportModel.id)).limit(1))).scalars().first()
    comp = (await db.execute(select(ComplianceReportModel).where(ComplianceReportModel.contract_id == contract_id).order_by(desc(ComplianceReportModel.id)).limit(1))).scalars().first()
    ob = (await db.execute(select(ObligationScheduleModel).where(ObligationScheduleModel.contract_id == contract_id).order_by(desc(ObligationScheduleModel.id)).limit(1))).scalars().first()
    disp = (await db.execute(select(DisputeAssessmentModel).where(DisputeAssessmentModel.contract_id == contract_id).order_by(desc(DisputeAssessmentModel.id)).limit(1))).scalars().first()

    context_prompt = f"""
You are the CAS Legal Intelligence Officer for Contract: {contract.title} (ID: {contract_id}).
Answer the user's question with precise legal grounding, citing relevant clauses, risk scores, compliance rules, or obligations.

CONTRACT METADATA:
Title: {contract.title}
Status: {contract.status}
Governing Law: {contract.governing_law or 'Delaware'}

CONTRACT FULL TEXT (excerpt):
{contract.raw_text[:4000]}

MULTI-AGENT INTELLIGENCE FINDINGS:
- Risk Report: Overall Score {risk.overall_score if risk else 'Not analyzed'} (Escalation: {risk.requires_escalation if risk else False})
- Compliance Status: {comp.overall_status if comp else 'Not audited'}
- Total Obligations: {ob.total_obligations if ob else 0}
- Dispute Risk Index: {disp.overall_dispute_risk if disp else 'Not assessed'}

USER QUESTION:
{req.question}

Please provide an authoritative, clear, and grounded response. Cite specific contract clauses, financial risks, compliance variances, or dates where relevant.
"""
    answer = await gemini_service.generate_text(
        prompt=context_prompt,
        system_instruction="You are CAS Legal Intelligence Officer, an autonomous legal AI expert providing rigorous legal analysis grounded in contract text."
    )

    return {
        "contract_id": contract_id,
        "question": req.question,
        "answer": answer,
        "model": gemini_service.model
    }


@router.post("/{contract_id}/analyze")
async def trigger_mesh_analysis(
    contract_id: str,
    objective: Optional[str] = "Protect Customer liability and ensure bilateral commercial terms.",
    db: AsyncSession = Depends(get_db)
):
    """Triggers dynamic multi-society mesh orchestration for this contract."""
    contract = await db.get(ContractModel, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")

    analysis = await cas_director.orchestrate_mesh(
        contract_text=contract.raw_text,
        contract_id=contract_id,
        commercial_objective=objective,
        db_session=db
    )
    contract.status = analysis["status"]
    await db.commit()
    return analysis


@router.get("/{contract_id}/analysis")
async def get_full_analysis(contract_id: str, db: AsyncSession = Depends(get_db)):
    """Retrieves the aggregate multi-society findings."""
    graph = (await db.execute(select(ContractGraphModel).where(ContractGraphModel.contract_id == contract_id).order_by(desc(ContractGraphModel.id)).limit(1))).scalars().first()
    risk = (await db.execute(select(RiskReportModel).where(RiskReportModel.contract_id == contract_id).order_by(desc(RiskReportModel.id)).limit(1))).scalars().first()
    comp = (await db.execute(select(ComplianceReportModel).where(ComplianceReportModel.contract_id == contract_id).order_by(desc(ComplianceReportModel.id)).limit(1))).scalars().first()
    strat = (await db.execute(select(NegotiationStrategyModel).where(NegotiationStrategyModel.contract_id == contract_id).order_by(desc(NegotiationStrategyModel.id)).limit(1))).scalars().first()
    disp = (await db.execute(select(DisputeAssessmentModel).where(DisputeAssessmentModel.contract_id == contract_id).order_by(desc(DisputeAssessmentModel.id)).limit(1))).scalars().first()

    return {
        "contract_id": contract_id,
        "graph": graph.graph_json if graph else None,
        "risk_report": risk.report_json if risk else None,
        "compliance_report": comp.report_json if comp else None,
        "negotiation_strategy": strat.strategy_json if strat else None,
        "dispute_assessment": disp.assessment_json if disp else None
    }


@router.get("/{contract_id}/execution")
async def get_contract_execution(contract_id: str, db: AsyncSession = Depends(get_db)):
    """
    Returns the real-time or historical execution trace for this contract.
    If an analysis is currently running, returns live progress.
    If already analyzed, reconstructs the execution trace from stored reports.
    """
    live_exec = execution_tracker.get_execution(contract_id)
    if live_exec:
        return live_exec

    contract = await db.get(ContractModel, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")

    # Fetch stored reports to build trace
    graph_m = (await db.execute(select(ContractGraphModel).where(ContractGraphModel.contract_id == contract_id).order_by(desc(ContractGraphModel.id)).limit(1))).scalars().first()
    risk_m = (await db.execute(select(RiskReportModel).where(RiskReportModel.contract_id == contract_id).order_by(desc(RiskReportModel.id)).limit(1))).scalars().first()
    comp_m = (await db.execute(select(ComplianceReportModel).where(ComplianceReportModel.contract_id == contract_id).order_by(desc(ComplianceReportModel.id)).limit(1))).scalars().first()
    strat_m = (await db.execute(select(NegotiationStrategyModel).where(NegotiationStrategyModel.contract_id == contract_id).order_by(desc(NegotiationStrategyModel.id)).limit(1))).scalars().first()
    disp_m = (await db.execute(select(DisputeAssessmentModel).where(DisputeAssessmentModel.contract_id == contract_id).order_by(desc(DisputeAssessmentModel.id)).limit(1))).scalars().first()
    review_m = (await db.execute(select(HumanReviewModel).where(HumanReviewModel.contract_id == contract_id).order_by(desc(HumanReviewModel.id)).limit(1))).scalars().first()

    clauses_count = len(graph_m.graph_json.get("clauses", [])) if graph_m and graph_m.graph_json else 0
    obligations_count = len(graph_m.graph_json.get("obligations", [])) if graph_m and graph_m.graph_json else 0
    risk_score = risk_m.overall_score if risk_m else 0.0
    risk_findings_count = len(risk_m.report_json.get("findings", [])) if risk_m and risk_m.report_json else 0
    comp_status = comp_m.overall_status if comp_m else "COMPLIANT"
    comp_viols = comp_m.report_json.get("violations_count", 0) if comp_m and comp_m.report_json else 0
    neg_positions_count = len(strat_m.strategy_json.get("positions", [])) if strat_m and strat_m.strategy_json else 0
    disp_risk = disp_m.overall_dispute_risk if disp_m else "MODERATE"
    is_paused = review_m and review_m.status == "PENDING"

    stages = execution_tracker._get_initial_stages()

    # Populate stages based on stored records
    if graph_m:
        stages[1]["status"] = "COMPLETED"
        stages[1]["summary"] = f"{clauses_count} clauses, {obligations_count} obligations extracted"
        for ag in stages[1]["agents"]:
            ag["status"] = "COMPLETED"
            if ag["id"] == "clause_extractor":
                ag["result_summary"] = f"{clauses_count} clauses extracted"
            elif ag["id"] == "obligation_extractor":
                ag["result_summary"] = f"{obligations_count} obligations identified"
            elif ag["id"] == "doc_parser":
                ag["result_summary"] = "Structure extracted"
            elif ag["id"] == "entity_extractor":
                ag["result_summary"] = "Parties identified"
            elif ag["id"] == "contract_critic":
                ag["result_summary"] = "Graph verified"
        stages[2]["status"] = "COMPLETED"

    if risk_m:
        stages[3]["status"] = "COMPLETED"
        stages[3]["summary"] = f"Overall risk score: {risk_score:.2f}"
        for ag in stages[3]["agents"]:
            ag["status"] = "COMPLETED"
            if ag["id"] == "risk_hunter":
                ag["result_summary"] = f"{risk_findings_count} potential risks identified"
            elif ag["id"] == "legal_reasoner":
                ag["result_summary"] = "Exposure calibrated"
            elif ag["id"] == "counterargument_agent":
                ag["result_summary"] = "Defenses tested"
            elif ag["id"] == "evidence_verifier":
                ag["result_summary"] = "Supporting evidence verified"
            elif ag["id"] == "risk_synthesizer":
                ag["result_summary"] = f"Score: {(risk_score * 100):.0f}%"

    if comp_m:
        stages[4]["status"] = "COMPLETED"
        stages[4]["summary"] = f"{comp_status} ({comp_viols} violations)"
        for ag in stages[4]["agents"]:
            ag["status"] = "COMPLETED"
            if ag["id"] == "compliance_analyzer":
                ag["result_summary"] = f"{comp_status} ({comp_viols} violations)"
            elif ag["id"] == "policy_retriever":
                ag["result_summary"] = "Loaded policy rules"
            elif ag["id"] == "rule_matcher":
                ag["result_summary"] = "Rules matched"
            elif ag["id"] == "compliance_auditor":
                ag["result_summary"] = f"Status: {comp_status}"

    if strat_m:
        stages[5]["status"] = "COMPLETED"
        stages[5]["summary"] = f"{neg_positions_count} redlines formulated"
        for ag in stages[5]["agents"]:
            ag["status"] = "COMPLETED"
            if ag["id"] == "negotiation_planner":
                ag["result_summary"] = f"{neg_positions_count} redlines formulated"
            elif ag["id"] == "counterparty_simulator":
                ag["result_summary"] = "Vendor sensitivities modeled"
            elif ag["id"] == "concession_agent":
                ag["result_summary"] = "Concession packages ready"

    if disp_m:
        stages[6]["status"] = "COMPLETED"
        stages[6]["summary"] = f"Dispute risk index: {disp_risk}"
        for ag in stages[6]["agents"]:
            ag["status"] = "COMPLETED"
            if ag["id"] == "ambiguity_detector":
                ag["result_summary"] = "Ambiguity mapped"
            elif ag["id"] == "litigation_sim":
                ag["result_summary"] = f"Risk: {disp_risk}"

    if graph_m and risk_m:
        stages[7]["status"] = "COMPLETED"
        stages[7]["summary"] = "Conflict resolution and consensus synthesis completed"
        for ag in stages[7]["agents"]:
            ag["status"] = "COMPLETED"
            ag["result_summary"] = "Conflicts arbitrated"

    if is_paused:
        stages[8]["status"] = "PAUSED_FOR_HUMAN"
        stages[8]["summary"] = review_m.reason or "Critical risk requires General Counsel approval."
        overall_status = "PAUSED_FOR_HUMAN"
    elif review_m and review_m.status != "PENDING":
        stages[8]["status"] = "COMPLETED"
        stages[8]["summary"] = f"Human decision: {review_m.status}"
        overall_status = "COMPLETED"
    elif graph_m and risk_m:
        stages[8]["status"] = "COMPLETED"
        stages[8]["summary"] = "Review not required or previously resolved"
        overall_status = "COMPLETED"
    else:
        overall_status = "WAITING"

    if risk_m and risk_m.requires_escalation:
        stages[9]["status"] = "COMPLETED"
        stages[9]["summary"] = "Risk escalation delivered to Slack #legal-contract-risks"

    return {
        "execution_id": f"EXEC-{contract_id}",
        "contract_id": contract_id,
        "title": contract.title,
        "status": overall_status,
        "started_at": contract.created_at.isoformat() if contract.created_at else None,
        "completed_at": contract.updated_at.isoformat() if contract.updated_at else None,
        "current_step": None,
        "next_step": None,
        "stages": stages,
        "events": [],
    }


@router.get("/{contract_id}/execution-stream")
async def stream_contract_execution(contract_id: str):
    """
    Streams live execution events via Server-Sent Events (SSE).
    """
    async def event_generator():
        async for item in execution_tracker.subscribe_stream(contract_id):
            yield f"data: {json.dumps(item)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/{contract_id}/risks")
async def get_contract_risks(contract_id: str, db: AsyncSession = Depends(get_db)):
    rec = (await db.execute(select(RiskReportModel).where(RiskReportModel.contract_id == contract_id).order_by(desc(RiskReportModel.id)).limit(1))).scalars().first()
    if not rec:
        raise HTTPException(status_code=404, detail="Risk report not found")
    return rec.report_json


@router.get("/{contract_id}/compliance")
async def get_contract_compliance(contract_id: str, db: AsyncSession = Depends(get_db)):
    rec = (await db.execute(select(ComplianceReportModel).where(ComplianceReportModel.contract_id == contract_id).order_by(desc(ComplianceReportModel.id)).limit(1))).scalars().first()
    if not rec:
        raise HTTPException(status_code=404, detail="Compliance report not found")
    return rec.report_json


@router.get("/{contract_id}/negotiation")
async def get_contract_negotiation(contract_id: str, db: AsyncSession = Depends(get_db)):
    rec = (await db.execute(select(NegotiationStrategyModel).where(NegotiationStrategyModel.contract_id == contract_id).order_by(desc(NegotiationStrategyModel.id)).limit(1))).scalars().first()
    if not rec:
        raise HTTPException(status_code=404, detail="Negotiation strategy not found")
    return rec.strategy_json


@router.get("/{contract_id}/obligations")
async def get_contract_obligations(contract_id: str, db: AsyncSession = Depends(get_db)):
    rec = (await db.execute(select(ObligationScheduleModel).where(ObligationScheduleModel.contract_id == contract_id).order_by(desc(ObligationScheduleModel.id)).limit(1))).scalars().first()
    if not rec:
        raise HTTPException(status_code=404, detail="Obligation schedule not found")
    return rec.schedule_json


@router.get("/{contract_id}/disputes")
async def get_contract_disputes(contract_id: str, db: AsyncSession = Depends(get_db)):
    rec = (await db.execute(select(DisputeAssessmentModel).where(DisputeAssessmentModel.contract_id == contract_id).order_by(desc(DisputeAssessmentModel.id)).limit(1))).scalars().first()
    if not rec:
        raise HTTPException(status_code=404, detail="Dispute assessment not found")
    return rec.assessment_json


@router.post("/{contract_id}/sign")
async def mark_contract_signed(
    contract_id: str,
    effective_date: str = "2026-10-01",
    db: AsyncSession = Depends(get_db)
):
    """Marks a contract as signed and activates Obligation Intelligence monitoring."""
    contract = await db.get(ContractModel, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")

    contract.status = "SIGNED"
    contract.effective_date = effective_date
    await db.commit()

    schedule = await obligation_intelligence_system.register_obligations(
        contract=contract.raw_text,
        contract_id=contract_id,
        effective_date=effective_date,
        db_session=db
    )
    return {
        "status": "SIGNED",
        "contract_id": contract_id,
        "schedule": schedule.model_dump()
    }


@router.post("/{contract_id}/review")
async def submit_human_review(
    contract_id: str,
    decision: HumanDecision,
    db: AsyncSession = Depends(get_db)
):
    """Submits a human review decision and stores it into persistent CAS memory."""
    contract = await db.get(ContractModel, contract_id)
    if not contract:
        raise HTTPException(status_code=404, detail=f"Contract {contract_id} not found")

    review = await db.get(HumanReviewModel, decision.review_id)
    if review:
        review.status = decision.decision
        review.reviewer_id = decision.reviewer_id
        review.decision_notes = decision.decision_notes
        from datetime import datetime, timezone
        review.resolved_at = datetime.now(timezone.utc)
        await db.commit()

    # Store in persistent CAS memory
    await feedback_loops.record_human_decision(db, contract_id, decision)

    if decision.decision == "APPROVE":
        contract.status = "APPROVED"
        await db.commit()

    return {
        "review_id": decision.review_id,
        "contract_id": contract_id,
        "decision": decision.decision,
        "message": "Human decision recorded in persistent CAS memory and applied to lifecycle."
    }
