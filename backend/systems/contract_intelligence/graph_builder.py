from typing import List
from backend.models.graph import ContractGraph, Party, Clause, Obligation, Deadline
from backend.systems.contract_intelligence.entity_extractor import EntityExtractionResponse
from backend.core.logging import get_logger

logger = get_logger("ContractStructureBuilder")


class ContractStructureBuilder:
    """Assembles parallel agent extractions into a strongly typed Contract Graph."""

    @staticmethod
    def build_graph(
        contract_id: str,
        title: str,
        entity_res: EntityExtractionResponse,
        clauses: List[Clause],
        obligations: List[Obligation],
        deadlines: List[Deadline],
        raw_char_count: int,
    ) -> ContractGraph:
        parties = [
            Party(
                id=f"PTY-{i+1:02d}",
                name=p.name,
                role=p.role,
                jurisdiction=p.jurisdiction,
                entity_type=p.entity_type
            )
            for i, p in enumerate(entity_res.parties)
        ]

        # Extract renewal metadata
        renewals = []
        for c in clauses:
            if c.clause_type == "RENEWAL" or "renew" in c.title.lower():
                renewals.append({
                    "clause_id": c.id,
                    "section": c.section_number,
                    "summary": c.summary or c.title,
                    "is_unusual": c.is_unusual
                })

        # Assemble dependencies between clauses and obligations
        dependencies = []
        for ob in obligations:
            if ob.clause_id:
                dependencies.append({
                    "obligation_id": ob.id,
                    "clause_ref": ob.clause_id,
                    "bound_party": ob.party_name
                })

        graph = ContractGraph(
            contract_id=contract_id,
            title=title,
            parties=parties,
            clauses=clauses,
            obligations=obligations,
            deadlines=deadlines,
            renewals=renewals,
            dependencies=dependencies,
            governing_law=entity_res.governing_law,
            effective_date=entity_res.effective_date,
            expiration_date=entity_res.expiration_date,
            raw_character_count=raw_char_count
        )

        logger.info(
            f"Built Contract Graph for {contract_id}: {len(parties)} parties, "
            f"{len(clauses)} clauses, {len(obligations)} obligations, {len(deadlines)} deadlines."
        )
        return graph
