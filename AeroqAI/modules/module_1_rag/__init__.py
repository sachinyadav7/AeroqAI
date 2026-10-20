"""
Module 1: RAG Engine Components.
Stage 1: Document Loading
Stage 2: Text Cleaning & Normalization
Stage 3: Text Chunking
Stage 4: Embedding Generation
Stage 5: Vector Store & Retrieval
Stage 6: Cross-Encoder Reranker
"""

from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader, DocumentLoaderError
from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner
from AeroqAI.modules.module_1_rag.text_chunker import TextChunker, TextChunkerError
from AeroqAI.modules.module_1_rag.embedding_generator import (
    BaseEmbeddingGenerator,
    DeterministicMockEmbedder,
    SentenceTransformerEmbedder,
    OpenAIEmbedder,
    EmbeddingGeneratorError,
    get_embedding_generator
)
from AeroqAI.modules.module_1_rag.vector_store import (
    BaseVectorStore,
    InMemoryVectorStore,
    PgVectorStore,
    VectorStoreError,
    get_vector_store
)
from AeroqAI.modules.module_1_rag.reranker import (
    BaseReranker,
    DeterministicMockReranker,
    CrossEncoderReranker,
    RerankerError,
    get_reranker
)
from AeroqAI.modules.module_1_rag.generator import (
    BaseLLMGenerator,
    DeterministicMockGenerator,
    OpenAIGenerator,
    get_llm_generator
)

__all__ = [
    "PDFDocumentLoader",
    "DocumentLoaderError",
    "TextCleaner",
    "TextChunker",
    "TextChunkerError",
    "BaseEmbeddingGenerator",
    "DeterministicMockEmbedder",
    "SentenceTransformerEmbedder",
    "OpenAIEmbedder",
    "EmbeddingGeneratorError",
    "get_embedding_generator",
    "BaseVectorStore",
    "InMemoryVectorStore",
    "PgVectorStore",
    "VectorStoreError",
    "get_vector_store",
    "BaseReranker",
    "DeterministicMockReranker",
    "CrossEncoderReranker",
    "RerankerError",
    "get_reranker",
    "BaseLLMGenerator",
    "DeterministicMockGenerator",
    "OpenAIGenerator",
    "get_llm_generator"
]

