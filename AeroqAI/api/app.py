"""
AeroqAI REST API Application.

Provides unified REST endpoints for:
- RAG Query Execution (Module 1)
- Automated Evaluation Engine (Module 2)
- Hyperparameter Optimizer & Pareto Frontier (Module 3)
- Experiment Tracking & Differential Comparison (Module 4)
- Quality Regression & CI/CD Gates (Module 5)
- Interactive Query Debugger (Module 6)
"""
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from AeroqAI.api.state import pipeline_state
from AeroqAI.api.routes.system import router as system_router
from AeroqAI.api.routes.rag import router as rag_router
from AeroqAI.api.routes.debugger import router as debugger_router
from AeroqAI.api.routes.evaluation import router as evaluation_router
from AeroqAI.api.routes.optimizer import router as optimizer_router
from AeroqAI.api.routes.experiments import router as experiments_router
from AeroqAI.api.routes.quality_gate import router as quality_gate_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager: initialize shared RAG models on startup."""
    pipeline_state.initialize()
    yield


app = FastAPI(
    title="AeroqAI REST Platform API",
    description="Enterprise Platform for AI Application Evaluation, RAG Optimization, and Quality Assurance.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Next.js frontend and local dev clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register route modules
app.include_router(system_router)
app.include_router(rag_router)
app.include_router(debugger_router)
app.include_router(evaluation_router)
app.include_router(optimizer_router)
app.include_router(experiments_router)
app.include_router(quality_gate_router)


# Resolve frontend dist path
dist_path = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
assets_path = dist_path / "assets"

if assets_path.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/assets", StaticFiles(directory=str(assets_path)), name="frontend_assets")


@app.get("/")
async def root(request: Request):
    """
    API Root descriptor or Web Application SPA depending on Accept header.
    Returns index.html when accessed from a web browser, and JSON metadata
    when requested by API clients / test runners.
    """
    accept = request.headers.get("accept", "")
    index_file = dist_path / "index.html"
    if "text/html" in accept and index_file.exists():
        return FileResponse(index_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})

    return {
        "platform": "AeroqAI",
        "tagline": "Enterprise RAG Evaluation, Optimization & Quality Governance",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "status": "online",
        "version": "1.0.0"
    }


@app.get("/app")
@app.get("/ui")
async def serve_ui():
    """Explicit endpoint to serve the React Web Application."""
    index_file = dist_path / "index.html"
    if index_file.exists():
        return FileResponse(index_file, headers={"Cache-Control": "no-cache, no-store, must-revalidate"})
    return {"message": "Frontend distribution not built yet. Run 'npm run build' inside frontend/ directory."}


def create_app() -> FastAPI:
    """Factory helper to obtain configured FastAPI instance."""
    return app

