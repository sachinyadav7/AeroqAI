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
from fastapi import FastAPI
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


@app.get("/")
def root():
    """API Root descriptor with links to OpenAPI documentation."""
    return {
        "platform": "AeroqAI",
        "tagline": "Enterprise RAG Evaluation, Optimization & Quality Governance",
        "documentation": "/docs",
        "openapi": "/openapi.json",
        "status": "online",
        "version": "1.0.0"
    }


def create_app() -> FastAPI:
    """Factory helper to obtain configured FastAPI instance."""
    return app
