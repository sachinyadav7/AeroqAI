"""
Module 1 — Stage 6: Reranker Engine

Applies deep Cross-Encoder relevance scoring to search results retrieved by Stage 5.
Supports:
  - HuggingFace / SentenceTransformers CrossEncoder models
  - Deterministic lexical-overlap mock reranker for high-speed testing & CI/CD
  - Dynamic RAG Optimizer benchmarking (reranker ON vs OFF)
"""

import time
from abc import ABC, abstractmethod
from typing import List, Optional, Sequence
import numpy as np

from AeroqAI.models.retrieval import SearchResult, RerankedSearchResult, RerankResult


class RerankerError(Exception):
    """Custom exception raised when reranking fails."""
    pass


class BaseReranker(ABC):
    """Abstract Base Class for all AeroqAI reranking models."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier of the reranker model."""
        pass

    @abstractmethod
    def rerank(
        self,
        query: str,
        search_results: Sequence[SearchResult],
        top_k: Optional[int] = None
    ) -> RerankResult:
        """
        Re-ranks a list of SearchResults against the query.

        Args:
            query: The user query string.
            search_results: List of candidate SearchResults from Stage 5.
            top_k: Optional maximum number of top results to return.

        Returns:
            RerankResult: Structured bundle containing re-ordered chunks.
        """
        pass


class DeterministicMockReranker(BaseReranker):
    """
    Lightweight, deterministic lexical and keyword-density cross-scorer.
    
    Scores (query, passage) pairs without requiring neural model downloads or GPUs.
    Ideal for unit tests, offline development, and fast CI/CD quality gate passes.
    """

    def __init__(self, model_name: str = "mock-lexical-reranker"):
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    def rerank(
        self,
        query: str,
        search_results: Sequence[SearchResult],
        top_k: Optional[int] = None
    ) -> RerankResult:
        start_time = time.perf_counter()

        if not search_results:
            return RerankResult(
                query=query,
                results=[],
                top_k=top_k or 0,
                total_reranked=0,
                rerank_latency_ms=0.0,
                reranker_model=self._model_name
            )

        query_tokens = set(query.lower().split())
        scored: List[tuple[float, SearchResult]] = []

        for res in search_results:
            content_lower = res.chunk.content.lower()
            content_tokens = content_lower.split()
            
            if not content_tokens:
                scored.append((0.0, res))
                continue

            # Calculate token intersection ratio + exact phrase bonus
            matched_tokens = sum(1 for t in query_tokens if t in content_tokens)
            overlap_score = matched_tokens / max(1, len(query_tokens))

            # Phrase bonus if exact query substrings appear
            phrase_bonus = 0.2 if any(len(q) > 4 and q in content_lower for q in query_tokens) else 0.0

            # Composite cross-score combining bi-encoder prior and cross-token overlap
            final_score = float(0.4 * res.similarity_score + 0.6 * (overlap_score + phrase_bonus))
            scored.append((final_score, res))

        # Sort descending by rerank score
        scored.sort(key=lambda x: x[0], reverse=True)

        cutoff = top_k if (top_k is not None and top_k > 0) else len(scored)
        reranked_results: List[RerankedSearchResult] = []

        for new_idx, (r_score, orig_res) in enumerate(scored[:cutoff], start=1):
            reranked_results.append(
                RerankedSearchResult(
                    chunk=orig_res.chunk,
                    original_score=orig_res.similarity_score,
                    original_rank=orig_res.rank,
                    rerank_score=round(r_score, 4),
                    new_rank=new_idx
                )
            )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return RerankResult(
            query=query,
            results=reranked_results,
            top_k=cutoff,
            total_reranked=len(reranked_results),
            rerank_latency_ms=round(latency_ms, 2),
            reranker_model=self._model_name
        )


class CrossEncoderReranker(BaseReranker):
    """
    Production Cross-Encoder reranker using HuggingFace / SentenceTransformers.
    
    Compatible with models such as:
      - 'cross-encoder/ms-marco-MiniLM-L-6-v2'
      - 'BAAI/bge-reranker-base'
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: Optional[str] = None,
        batch_size: int = 16
    ):
        self._model_name = model_name
        self._batch_size = batch_size

        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(model_name, device=device)
        except Exception as e:
            raise RerankerError(
                f"Failed to load CrossEncoder model '{model_name}': {e}"
            ) from e

    @property
    def model_name(self) -> str:
        return self._model_name

    def rerank(
        self,
        query: str,
        search_results: Sequence[SearchResult],
        top_k: Optional[int] = None
    ) -> RerankResult:
        start_time = time.perf_counter()

        if not search_results:
            return RerankResult(
                query=query,
                results=[],
                top_k=top_k or 0,
                total_reranked=0,
                rerank_latency_ms=0.0,
                reranker_model=self._model_name
            )

        # Build cross-encoder pairs: (query, passage)
        pairs = [[query, res.chunk.content] for res in search_results]

        try:
            raw_scores = self._model.predict(
                pairs,
                batch_size=self._batch_size,
                show_progress_bar=False
            )
            # Normalize scores via sigmoid if needed
            scores = [float(s) for s in raw_scores]
        except Exception as e:
            raise RerankerError(f"CrossEncoder scoring failed: {e}") from e

        # Pair scores with original results
        scored = list(zip(scores, search_results))
        # Sort descending by rerank score
        scored.sort(key=lambda x: x[0], reverse=True)

        cutoff = top_k if (top_k is not None and top_k > 0) else len(scored)
        reranked_results: List[RerankedSearchResult] = []

        for new_idx, (r_score, orig_res) in enumerate(scored[:cutoff], start=1):
            reranked_results.append(
                RerankedSearchResult(
                    chunk=orig_res.chunk,
                    original_score=orig_res.similarity_score,
                    original_rank=orig_res.rank,
                    rerank_score=round(r_score, 4),
                    new_rank=new_idx
                )
            )

        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return RerankResult(
            query=query,
            results=reranked_results,
            top_k=cutoff,
            total_reranked=len(reranked_results),
            rerank_latency_ms=round(latency_ms, 2),
            reranker_model=self._model_name
        )


def get_reranker(
    provider: str = "mock",
    model_name: Optional[str] = None,
    **kwargs
) -> BaseReranker:
    """
    Factory helper for reranker instantiation.
    """
    prov = provider.lower().strip()
    if prov in ("cross-encoder", "cross_encoder", "hf", "sentence-transformers"):
        name = model_name or "cross-encoder/ms-marco-MiniLM-L-6-v2"
        return CrossEncoderReranker(model_name=name, **kwargs)
    elif prov in ("mock", "deterministic", "lexical", "test"):
        name = model_name or "mock-lexical-reranker"
        return DeterministicMockReranker(model_name=name)
    else:
        raise ValueError(
            f"Unknown reranker provider: '{provider}'. Expected 'cross-encoder' or 'mock'."
        )
