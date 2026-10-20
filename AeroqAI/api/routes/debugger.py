"""Interactive RAG Debugger query profiling routes."""
from fastapi import APIRouter, HTTPException
from AeroqAI.models.trace import QueryExecutionTrace
from AeroqAI.api.schemas import TraceRequest
from AeroqAI.api.state import pipeline_state

router = APIRouter(prefix="/api/debugger", tags=["Debugger"])


@router.post("/trace", response_model=QueryExecutionTrace)
def trace_query_execution(req: TraceRequest):
    """Execute query while profiling every internal stage (latency waterfall, scores, reranking shifts, tokens)."""
    if not pipeline_state.is_initialized or not pipeline_state.debugger:
        raise HTTPException(status_code=503, detail="Debugger service not initialized")

    # Temporarily adjust reranker based on request flag
    orig_reranker = pipeline_state.debugger.reranker
    if not req.use_reranker:
        pipeline_state.debugger.reranker = None

    try:
        trace = pipeline_state.debugger.trace_query(
            query=req.query,
            ground_truth_answer=req.ground_truth_answer,
            top_k=req.top_k,
            rerank_top_k=req.rerank_top_k
        )
        return trace
    finally:
        pipeline_state.debugger.reranker = orig_reranker
