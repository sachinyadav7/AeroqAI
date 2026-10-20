"""
Module 1 — Stage 4: Embedding Generator

Transforms TextChunk instances into dense numerical vector representations (EmbeddedChunk).
Supports multiple pluggable providers:
  - Local HuggingFace / SentenceTransformers (e.g. 'all-MiniLM-L6-v2', 'bge-small-en')
  - Deterministic Mock / Hashed Embedder (for high-speed testing & CI/CD)
  - OpenAI / API-compatible Embedder
"""

import math
import hashlib
from abc import ABC, abstractmethod
from typing import List, Optional, Sequence
import numpy as np

from AeroqAI.models.chunk import TextChunk, EmbeddedChunk


class EmbeddingGeneratorError(Exception):
    """Custom exception raised when embedding generation fails."""
    pass


class BaseEmbeddingGenerator(ABC):
    """Abstract Base Class for all AeroqAI embedding providers."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of the generated embedding vectors."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name or identifier of the embedding model."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generates a dense vector embedding for a single string."""
        pass

    @abstractmethod
    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        """Generates dense vector embeddings for a sequence of strings."""
        pass

    def embed_chunks(self, chunks: Sequence[TextChunk]) -> List[EmbeddedChunk]:
        """
        Transforms a sequence of TextChunk instances into EmbeddedChunk instances.

        Args:
            chunks: List of TextChunk objects from Stage 3.

        Returns:
            List[EmbeddedChunk]: List of chunks paired with normalized vectors.
        """
        if not chunks:
            return []

        texts = [c.content for c in chunks]
        embeddings = self.embed_texts(texts)

        embedded_chunks: List[EmbeddedChunk] = []
        for chunk, emb in zip(chunks, embeddings):
            embedded_chunks.append(
                EmbeddedChunk(
                    chunk_id=chunk.chunk_id,
                    content=chunk.content,
                    embedding=emb,
                    embedding_model=self.model_name,
                    embedding_dimension=self.dimension,
                    metadata=chunk.metadata
                )
            )
        return embedded_chunks

    @staticmethod
    def cosine_similarity(vec_a: Sequence[float], vec_b: Sequence[float]) -> float:
        """Computes cosine similarity between two vectors."""
        a = np.array(vec_a, dtype=np.float32)
        b = np.array(vec_b, dtype=np.float32)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return float(np.dot(a, b) / (norm_a * norm_b))


class DeterministicMockEmbedder(BaseEmbeddingGenerator):
    """
    Lightweight, deterministic hashed embedding generator.
    
    Produces unit-normalized dense vectors without requiring model downloads or GPUs.
    Ideal for fast unit tests, offline development, and CI/CD quality gates.
    """

    def __init__(self, dimension: int = 384, model_name: str = "mock-deterministic-384"):
        if dimension <= 0:
            raise ValueError(f"Dimension must be positive, got {dimension}")
        self._dim = dimension
        self._model_name = model_name

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_text(self, text: str) -> List[float]:
        if not text:
            return [0.0] * self._dim

        # Project tokens into fixed-dimension space using multi-hash seeding
        vector = np.zeros(self._dim, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return [0.0] * self._dim

        for word in words:
            digest = hashlib.sha256(word.encode("utf-8")).digest()
            for idx in range(0, min(len(digest), 16), 2):
                bucket = int.from_bytes(digest[idx:idx+2], "big") % self._dim
                vector[bucket] += 1.0

        # L2 Normalize
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm
        return vector.tolist()

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]


class SentenceTransformerEmbedder(BaseEmbeddingGenerator):
    """
    Production-grade local embedding generator using SentenceTransformers.
    
    Compatible with HuggingFace models (e.g. 'all-MiniLM-L6-v2', 'BAAI/bge-small-en-v1.5').
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        batch_size: int = 32,
        normalize_embeddings: bool = True,
        device: Optional[str] = None
    ):
        self._model_name = model_name
        self._batch_size = batch_size
        self._normalize = normalize_embeddings
        self._device = device

        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(model_name, device=device)
            self._dim = self._model.get_sentence_embedding_dimension()
        except Exception as e:
            raise EmbeddingGeneratorError(
                f"Failed to load SentenceTransformer model '{model_name}': {e}"
            ) from e

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_text(self, text: str) -> List[float]:
        try:
            emb = self._model.encode(
                text,
                normalize_embeddings=self._normalize,
                show_progress_bar=False
            )
            return emb.tolist()
        except Exception as e:
            raise EmbeddingGeneratorError(f"Error generating embedding for text: {e}") from e

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            embeddings = self._model.encode(
                list(texts),
                batch_size=self._batch_size,
                normalize_embeddings=self._normalize,
                show_progress_bar=False
            )
            return embeddings.tolist()
        except Exception as e:
            raise EmbeddingGeneratorError(f"Error generating batch embeddings: {e}") from e


class OpenAIEmbedder(BaseEmbeddingGenerator):
    """
    Cloud-based embedding generator for OpenAI and compatible endpoints.
    """

    def __init__(
        self,
        model_name: str = "text-embedding-3-small",
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        dimension: int = 1536
    ):
        self._model_name = model_name
        self._dim = dimension

        try:
            from openai import OpenAI
            self._client = OpenAI(api_key=api_key, base_url=base_url)
        except Exception as e:
            raise EmbeddingGeneratorError(f"Failed to initialize OpenAI client: {e}") from e

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return self._model_name

    def embed_text(self, text: str) -> List[float]:
        try:
            resp = self._client.embeddings.create(input=[text], model=self._model_name)
            return resp.data[0].embedding
        except Exception as e:
            raise EmbeddingGeneratorError(f"OpenAI embedding error: {e}") from e

    def embed_texts(self, texts: Sequence[str]) -> List[List[float]]:
        if not texts:
            return []
        try:
            resp = self._client.embeddings.create(input=list(texts), model=self._model_name)
            return [item.embedding for item in resp.data]
        except Exception as e:
            raise EmbeddingGeneratorError(f"OpenAI batch embedding error: {e}") from e


def get_embedding_generator(
    provider: str = "sentence-transformers",
    model_name: Optional[str] = None,
    **kwargs
) -> BaseEmbeddingGenerator:
    """
    Factory helper to instantiate an embedding generator by provider name.

    Args:
        provider: 'sentence-transformers', 'mock', or 'openai'.
        model_name: Specific model string (optional).
        **kwargs: Provider-specific configuration options.

    Returns:
        BaseEmbeddingGenerator instance.
    """
    prov = provider.lower().strip()
    if prov in ("sentence-transformers", "sentence_transformers", "hf", "huggingface"):
        name = model_name or "all-MiniLM-L6-v2"
        return SentenceTransformerEmbedder(model_name=name, **kwargs)
    elif prov in ("mock", "deterministic", "test"):
        name = model_name or "mock-deterministic-384"
        return DeterministicMockEmbedder(model_name=name, **kwargs)
    elif prov in ("openai", "api"):
        name = model_name or "text-embedding-3-small"
        return OpenAIEmbedder(model_name=name, **kwargs)
    else:
        raise ValueError(f"Unknown embedding provider: '{provider}'. Expected 'sentence-transformers', 'mock', or 'openai'.")
