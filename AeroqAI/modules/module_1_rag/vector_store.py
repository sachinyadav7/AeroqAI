"""
Module 1 — Stage 5: Vector Store & Retrieval Engine

Stores EmbeddedChunk instances and executes Top-K similarity search.
Supports:
  - In-memory high-speed vectorized indexing (NumPy dot-product)
  - Metadata attribute filtering (page number, source file, custom fields)
  - Score threshold filtering
  - PostgreSQL / pgvector connector architecture
"""

import time
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Sequence
import numpy as np

from AeroqAI.models.chunk import EmbeddedChunk
from AeroqAI.models.retrieval import SearchResult, RetrievalResult
from AeroqAI.modules.module_1_rag.embedding_generator import BaseEmbeddingGenerator


class VectorStoreError(Exception):
    """Custom exception raised when vector store operations fail."""
    pass


class BaseVectorStore(ABC):
    """Abstract Base Class for all AeroqAI vector store implementations."""

    @abstractmethod
    def add_chunks(self, chunks: Sequence[EmbeddedChunk]) -> None:
        """Add embedded chunks to the vector store index."""
        pass

    @abstractmethod
    def search_vector(
        self,
        query_vector: Sequence[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Execute Top-K cosine similarity search using a dense query vector."""
        pass

    def search_text(
        self,
        query_text: str,
        embedder: BaseEmbeddingGenerator,
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> RetrievalResult:
        """
        Embeds a text query and retrieves the Top-K matching chunks.
        
        Tracks query latency and packages output into a structured RetrievalResult.
        """
        start_time = time.perf_counter()
        query_vec = embedder.embed_text(query_text)
        results = self.search_vector(
            query_vector=query_vec,
            top_k=top_k,
            score_threshold=score_threshold,
            metadata_filter=metadata_filter
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        return RetrievalResult(
            query=query_text,
            results=results,
            top_k=top_k,
            total_retrieved=len(results),
            retrieval_latency_ms=round(latency_ms, 2),
            embedding_model=embedder.model_name
        )

    @abstractmethod
    def count(self) -> int:
        """Total number of indexed vectors."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Empties all indexed vectors."""
        pass

    @abstractmethod
    def get_by_id(self, chunk_id: str) -> Optional[EmbeddedChunk]:
        """Fetch a specific chunk by its unique ID."""
        pass


class InMemoryVectorStore(BaseVectorStore):
    """
    High-performance, in-memory vectorized search index.
    
    Uses NumPy matrix multiplication for instant Top-K cosine retrieval.
    Zero external database dependencies; ideal for local development,
    hyperparameter optimization grids (Module 3), and fast unit tests.
    """

    def __init__(self):
        self._chunks: List[EmbeddedChunk] = []
        self._id_map: Dict[str, EmbeddedChunk] = {}
        self._matrix: Optional[np.ndarray] = None
        self._dimension: Optional[int] = None

    def add_chunks(self, chunks: Sequence[EmbeddedChunk]) -> None:
        if not chunks:
            return

        for chunk in chunks:
            if self._dimension is None:
                self._dimension = chunk.embedding_dimension
            elif chunk.embedding_dimension != self._dimension:
                raise VectorStoreError(
                    f"Dimension mismatch: expected {self._dimension}, got {chunk.embedding_dimension} for chunk {chunk.chunk_id}"
                )

            # Avoid duplicates by updating if already present
            if chunk.chunk_id in self._id_map:
                existing_idx = next(i for i, c in enumerate(self._chunks) if c.chunk_id == chunk.chunk_id)
                self._chunks[existing_idx] = chunk
            else:
                self._chunks.append(chunk)

            self._id_map[chunk.chunk_id] = chunk

        # Reconstruct matrix
        self._rebuild_matrix()

    def _rebuild_matrix(self) -> None:
        if not self._chunks:
            self._matrix = None
            return
        vectors = [c.embedding for c in self._chunks]
        self._matrix = np.array(vectors, dtype=np.float32)

    def search_vector(
        self,
        query_vector: Sequence[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        if self._matrix is None or len(self._chunks) == 0:
            return []

        if top_k <= 0:
            raise ValueError(f"top_k must be positive, got {top_k}")

        q_vec = np.array(query_vector, dtype=np.float32)
        if len(q_vec) != self._dimension:
            raise VectorStoreError(
                f"Query vector dimension ({len(q_vec)}) does not match index dimension ({self._dimension})"
            )

        # Compute cosine similarity (vectors are unit normalized)
        # Dot product: (N, D) @ (D,) -> (N,)
        scores = np.dot(self._matrix, q_vec)

        # Sort descending
        sorted_indices = np.argsort(-scores)

        results: List[SearchResult] = []
        rank = 1

        for idx in sorted_indices:
            score = float(scores[idx])
            chunk = self._chunks[idx]

            # Apply score threshold filter
            if score_threshold is not None and score < score_threshold:
                continue

            # Apply metadata filters
            if metadata_filter is not None and not self._matches_filter(chunk, metadata_filter):
                continue

            results.append(SearchResult(
                chunk=chunk,
                similarity_score=score,
                rank=rank
            ))
            rank += 1

            if len(results) >= top_k:
                break

        return results

    @staticmethod
    def _matches_filter(chunk: EmbeddedChunk, filters: Dict[str, Any]) -> bool:
        """Checks if a chunk matches all provided key-value metadata filter pairs."""
        meta_dict = chunk.metadata.model_dump()
        extra_dict = meta_dict.get("extra", {})

        for key, expected_val in filters.items():
            # Check top-level metadata attributes first (e.g. page_number, source_file, doc_id)
            if key in meta_dict and meta_dict[key] != expected_val:
                return False
            # Check extra metadata fields
            elif key in extra_dict and extra_dict[key] != expected_val:
                return False
            elif key not in meta_dict and key not in extra_dict:
                return False
        return True

    def count(self) -> int:
        return len(self._chunks)

    def clear(self) -> None:
        self._chunks.clear()
        self._id_map.clear()
        self._matrix = None
        self._dimension = None

    def get_by_id(self, chunk_id: str) -> Optional[EmbeddedChunk]:
        return self._id_map.get(chunk_id)

    def delete_by_id(self, chunk_id: str) -> bool:
        if chunk_id in self._id_map:
            del self._id_map[chunk_id]
            self._chunks = [c for c in self._chunks if c.chunk_id != chunk_id]
            self._rebuild_matrix()
            return True
        return False


class PgVectorStore(BaseVectorStore):
    """
    PostgreSQL with pgvector extension implementation.
    
    Designed for production deployments as specified in the AeroqAI synopsis.
    """

    def __init__(
        self,
        connection_url: str,
        table_name: str = "aeroq_embeddings",
        dimension: int = 384
    ):
        self.connection_url = connection_url
        self.table_name = table_name
        self.dimension = dimension

    def add_chunks(self, chunks: Sequence[EmbeddedChunk]) -> None:
        # SQL-based bulk insert with vector casting
        raise NotImplementedError("PgVectorStore requires active PostgreSQL connection credentials.")

    def search_vector(
        self,
        query_vector: Sequence[float],
        top_k: int = 5,
        score_threshold: Optional[float] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        raise NotImplementedError("PgVectorStore requires active PostgreSQL connection credentials.")

    def count(self) -> int:
        raise NotImplementedError()

    def clear(self) -> None:
        raise NotImplementedError()

    def get_by_id(self, chunk_id: str) -> Optional[EmbeddedChunk]:
        raise NotImplementedError()


def get_vector_store(store_type: str = "in_memory", **kwargs) -> BaseVectorStore:
    """
    Factory function for vector store initialization.
    """
    stype = store_type.lower().strip()
    if stype in ("in_memory", "memory", "local"):
        return InMemoryVectorStore()
    elif stype in ("pgvector", "postgres", "postgresql"):
        return PgVectorStore(**kwargs)
    else:
        raise ValueError(f"Unknown vector store type: '{store_type}'. Expected 'in_memory' or 'pgvector'.")
