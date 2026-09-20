import asyncio
import uuid
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.core.logging import get_logger
from backend.models.graph import ContractGraph
from backend.models.cas_message import CASMessage
from backend.events.bus import event_bus
from backend.systems.contract_intelligence.parser import DocumentParser
from backend.systems.contract_intelligence.clause_extractor import ClauseExtractor
from backend.systems.contract_intelligence.entity_extractor import EntityExtractor
from backend.systems.contract_intelligence.obligation_extractor import ObligationExtractor
from backend.systems.contract_intelligence.deadline_extractor import DeadlineExtractor
from backend.systems.contract_intelligence.graph_builder import ContractStructureBuilder
from backend.systems.contract_intelligence.critic import ContractCriticAgent
from backend.database.schema import ContractModel, ContractGraphModel

logger = get_logger("ContractIntelligenceSystem")


class ContractIntelligenceSystem:
    """
    SYSTEM 1 — CONTRACT INTELLIGENCE
    Architecture: Parallel + Verification Architecture
    Understands and structurally represents contracts into a normalized Contract Graph.
    Can be executed completely independently.
    """

    @classmethod
    async def analyze_contract(
        cls,
        contract_text: str,
        contract_id: Optional[str] = None,
        db_session: Optional[AsyncSession] = None,
    ) -> ContractGraph:
        cid = contract_id or f"CTR-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"Initiating Contract Intelligence analysis for {cid}...")

        # 1. Document Parsing
        parse_res = DocumentParser.parse_document(contract_text)
        sanitized_text = parse_res["raw_text"]
        title = parse_res["title"]

        # 2. Parallel Extraction: Clauses, Entities, Obligations, Deadlines
        logger.info("Executing parallel extraction agents (Clauses, Entities, Obligations, Deadlines)...")
        clauses_task = ClauseExtractor.extract_clauses(sanitized_text)
        entities_task = EntityExtractor.extract_entities(sanitized_text)
        obligations_task = ObligationExtractor.extract_obligations(sanitized_text)
        deadlines_task = DeadlineExtractor.extract_deadlines(sanitized_text)

        clauses, entity_res, obligations, deadlines = await asyncio.gather(
            clauses_task,
            entities_task,
            obligations_task,
            deadlines_task,
        )

        # 3. Assemble Normalized Contract Graph
        graph = ContractStructureBuilder.build_graph(
            contract_id=cid,
            title=title,
            entity_res=entity_res,
            clauses=clauses,
            obligations=obligations,
            deadlines=deadlines,
            raw_char_count=parse_res["char_count"]
        )

        # 4. Critic & Verification
        critic_report = await ContractCriticAgent.verify_graph(graph, sanitized_text)
        logger.info(f"Critic verified contract {cid} with confidence {critic_report.confidence_score:.2f}")

        # 5. Persist to PostgreSQL if session is provided
        if db_session:
            contract_rec = await db_session.get(ContractModel, cid)
            if not contract_rec:
                contract_rec = ContractModel(
                    id=cid,
                    title=graph.title,
                    raw_text=sanitized_text,
                    status="PARSED",
                    governing_law=graph.governing_law,
                    effective_date=graph.effective_date,
                    expiration_date=graph.expiration_date,
                    metadata_json={"critic_confidence": critic_report.confidence_score}
                )
                db_session.add(contract_rec)
            else:
                contract_rec.status = "PARSED"
                contract_rec.governing_law = graph.governing_law

            existing_graph = (await db_session.execute(
                select(ContractGraphModel).where(ContractGraphModel.contract_id == cid)
            )).scalar_one_or_none()

            if existing_graph:
                existing_graph.graph_json = graph.model_dump(mode="json")
            else:
                graph_rec = ContractGraphModel(
                    contract_id=cid,
                    graph_json=graph.model_dump(mode="json")
                )
                db_session.add(graph_rec)

            await db_session.commit()
            logger.info(f"Persisted Contract Graph {cid} in PostgreSQL.")

        # 6. Publish standardized CASMessage
        message = CASMessage.create(
            contract_id=cid,
            source_system="contract_intelligence",
            target_system="director",
            event_type="CONTRACT_PARSED",
            payload={
                "contract_id": cid,
                "title": graph.title,
                "parties": [p.model_dump(mode="json") for p in graph.parties],
                "clause_count": len(graph.clauses),
                "obligation_count": len(graph.obligations),
                "critic_valid": critic_report.is_valid,
                "confidence": critic_report.confidence_score
            },
            evidence_refs=[c.id for c in graph.clauses[:5]],
            confidence=critic_report.confidence_score,
            priority="LOW"
        )
        await event_bus.publish(message)

        return graph


contract_intelligence_system = ContractIntelligenceSystem()
