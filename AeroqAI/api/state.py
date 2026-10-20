"""Global state container for AeroqAI API services."""
import os
import sys
from pathlib import Path
from typing import Optional, List

from AeroqAI.models.document import CleanedDocument
from AeroqAI.modules.module_1_rag.document_loader import PDFDocumentLoader
from AeroqAI.modules.module_1_rag.text_cleaner import TextCleaner
from AeroqAI.modules.module_1_rag.text_chunker import TextChunker
from AeroqAI.modules.module_1_rag.embedding_generator import get_embedding_generator, BaseEmbeddingGenerator
from AeroqAI.modules.module_1_rag.vector_store import get_vector_store, BaseVectorStore
from AeroqAI.modules.module_1_rag.reranker import get_reranker, BaseReranker
from AeroqAI.modules.module_1_rag.generator import get_llm_generator, BaseLLMGenerator
from AeroqAI.modules.module_2_evaluation.evaluator import get_evaluator, BaseEvaluator
from AeroqAI.modules.module_4_experiment_tracking.tracker import ExperimentTracker
from AeroqAI.modules.module_6_debugger.debugger import RAGDebugger


class PipelineState:
    """Manages loaded document corpus and shared pipeline components."""
    def __init__(self) -> None:
        self.is_initialized = False
        self.cleaned_documents: List[CleanedDocument] = []
        self.vector_store: Optional[BaseVectorStore] = None
        self.embedder: Optional[BaseEmbeddingGenerator] = None
        self.reranker: Optional[BaseReranker] = None
        self.generator: Optional[BaseLLMGenerator] = None
        self.evaluator: Optional[BaseEvaluator] = None
        self.debugger: Optional[RAGDebugger] = None
        self.tracker: Optional[ExperimentTracker] = None

    def initialize(self, force_mock: bool = False) -> None:
        """Initialize models, load sample document, and populate vector store."""
        if self.is_initialized:
            return

        # 1. Load and clean document
        pdf_path = Path("AeroqAI/data/sample_docs/hr_policy.pdf")
        if pdf_path.exists():
            loader = PDFDocumentLoader(extract_empty_pages=False)
            pages = loader.load_file(pdf_path)
            cleaner = TextCleaner()
            self.cleaned_documents = cleaner.clean_documents(pages)
        else:
            self.cleaned_documents = []

        # 2. Components
        provider = "mock" if force_mock else "sentence-transformers"
        self.embedder = get_embedding_generator(provider=provider, model_name="all-MiniLM-L6-v2")
        
        self.vector_store = get_vector_store(store_type="memory")
        if self.cleaned_documents:
            chunker = TextChunker(chunk_size=800, chunk_overlap=60, strategy="recursive")
            chunks = chunker.chunk_documents(self.cleaned_documents)
            embedded = self.embedder.embed_chunks(chunks)
            self.vector_store.add_chunks(embedded)

        reranker_provider = "mock" if force_mock else "cross-encoder"
        self.reranker = get_reranker(provider=reranker_provider, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2")

        has_groq = bool((os.getenv("GROQ_API_KEY") or Path(".env").exists()) and not force_mock)
        gen_provider = "groq" if has_groq else "mock"
        self.generator = get_llm_generator(provider=gen_provider)

        self.evaluator = get_evaluator(provider="deterministic")

        self.debugger = RAGDebugger(
            vector_store=self.vector_store,
            embedder=self.embedder,
            generator=self.generator,
            reranker=self.reranker,
            evaluator=self.evaluator
        )

        self.tracker = ExperimentTracker(runs_dir="AeroqAI/data/runs")
        self.is_initialized = True


pipeline_state = PipelineState()
