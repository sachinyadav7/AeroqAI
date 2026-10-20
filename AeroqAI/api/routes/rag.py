"""RAG query execution routes."""
import time
from fastapi import APIRouter, HTTPException
from AeroqAI.api.schemas import QueryRequest, QueryResponse
from AeroqAI.api.state import pipeline_state

router = APIRouter(prefix="/api/rag", tags=["RAG Pipeline"])


@router.post("/query", response_model=QueryResponse)
def execute_query(req: QueryRequest):
    """Execute a query through the full RAG pipeline (retrieve -> rerank -> generate)."""
    if not pipeline_state.is_initialized:
        raise HTTPException(status_code=503, detail="Pipeline state not initialized")

    start_time = time.perf_counter()

    # Step 1: Retrieval
    retrieval_res = pipeline_state.vector_store.search_text(
        query_text=req.query,
        embedder=pipeline_state.embedder,
        top_k=req.top_k
    )

    # Step 2: Rerank
    active_results = retrieval_res
    if req.use_reranker and pipeline_state.reranker:
        rerank_res = pipeline_state.reranker.rerank(
            query=req.query,
            search_results=retrieval_res,
            top_k=req.reranker_top_k
        )
        active_results = rerank_res

    # Step 3: Generate
    gen_result = pipeline_state.generator.generate(
        query=req.query,
        context=active_results
    )

    latency_ms = (time.perf_counter() - start_time) * 1000.0

    return QueryResponse(
        query=req.query,
        answer=gen_result.answer,
        sources=gen_result.sources,
        latency_ms=round(latency_ms, 2),
        model_name=pipeline_state.generator.model_name,
        provider=pipeline_state.generator.provider
    )
