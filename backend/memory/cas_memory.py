from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from backend.database.schema import CASMemoryModel
from backend.core.logging import get_logger

logger = get_logger("CASMemory")


class CASMemoryService:
    """
    Persistent memory service backed by PostgreSQL.
    Maintains historical memory of past contracts, human decisions, negotiation outcomes,
    resolved conflicts, and dispute precedents.
    """

    @classmethod
    async def store(
        cls,
        memory_type: str,
        content: Dict[str, Any],
        tags: Optional[List[str]] = None,
        title: Optional[str] = None,
        session: Optional[AsyncSession] = None,
        reference_id: Optional[str] = None,
    ) -> Optional[CASMemoryModel]:
        """Convenience method to persist a memory item with or without an existing db session."""
        t = title or f"{memory_type}: {content.get('event') or content.get('contract_id') or 'Memory'}"
        ref = reference_id or content.get("contract_id") or content.get("reference_id")
        try:
            if session:
                return await cls.record_memory(
                    session=session,
                    memory_type=memory_type,
                    title=t,
                    content=content,
                    reference_id=ref,
                    context_tags=tags,
                )
            else:
                from backend.database.db import AsyncSessionLocal
                async with AsyncSessionLocal() as s:
                    return await cls.record_memory(
                        session=s,
                        memory_type=memory_type,
                        title=t,
                        content=content,
                        reference_id=ref,
                        context_tags=tags,
                    )
        except Exception as e:
            logger.warning(f"Could not persist memory to database: {e}")
            return None

    @staticmethod
    async def record_memory(
        session: AsyncSession,
        memory_type: str,
        title: str,
        content: Dict[str, Any],
        reference_id: Optional[str] = None,
        context_tags: Optional[List[str]] = None,
    ) -> CASMemoryModel:
        tags_str = ",".join(context_tags) if context_tags else ""
        memory_record = CASMemoryModel(
            memory_type=memory_type,
            reference_id=reference_id,
            title=title,
            content_json=content,
            context_tags=tags_str,
        )
        session.add(memory_record)
        await session.commit()
        await session.refresh(memory_record)
        logger.info(f"Recorded CAS Memory [{memory_type}]: {title} (ID: {memory_record.id})")
        return memory_record

    @staticmethod
    async def record_human_decision(
        session: AsyncSession,
        contract_id: str,
        review_id: str,
        decision: str,
        reasoning: str,
        tags: Optional[List[str]] = None,
    ):
        return await CASMemoryService.record_memory(
            session=session,
            memory_type="DECISION",
            title=f"Human Decision on {contract_id} ({decision})",
            reference_id=review_id,
            content={
                "contract_id": contract_id,
                "review_id": review_id,
                "decision": decision,
                "reasoning": reasoning,
            },
            context_tags=(tags or []) + ["human_review", decision.lower()],
        )

    @staticmethod
    async def record_negotiation_outcome(
        session: AsyncSession,
        contract_id: str,
        objective: str,
        accepted_concessions: List[str],
        successful_strategies: List[str],
    ):
        return await CASMemoryService.record_memory(
            session=session,
            memory_type="NEGOTIATION",
            title=f"Negotiation Strategy Outcome: {contract_id}",
            reference_id=contract_id,
            content={
                "contract_id": contract_id,
                "objective": objective,
                "accepted_concessions": accepted_concessions,
                "successful_strategies": successful_strategies,
            },
            context_tags=["negotiation", "strategy", "concession"],
        )

    @staticmethod
    async def record_dispute_precedent(
        session: AsyncSession,
        contract_id: str,
        clause_topic: str,
        conflict_scenario: str,
        resolution_strategy: str,
    ):
        return await CASMemoryService.record_memory(
            session=session,
            memory_type="DISPUTE",
            title=f"Dispute Precedent: {clause_topic}",
            reference_id=contract_id,
            content={
                "contract_id": contract_id,
                "clause_topic": clause_topic,
                "conflict_scenario": conflict_scenario,
                "resolution_strategy": resolution_strategy,
            },
            context_tags=["dispute", clause_topic.lower(), "precedent"],
        )

    @staticmethod
    async def retrieve_relevant_memories(
        session: AsyncSession,
        tags: List[str],
        memory_type: Optional[str] = None,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Queries PostgreSQL for past relevant precedents matching search tags."""
        stmt = select(CASMemoryModel)
        if memory_type:
            stmt = stmt.where(CASMemoryModel.memory_type == memory_type)

        if tags:
            tag_filters = [CASMemoryModel.context_tags.ilike(f"%{t}%") for t in tags]
            stmt = stmt.where(or_(*tag_filters))

        stmt = stmt.order_by(CASMemoryModel.created_at.desc()).limit(limit)
        result = await session.execute(stmt)
        records = result.scalars().all()

        return [
            {
                "id": r.id,
                "memory_type": r.memory_type,
                "title": r.title,
                "content": r.content_json,
                "tags": r.context_tags.split(",") if r.context_tags else [],
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in records
        ]


cas_memory = CASMemoryService()
