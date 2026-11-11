from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.core.auth import authorize, verify_webhook_signature
from backend.core.config import settings
from backend.core.logging import get_logger
from backend.database.db import init_db, AsyncSessionLocal
from backend.database.schema import CASMessageModel
from backend.events.bus import event_bus
from backend.models.cas_message import CASMessage

# Import routers
from backend.api.routes_auth import router as auth_router
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
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


import os
from fastapi import HTTPException
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

_SPA_NON_HTML_PREFIXES = (
    "/api/",
    "/webhooks/",
    "/assets/",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon",
)


def _is_browser_spa_request(request: Request) -> bool:
    """
    Detects browser document navigation / page refresh / back-forward reload
    so client-side SPA routes (e.g. /contracts, /contracts/:id, /societies,
    /approvals, /automations, /memory, /demo, /evaluation) receive index.html
    instead of hitting root-mounted JSON API endpoints.
    """
    if request.method != "GET":
        return False
    path = request.url.path
    if path == "/api" or path.startswith(_SPA_NON_HTML_PREFIXES):
        return False
    accept = request.headers.get("accept", "").lower()
    sec_dest = request.headers.get("sec-fetch-dest", "").lower()
    sec_mode = request.headers.get("sec-fetch-mode", "").lower()
    return "text/html" in accept or sec_dest == "document" or sec_mode == "navigate"


def _apply_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Vary"] = "Accept"
    return response


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    if _is_browser_spa_request(request) and frontend_dist:
        req_path = request.url.path.lstrip("/")
        if req_path:
            static_candidate = os.path.join(frontend_dist, req_path)
            if os.path.isfile(static_candidate):
                return _apply_security_headers(FileResponse(static_candidate))
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            resp = FileResponse(index_file)
            resp.headers["Cache-Control"] = "no-cache"
            return _apply_security_headers(resp)

    response = await call_next(request)
    return _apply_security_headers(response)


# Route mounting.
# - Auth routes are public (they issue/refresh tokens).
# - Every business router is protected by `authorize`: a valid JWT (401) plus
#   the central RBAC policy in backend/core/auth.py (403).
# - Fastn webhooks are machine-to-machine and use HMAC signature verification.
# Routers are mounted both under /api and at the root for backwards compatibility.
PROTECTED_ROUTERS = [
    contracts_router,
    systems_router,
    mesh_router,
    audit_router,
    dashboard_router,
    automations_router,
    demo_router,
    evaluation_router,
]

for _prefix in ("/api", ""):
    app.include_router(auth_router, prefix=_prefix)
    for _router in PROTECTED_ROUTERS:
        app.include_router(_router, prefix=_prefix, dependencies=[Depends(authorize)])
    app.include_router(webhooks_router, prefix=_prefix, dependencies=[Depends(verify_webhook_signature)])


@app.get("/")
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept.lower():
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

    @app.get("/icons.svg")
    async def serve_icons():
        icons = os.path.join(frontend_dist, "icons.svg")
        if os.path.exists(icons):
            return FileResponse(icons)
        raise HTTPException(status_code=404, detail="Not Found")

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

    @app.get("/{full_path:path}")
    async def serve_root_spa_fallback(full_path: str, request: Request):
        if full_path == "api" or full_path.startswith(("api/", "webhooks/")):
            raise HTTPException(status_code=404, detail="Not Found")
        target = os.path.join(frontend_dist, full_path)
        if os.path.isfile(target):
            return FileResponse(target)
        spa_prefixes = (
            "contracts",
            "approvals",
            "societies",
            "automations",
            "memory",
            "demo",
            "evaluation",
            "login",
        )
        first_seg = full_path.split("/")[0].lower()
        if _is_browser_spa_request(request) or first_seg in spa_prefixes:
            index_file = os.path.join(frontend_dist, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
        raise HTTPException(status_code=404, detail="Not Found")




if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
