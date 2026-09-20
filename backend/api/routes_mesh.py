from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel

from backend.database.db import get_db
from backend.director.coordinator import cas_director

router = APIRouter(prefix="/mesh", tags=["CAS Director Mesh"])


class MeshAnalysisRequest(BaseModel):
    contract_text: str
    contract_id: Optional[str] = None
    commercial_objective: Optional[str] = "Cap liability at 12 months, eliminate uncapped indemnity, and secure bilateral termination."
    policy_path: Optional[str] = None


@router.post("/analyze")
async def orchestrate_mesh(
    req: MeshAnalysisRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    COORDINATED OPERATION: CONTRACT MESH DIRECTOR
    Dynamically routes and collaborates across all required autonomous societies,
    detects cross-domain conflicts, applies feedback loops, and triggers Fastn workflows.
    """
    analysis = await cas_director.orchestrate_mesh(
        contract_text=req.contract_text,
        contract_id=req.contract_id,
        commercial_objective=req.commercial_objective or "Protect commercial terms",
        policy_path=req.policy_path,
        db_session=db
    )
    return analysis
