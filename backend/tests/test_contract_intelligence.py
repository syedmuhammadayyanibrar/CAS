import pytest
from backend.systems.contract_intelligence.system import contract_intelligence_system
from backend.models.graph import ContractGraph


@pytest.mark.asyncio
async def test_contract_intelligence_standalone(test_contract_text, db_session):
    """Verifies that Contract Intelligence operates independently and outputs a normalized Contract Graph."""
    graph = await contract_intelligence_system.analyze_contract(
        contract_text=test_contract_text,
        contract_id="TEST-CTR-001",
        db_session=db_session
    )

    assert isinstance(graph, ContractGraph)
    assert graph.contract_id == "TEST-CTR-001"
    assert len(graph.clauses) > 0
    assert len(graph.parties) >= 2

    # Check key clauses extracted
    clause_types = [c.clause_type for c in graph.clauses]
    assert any("LIABILITY" in ct or "INDEMNITY" in ct or "TERMINATION" in ct for ct in clause_types)

    # Check obligations and deadlines
    assert len(graph.obligations) > 0
    assert len(graph.deadlines) > 0
