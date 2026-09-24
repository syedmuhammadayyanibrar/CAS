from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.database.db import init_db, AsyncSessionLocal
from backend.database.schema import CASMessageModel
from backend.events.bus import event_bus
from backend.models.cas_message import CASMessage

# Import routers
from backend.api.routes_contracts import router as contracts_router
from backend.api.routes_systems import router as systems_router
from backend.api.routes_mesh import router as mesh_router
from backend.api.routes_webhooks import router as webhooks_router
from backend.api.routes_audit import router as audit_router
from backend.api.routes_dashboard import router as dashboard_router
from backend.api.routes_automations import router as automations_router
from backend.api.routes_demo import router as demo_router
from backend.api.routes_evaluation import router as evaluation_router

logger = get_logger("CASMain")


async def persist_cas_message(message: CASMessage):
    """Event bus subscriber: persists every CASMessage into PostgreSQL."""
    try:
        async with AsyncSessionLocal() as session:
            record = CASMessageModel(
                event_id=message.event_id,
                contract_id=message.contract_id,
                source_system=message.source_system,
                target_system=message.target_system,
                event_type=message.event_type,
                confidence=message.confidence,
                priority=message.priority,
                message_json=message.model_dump(mode="json")
            )
            session.add(record)
            await session.commit()
    except Exception as e:
        logger.error(f"Failed to persist CASMessage to database: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} (v{settings.VERSION})...")
    try:
        await init_db()
    except Exception as e:
        logger.error(f"init_db caught during lifespan startup: {e}")

    try:
        # Subscribe persistence logger to event bus
        event_bus.subscribe_all(persist_cas_message)
        logger.info("Subscribed database persistence to CAS event bus.")
    except Exception as e:
        logger.error(f"Event bus subscription error during lifespan: {e}")

    yield
    # Shutdown
    logger.info(f"Shutting down {settings.PROJECT_NAME}...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Federation of Independent Multi-Agent Systems for Contract Intelligence & Negotiation Mesh via Fastn.",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API route modules
app.include_router(contracts_router)
app.include_router(systems_router)
app.include_router(mesh_router)
app.include_router(webhooks_router)
app.include_router(audit_router)
app.include_router(dashboard_router)
app.include_router(automations_router)
app.include_router(demo_router)
app.include_router(evaluation_router)


import os
from fastapi import Request
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles


def find_frontend_dist() -> str | None:
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../public")),
        os.path.abspath("public"),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../frontend/dist")),
        os.path.abspath("frontend/dist"),
    ]
    for p in candidates:
        if os.path.exists(p) and os.path.exists(os.path.join(p, "index.html")):
            return p
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


frontend_dist = find_frontend_dist()


@app.get("/")
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if accept.startswith("text/html"):
        if frontend_dist and os.path.exists(os.path.join(frontend_dist, "index.html")):
            return FileResponse(os.path.join(frontend_dist, "index.html"))
        return RedirectResponse(url="/ui", status_code=307)

    return {
        "system": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "OPERATIONAL",
        "reasoning_provider": "Google Gemini API (Sole Provider)",
        "gemini_model": settings.GEMINI_MODEL,
        "nervous_system": "Fastn + Fastn MCP",
        "fastn_org_id": settings.FASTN_ORG_ID,
        "active_societies": [
            "Contract Intelligence (Parallel + Verification)",
            "Risk Intelligence (Adversarial Debate)",
            "Negotiation Intelligence (Planner + Simulator + Critic)",
            "Compliance Intelligence (Retrieval + Rules + Verification)",
            "Obligation Intelligence (Event-Driven Monitoring)",
            "Dispute Intelligence (Multi-Perspective Simulation + Debate)"
        ],
        "fastn_workflows": {
            "intake": settings.FASTN_INTAKE_WORKFLOW_ID,
            "risk_escalation": settings.FASTN_RISK_WORKFLOW_ID,
            "approval_dispatch": settings.FASTN_APPROVAL_WORKFLOW_ID,
            "obligation_sync": settings.FASTN_OBLIGATION_WORKFLOW_ID,
            "renewal_monitor": settings.FASTN_RENEWAL_WORKFLOW_ID
        }
    }


# Mount built React frontend static assets if present
if frontend_dist and os.path.exists(frontend_dist):
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/favicon.svg")
    @app.get("/favicon.ico")
    async def serve_favicon():
        fav = os.path.join(frontend_dist, "favicon.svg")
        if os.path.exists(fav):
            return FileResponse(fav)
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"status": "ok"}

    @app.get("/ui")
    @app.get("/ui/")
    async def serve_ui_root():
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"status": "Frontend build not found"}

    @app.get("/ui/{full_path:path}")
    async def serve_ui_spa(full_path: str):
        target = os.path.join(frontend_dist, full_path)
        if os.path.isfile(target):
            return FileResponse(target)
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"status": "Frontend build not found"}




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
