"""System health, metadata, and status routes."""
from fastapi import APIRouter
from AeroqAI.api.state import pipeline_state

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/health")
def get_health():
    """Return health status, loaded models, and corpus statistics."""
    vector_count = pipeline_state.vector_store.count() if pipeline_state.vector_store else 0
    return {
        "status": "healthy",
        "service": "AeroqAI AI Evaluation & Optimization Engine",
        "version": "1.0.0",
        "initialized": pipeline_state.is_initialized,
        "models": {
            "embedder": pipeline_state.embedder.model_name if pipeline_state.embedder else None,
            "reranker": pipeline_state.reranker.model_name if pipeline_state.reranker else None,
            "generator": pipeline_state.generator.model_name if pipeline_state.generator else None,
            "evaluator": pipeline_state.evaluator.model_name if pipeline_state.evaluator else None,
        },
        "corpus": {
            "pages_loaded": len(pipeline_state.cleaned_documents),
            "vector_chunks_indexed": vector_count
        }
    }
