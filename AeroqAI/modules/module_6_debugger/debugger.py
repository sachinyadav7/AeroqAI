"""
Module 6: Interactive RAG Debugger.

Profiles every internal step of RAG execution for any query:
- Latency waterfall timing per stage
- Vector candidate similarity scores and ranking
- Cross-encoder rerank score shifts and pruning
- Assembled prompt inspection and token accounting
- Real-time ground truth evaluation triad
"""
import time
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from AeroqAI.models.retrieval import RetrievalResult, RerankResult
from AeroqAI.models.generation import GenerationResult
from AeroqAI.models.trace import (
    ChunkTraceItem,
    RetrievalStageTrace,
    RerankStageTrace,
    PromptAssemblyStageTrace,
    GenerationStageTrace,
    QueryExecutionTrace
)
from AeroqAI.modules.module_1_rag.embedding_generator import BaseEmbeddingGenerator
from AeroqAI.modules.module_1_rag.vector_store import BaseVectorStore
from AeroqAI.modules.module_1_rag.reranker import BaseReranker
from AeroqAI.modules.module_1_rag.generator import BaseLLMGenerator
from AeroqAI.modules.module_2_evaluation.evaluator import BaseEvaluator


class RAGDebugger:
    """
    Step-by-step diagnostic execution profiler for RAG pipelines.
    """

    def __init__(
        self,
        vector_store: BaseVectorStore,
        embedder: BaseEmbeddingGenerator,
        generator: BaseLLMGenerator,
        reranker: Optional[BaseReranker] = None,
        evaluator: Optional[BaseEvaluator] = None
    ) -> None:
        self.vector_store = vector_store
        self.embedder = embedder
        self.generator = generator
        self.reranker = reranker
        self.evaluator = evaluator

    def trace_query(
        self,
        query: str,
        ground_truth_answer: Optional[str] = None,
        top_k: int = 5,
        rerank_top_k: int = 2
    ) -> QueryExecutionTrace:
        """
        Execute query through the pipeline while profiling latency, scores, and prompts.
        """
        overall_start = time.perf_counter()
        trace_id = f"trace_{uuid.uuid4().hex[:8]}"

        # =========================================================================
        # Stage 5: Vector Retrieval
        # =========================================================================
        t_retrieval_start = time.perf_counter()
        retrieval_result: RetrievalResult = self.vector_store.search_text(
            query_text=query,
            embedder=self.embedder,
            top_k=top_k
        )
        retrieval_latency = (time.perf_counter() - t_retrieval_start) * 1000.0

        retrieval_chunk_items: List[ChunkTraceItem] = []
        for rank, res in enumerate(retrieval_result.results, start=1):
            snippet = res.chunk.content[:150]
            retrieval_chunk_items.append(
                ChunkTraceItem(
                    chunk_id=res.chunk.chunk_id,
                    source_file=res.chunk.metadata.source_file,
                    page_number=res.chunk.metadata.page_number,
                    content_snippet=snippet,
                    char_length=len(res.chunk.content),
                    initial_retrieval_score=round(res.similarity_score, 4),
                    initial_rank=rank,
                    retained_in_context=not bool(self.reranker)
                )
            )

        retrieval_stage = RetrievalStageTrace(
            top_k_requested=top_k,
            total_candidates_found=len(retrieval_chunk_items),
            retrieved_chunks=retrieval_chunk_items,
            latency_ms=round(retrieval_latency, 2)
        )

        # =========================================================================
        # Stage 6: Neural Cross-Encoder Reranking (Optional)
        # =========================================================================
        rerank_stage: Optional[RerankStageTrace] = None
        active_results = retrieval_result

        if self.reranker:
            t_rerank_start = time.perf_counter()
            rerank_result: RerankResult = self.reranker.rerank(
                query=query,
                search_results=retrieval_result,
                top_k=rerank_top_k
            )
            rerank_latency = (time.perf_counter() - t_rerank_start) * 1000.0
            active_results = rerank_result

            # Map reranked scores and calculate rank shifts
            reranked_chunk_items: List[ChunkTraceItem] = []
            reranked_dict = {
                r.chunk.chunk_id: (new_rank, r.rerank_score)
                for new_rank, r in enumerate(rerank_result.results, start=1)
            }

            for item in retrieval_chunk_items:
                if item.chunk_id in reranked_dict:
                    new_rank, rr_score = reranked_dict[item.chunk_id]
                    rank_delta = item.initial_rank - new_rank  # positive = climbed up
                    updated_item = item.model_copy(update={
                        "rerank_score": round(rr_score, 4),
                        "final_rank": new_rank,
                        "rank_delta": rank_delta,
                        "retained_in_context": True
                    })
                    reranked_chunk_items.append(updated_item)
                else:
                    # Pruned candidate
                    updated_item = item.model_copy(update={
                        "retained_in_context": False,
                        "rank_delta": None
                    })
                    reranked_chunk_items.append(updated_item)

            # Sort items by final_rank (None placed at end)
            reranked_chunk_items.sort(
                key=lambda x: (x.final_rank is None, x.final_rank or 999)
            )

            rerank_stage = RerankStageTrace(
                model_name=self.reranker.model_name,
                top_k_retained=rerank_top_k,
                reranked_chunks=reranked_chunk_items,
                latency_ms=round(rerank_latency, 2)
            )

        # =========================================================================
        # Stage 7a: Context Assembly & Prompt Construction
        # =========================================================================
        t_prompt_start = time.perf_counter()
        context_chunks = [r.chunk.content for r in active_results.results]
        total_context_chars = sum(len(c) for c in context_chunks)
        
        system_prompt = (
            "You are AeroqAI, an enterprise compliance and policy expert assistant. "
            "Answer the query strictly based on the provided document contexts. "
            "If the answer cannot be found, state clearly that the documentation does not contain it."
        )

        assembled_prompt = (
            f"Context Information:\n" +
            "\n\n---\n\n".join(context_chunks) +
            f"\n\nUser Question: {query}"
        )
        prompt_latency = (time.perf_counter() - t_prompt_start) * 1000.0

        prompt_stage = PromptAssemblyStageTrace(
            context_chunks_count=len(context_chunks),
            context_total_characters=total_context_chars,
            system_prompt=system_prompt,
            assembled_prompt_preview=assembled_prompt[:300] + ("..." if len(assembled_prompt) > 300 else ""),
            latency_ms=round(prompt_latency, 3)
        )

        # =========================================================================
        # Stage 7b: LLM Generation
        # =========================================================================
        t_gen_start = time.perf_counter()
        gen_result: GenerationResult = self.generator.generate(
            query=query,
            context=active_results
        )
        gen_latency = (time.perf_counter() - t_gen_start) * 1000.0

        citation_labels = [c.to_citation_label() for c in gen_result.sources]
        est_in_tokens = (len(system_prompt) + len(assembled_prompt)) // 4
        est_out_tokens = len(gen_result.answer) // 4

        generation_stage = GenerationStageTrace(
            provider=self.generator.provider,
            model_name=self.generator.model_name,
            generated_answer=gen_result.answer,
            source_citations=citation_labels,
            estimated_prompt_tokens=est_in_tokens,
            estimated_completion_tokens=est_out_tokens,
            latency_ms=round(gen_latency, 2)
        )

        # =========================================================================
        # Optional: Real-Time Evaluation Triad
        # =========================================================================
        eval_dict: Optional[Dict[str, Any]] = None
        if ground_truth_answer and self.evaluator:
            faith = self.evaluator.evaluate_faithfulness(
                query=query,
                generated_answer=gen_result.answer,
                contexts=context_chunks
            )
            corr = self.evaluator.evaluate_correctness(
                query=query,
                generated_answer=gen_result.answer,
                ground_truth=ground_truth_answer
            )
            prec = self.evaluator.evaluate_context_precision(
                query=query,
                contexts=context_chunks,
                ground_truth=ground_truth_answer
            )
            overall = round((faith.score + corr.score + prec.score) / 3.0, 4)

            eval_dict = {
                "faithfulness": faith.score,
                "correctness": corr.score,
                "precision": prec.score,
                "overall": overall,
                "faithfulness_reasoning": faith.reasoning,
                "correctness_reasoning": corr.reasoning
            }

        total_latency = (time.perf_counter() - overall_start) * 1000.0

        return QueryExecutionTrace(
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            query=query,
            total_latency_ms=round(total_latency, 2),
            retrieval=retrieval_stage,
            rerank=rerank_stage,
            prompt_assembly=prompt_stage,
            generation=generation_stage,
            evaluation=eval_dict
        )
