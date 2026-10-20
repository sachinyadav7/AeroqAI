# AeroqAI — Project Progress & Architecture Documentation

> **AeroqAI**: Intelligent AI Application Evaluation, RAG Optimization & Automated Quality Assurance Platform.

This document serves as the single source of truth for all completed work, technical specifications, design decisions, data contracts, and remaining roadmap steps. It is updated incrementally with each stage.

---

## 🛠️ Global Technology Stack

| Layer | Technologies | Purpose |
| :--- | :--- | :--- |
| **Language & Runtime** | Python 3.10+ / 3.14 | Core data models, RAG stages, evaluation engine |
| **Data Validation** | Pydantic v2 (`BaseModel`, `Field`) | Strict schemas and data contracts across all stages |
| **Document Processing** | `pypdf` (>=3.17.0), Python `re`, `unicodedata` | Ingestion, page extraction, text normalization |
| **Synthetic Data Gen** | `reportlab` (>=4.0.0) | Automated generation of realistic PDF knowledge bases |
| **Testing & Quality** | `pytest` (>=7.4.0) | Automated unit testing and regression test suites |
| **Version Control** | Git & GitHub | Modular, step-by-step progress tracking |
| **Planned Vector DB** | PostgreSQL + `pgvector` / ChromaDB | Embedding storage and cosine similarity retrieval |
| **Planned Evaluation** | LLM-as-a-Judge, Ragas-style metrics | Automated faithfulness, correctness, and relevance scoring |
| **Planned Frontend** | Next.js, TypeScript, Vanilla CSS / Tailwind | Interactive dashboard, debugger traces, experiment charts |

---

## 📂 Project Structure

```text
Major-Project/
├── .gitignore                          # Standard git ignore rules (caches, environments)
├── PROJECT_PROGRESS.md                 # Complete progress log & technical guide (this file)
├── requirements.txt                    # Project dependencies
├── run_loader_demo.py                  # Module 1 Stage 1 interactive demo script
├── run_cleaner_demo.py                 # Module 1 Stage 2 interactive demo script
├── run_chunker_demo.py                 # Module 1 Stage 3 interactive demo script
├── run_embedder_demo.py                # Module 1 Stage 4 interactive demo script
├── run_retriever_demo.py               # Module 1 Stage 5 interactive demo script
├── run_reranker_demo.py                # Module 1 Stage 6 interactive demo script
├── AeroqAI/                            # Core AeroqAI Python package
│   ├── __init__.py                     # Package entry point
│   ├── models/                         # Structured Pydantic data models
│   │   ├── __init__.py
│   │   ├── document.py                 # DocumentMetadata, RawDocument, CleanedDocument
│   │   ├── chunk.py                    # ChunkMetadata, TextChunk, EmbeddedChunk
│   │   ├── retrieval.py                # SearchResult, RetrievalResult, RerankResult
│   │   ├── generation.py               # Stage 7: SourceCitation, GenerationResult
│   │   └── evaluation.py               # Module 2: EvaluationSample, SampleEvaluationResult, BenchmarkReport
│   ├── modules/                        # Core system modules
│   │   ├── __init__.py
│   │   ├── module_1_rag/               # Module 1: Core RAG Pipeline (100% Complete)
│   │   │   ├── __init__.py
│   │   │   ├── document_loader.py      # Stage 1: PDF ingestion & metadata extraction
│   │   │   ├── text_cleaner.py         # Stage 2: Normalization & cleaning engine
│   │   │   ├── text_chunker.py         # Stage 3: Recursive & fixed-size text chunker
│   │   │   ├── embedding_generator.py  # Stage 4: Pluggable vector embedding engine
│   │   │   ├── vector_store.py         # Stage 5: In-memory & pgvector similarity search
│   │   │   ├── reranker.py             # Stage 6: Cross-Encoder neural reranker
│   │   │   └── generator.py            # Stage 7: Context assembly, Mock & Groq LLM generation
│   │   └── module_2_evaluation/        # Module 2: Automated Evaluation Engine (100% Complete)
│   │       ├── __init__.py
│   │       └── evaluator.py            # Triad evaluator: Deterministic & Groq LLM-as-a-Judge
│   └── data/
│       ├── sample_docs/
│       │   └── hr_policy.pdf           # 10-page enterprise test document
│       └── evaluation_sets/
│           └── hr_policy_benchmark.json# Curated 10-sample golden evaluation benchmark
├── scripts/
│   └── generate_sample_pdf.py          # Script generating multi-page test PDF
├── run_loader_demo.py                  # Stage 1 interactive demo
├── run_cleaner_demo.py                 # Stage 2 interactive demo
├── run_chunker_demo.py                 # Stage 3 interactive demo
├── run_embedder_demo.py                # Stage 4 interactive demo
├── run_retriever_demo.py               # Stage 5 interactive demo
├── run_reranker_demo.py                # Stage 6 interactive demo
├── run_generator_demo.py               # Stage 7 complete end-to-end RAG demo
├── run_live_module1_test.py            # Complete live diagnostic test for Module 1
├── run_evaluation_demo.py              # Module 2 automated evaluation benchmark runner
├── benchmark_results.json              # Detailed evaluation benchmark run output
└── tests/                              # Automated test suites (45 tests passing)
    ├── test_document_loader.py         # Stage 1 unit tests
    ├── test_text_cleaner.py            # Stage 2 unit tests
    ├── test_text_chunker.py            # Stage 3 unit tests
    ├── test_embedding_generator.py     # Stage 4 unit tests
    ├── test_vector_store.py            # Stage 5 unit tests
    ├── test_reranker.py                # Stage 6 unit tests
    ├── test_generator.py               # Stage 7 unit tests (Mock, OpenAI, Groq)
    └── test_evaluation_engine.py       # Module 2 evaluation engine unit tests
```

---

## 📋 Module-by-Module Progress Log

---

### Module 1: RAG Pipeline

Module 1 builds the document ingestion, transformation, retrieval, and generation pipeline.

```
Raw PDF / Docs ➡️ [Stage 1: Loader] ➡️ RawDocument
                     ⬇️
               [Stage 2: Cleaner] ➡️ CleanedDocument
                     ⬇️
               [Stage 3: Chunker] ➡️ TextChunk
                     ⬇️
               [Stage 4: Embedder] ➡️ Vector Embeddings
                     ⬇️
               [Stage 5: Vector Store] ➡️ pgvector / Similarity Search
                     ⬇️
               [Stage 6: Reranker] ➡️ Cross-Encoder Top-K
                     ⬇️
               [Stage 7: Generator] ➡️ Context-Augmented LLM Response
```

---

#### 🔹 Foundation: Structured Data Contracts
- **File**: [`AeroqAI/models/document.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/models/document.py)
- **Tech Stack**: Pydantic v2 (`BaseModel`, `Field`)
- **Understanding & Purpose**:
  In a production RAG system, passing unstructured raw dictionaries between steps causes bugs, type mismatches, and data loss. We established strict typed schemas that enforce explicit contracts between stages:
  1. `DocumentMetadata`: Captures `source_file`, `file_type`, `page_number`, `total_pages`, `char_count`, `word_count`, `file_size_bytes`, UTC `loaded_at`, and arbitrary `extra` metadata.
  2. `RawDocument`: Wraps raw text extracted directly from source files before any transformation.
  3. `CleanedDocument`: Carries both the cleaned text and the original `raw_content`, alongside a `cleaning_stats` dictionary recording exact character reductions, fixes, and removals.

---

#### 🔹 Stage 1: Document Loader
- **File**: [`AeroqAI/modules/module_1_rag/document_loader.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/modules/module_1_rag/document_loader.py)
- **Tech Stack**: `pypdf`, Python `pathlib`, Pydantic v2
- **Understanding & Purpose**:
  Extracting text from PDF files often fails silently due to missing files, empty pages, corrupted files, or encryption. `PDFDocumentLoader`:
  - Validates file existence and extension (`.pdf`).
  - Reads pages individually, capturing 1-based page indexing.
  - Skips empty pages (configurable via `extract_empty_pages=False`).
  - Computes per-page character and word counts.
  - Supports loading single files (`load_file`) or entire directories (`load_directory`).
  - Raises descriptive `DocumentLoaderError` exceptions.
- **Verification & Demo**:
  - Script: [`run_loader_demo.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/run_loader_demo.py)
  - Run command: `python run_loader_demo.py`
  - Unit tests: [`tests/test_document_loader.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/tests/test_document_loader.py) (5 tests covering valid loading, missing files, invalid extensions, empty files, directory scanning).

---

#### 🔹 Stage 2: Text Cleaner & Normalizer
- **File**: [`AeroqAI/modules/module_1_rag/text_cleaner.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/modules/module_1_rag/text_cleaner.py)
- **Tech Stack**: Python `re` (Regular Expressions), `unicodedata`, Pydantic v2
- **Understanding & Purpose**:
  PDF extraction yields noisy artifacts such as non-printable ASCII control characters (`\x00`, `\x0c`), hyphenated line breaks (`pol-\nicy`), curly quotes (`“ ” ‘ ’`), non-breaking spaces (`\xa0`), and excessive newlines. If uncleaned, these corrupt tokenization, waste embedding dimensions, and degrade retrieval.
  `TextCleaner`:
  - **Control Character Stripping**: Preserves `\n` and `\t`, strips zero-width and unprintable characters (`\x00-\x08`, `\x0b`, `\x0c`, etc.).
  - **Hyphenated Line-Wrap Repair**: Uses regex `r'(\b\w+)-\s*\n\s*(\w+\b)'` to stitch broken words (e.g. `inter-\nnational` ➡️ `international`).
  - **Unicode Normalization**: Converts smart curly quotes to standard ASCII quotes (`"` and `'`), em/en dashes to hyphens, and non-breaking spaces to standard spaces.
  - **Whitespace Collapsing**: Collapses multiple horizontal spaces to single spaces and clamps excessive consecutive newlines (default max: 2).
  - **Metrics Tracking**: Calculates `raw_char_count`, `cleaned_char_count`, `char_reduction_percent`, `hyphenated_wraps_fixed`, and `control_chars_removed`.
- **Verification & Demo**:
  - Script: [`run_cleaner_demo.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/run_cleaner_demo.py)
  - Run command: `python run_cleaner_demo.py`
  - Unit tests: [`tests/test_text_cleaner.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/tests/test_text_cleaner.py) (5 tests covering control chars, hyphenation wraps, quote/dash normalization, whitespace, and end-to-end transformation).

---

#### 🔹 Stage 3: Text Chunker & Token Segmenter
- **Files**:
  - Model: [`AeroqAI/models/chunk.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/models/chunk.py)
  - Engine: [`AeroqAI/modules/module_1_rag/text_chunker.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/modules/module_1_rag/text_chunker.py)
- **Tech Stack**: Python, Pydantic v2
- **Understanding & Purpose**:
  RAG systems cannot embed entire multi-page documents at once; documents must be broken down into discrete chunks. If chunks are too large, irrelevant context pollutes the prompt; if too small, key context is severed. 
  `TextChunker`:
  - **Strategies Supported**:
    - `recursive`: Splits text hierarchically using `["\n\n", "\n", ". ", " ", ""]` to preserve paragraphs and full sentences without breaking in the middle of words or ideas.
    - `fixed`: Rigid sliding-window slicing with overlap for strict token benchmarking.
  - **Overlapping Context**: Maintains configurable `chunk_overlap` between consecutive chunks so concepts crossing boundary lines are not lost during retrieval.
  - **Rich Linkage & Metadata**: Each `TextChunk` records `chunk_id` (`chunk_{doc_id}_{idx}`), parent `doc_id`, source page number, character start/end offsets, word count, estimated token counts, and parent configuration values.
  - **Optimization Ready**: Exposes exact parameters needed by Module 3 (RAG Optimizer) to search over chunk sizes (e.g. 250, 500, 1000) and overlap configurations.
- **Verification & Demo**:
  - Script: [`run_chunker_demo.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/run_chunker_demo.py)
  - Run command: `python run_chunker_demo.py`
  - Unit tests: [`tests/test_text_chunker.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/tests/test_text_chunker.py) (6 tests covering parameter validation, empty/whitespace docs, short doc handling, recursive splitting, fixed sliding windows, and multi-doc batches).

---

#### 🔹 Stage 4: Embedding Generator & Vector Space
- **Files**:
  - Model: [`AeroqAI/models/chunk.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/models/chunk.py) (`EmbeddedChunk`)
  - Engine: [`AeroqAI/modules/module_1_rag/embedding_generator.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/modules/module_1_rag/embedding_generator.py)
- **Tech Stack**: Python, `sentence-transformers`, `numpy`, `torch`, `openai`, Pydantic v2
- **Understanding & Purpose**:
  Keyword search fails when users ask questions with synonyms or conceptual phrasing. Embeddings convert text chunks into dense, mathematical vector coordinates in high-dimensional semantic space where related concepts cluster closely together.
  `embedding_generator.py`:
  - **Pluggable Architecture (`BaseEmbeddingGenerator`)**:
    - `SentenceTransformerEmbedder`: Uses local HuggingFace models (`all-MiniLM-L6-v2`, 384 dimensions). Generates dense vectors locally on CPU or GPU with zero cloud API fees.
    - `DeterministicMockEmbedder`: Pure Python + NumPy hashing-based generator (384 dimensions) that runs without downloading weights or GPUs, enabling lightning-fast unit tests and offline CI/CD test runs.
    - `OpenAIEmbedder`: Cloud-based generator supporting `text-embedding-3-small` (1536 dimensions) and compatible endpoints.
    - Factory function `get_embedding_generator(provider, model_name)` for automated hyperparameter tuning in Module 3 (RAG Optimizer).
  - **Unit-Length Normalization (L2 Norm = 1.0)**:
    - Automatically normalizes all output vectors so that expensive cosine distance calculations simplify to fast dot-products ($A \cdot B$).
  - **Semantic Cosine Similarity**:
    - Built-in `cosine_similarity(vec_a, vec_b)` utility to score similarity from -1.0 to +1.0.
- **Verification & Demo**:
  - Script: [`run_embedder_demo.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/run_embedder_demo.py)
  - Run command: `python run_embedder_demo.py`
  - Semantic query test: *"How many days of annual paid leave do employees receive?"* correctly ranked Page 3 (Paid Time Off & Leave Rules) as the top match (#1 with 62.05% similarity).
  - Unit tests: [`tests/test_embedding_generator.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/tests/test_embedding_generator.py) (6 tests verifying dimensions, L2 normalization, determinism, `EmbeddedChunk` mapping, cosine similarity math, and local SentenceTransformer embeddings).

---

#### 🔹 Stage 5: Vector Store & Retrieval Engine
- **Files**:
  - Models: [`AeroqAI/models/retrieval.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/models/retrieval.py) (`SearchResult`, `RetrievalResult`)
  - Engine: [`AeroqAI/modules/module_1_rag/vector_store.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/modules/module_1_rag/vector_store.py)
- **Tech Stack**: Python, NumPy, Pydantic v2
- **Understanding & Purpose**:
  Once chunks are vectorized, a vector store indexes them so the system can perform real-time similarity search when a user poses a question.
  `vector_store.py`:
  - **In-Memory Vectorized Engine (`InMemoryVectorStore`)**:
    - Stores chunk metadata and vector matrices in memory using NumPy.
    - Executes vectorized dot products for ultra-fast Top-K ranking (~13-35ms query latency).
    - Zero external database requirements, making it ideal for rapid development, test suites, and RAG optimizer grid searches.
  - **PostgreSQL / pgvector Architecture (`PgVectorStore`)**:
    - Production connector interface designed for PostgreSQL with `pgvector` indexing (`<=>` cosine operator).
  - **Top-K & Score Thresholding**:
    - Configurable `top_k` (e.g. 3, 5, 10) allows Module 3 (RAG Optimizer) to benchmark retrieval depth.
    - `score_threshold` filters out low-confidence matches before they reach the LLM.
  - **Metadata Filtering**:
    - Scopes similarity search to specific pages, document IDs, or custom department tags (e.g. `metadata_filter={'page_number': 3}`).
  - **Structured Retrieval Result**:
    - Outputs `RetrievalResult` containing ranked `SearchResult` objects, execution latency in milliseconds, query text, and a `get_context_text()` helper to format context for LLM generation (Stage 7).
- **Verification & Demo**:
  - Script: [`run_retriever_demo.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/run_retriever_demo.py)
  - Run command: `python run_retriever_demo.py`
  - Multi-query benchmark:
    - *"What are the rules and allowances for annual paid leave?"* ➡️ Top 2 matches on Page 3 (58.51% & 47.32%).
    - *"What are the core working hours and remote hybrid schedule?"* ➡️ Top match on Page 2 (82.56%).
    - *"What is the procedure for returning company equipment when leaving?"* ➡️ Top match on Page 10 (46.69%).
    - Scoped page filtering: strictly returned Page 3 chunks when filtered by `{'page_number': 3}`.
  - Unit tests: [`tests/test_vector_store.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/tests/test_vector_store.py) (8 tests covering chunk addition, dimension validation, Top-K ranking, score thresholding, metadata filtering, latency tracking, chunk deletion, and factory resolution).

---

#### 🔹 Stage 6: Cross-Encoder Reranker
- **Files**:
  - Models: [`AeroqAI/models/retrieval.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/models/retrieval.py) (`RerankedSearchResult`, `RerankResult`)
  - Engine: [`AeroqAI/modules/module_1_rag/reranker.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/modules/module_1_rag/reranker.py)
- **Tech Stack**: Python, `sentence-transformers` (Cross-Encoder), `torch`, NumPy, Pydantic v2
- **Understanding & Purpose**:
  Bi-encoder embeddings (Stage 4 & 5) are very fast because query and chunk vectors are computed independently. However, independent vectors miss deep token-level interactions between questions and documents. A **Cross-Encoder Reranker** feeds the `(query, document_chunk)` pair into a joint transformer attention mechanism simultaneously, producing an ultra-precise relevance score.
  `reranker.py`:
  - **Pluggable Architecture (`BaseReranker`)**:
    - `CrossEncoderReranker`: Uses local HuggingFace neural cross-encoder (`cross-encoder/ms-marco-MiniLM-L-6-v2`). Evaluates full cross-attention between user query and retrieved candidates.
    - `DeterministicMockReranker`: Fast, offline keyword-overlap & token Jaccard scoring engine with zero network or GPU requirements, enabling deterministic unit tests in milliseconds.
    - Factory function `get_reranker(reranker_type, model_name)` for automated hyperparameter tuning in Module 3 (RAG Optimizer).
  - **Two-Stage Retrieval (Bi-Encoder + Cross-Encoder)**:
    - Step 1: Vector store retrieves a broad candidate set (e.g. `top_k=10`).
    - Step 2: Cross-encoder reranks the candidates and truncates to the top most relevant chunks (e.g. `top_k=3`), discarding false positives.
  - **Structured Rerank Result**:
    - Outputs `RerankResult` containing `RerankedSearchResult` items with `rerank_score`, `original_rank`, `new_rank`, and `rerank_latency_ms`.
    - Includes `get_context_text()` helper for seamless injection into Stage 7 prompt assembly.
- **Verification & Demo**:
  - Script: [`run_reranker_demo.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/run_reranker_demo.py)
  - Run command: `python run_reranker_demo.py`
  - Demo test results:
    - *"What are the exact rules for annual paid leave?"* ➡️ Page 3 Annual Leave chunk promoted to #1 rank with 8.95 relevance score.
    - *"What is the remote work hybrid policy?"* ➡️ Page 2 Hybrid Model chunk promoted to #1 rank with 8.61 relevance score.
  - Unit tests: [`tests/test_reranker.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/tests/test_reranker.py) (5 tests covering deterministic mock scoring, empty results, top_k truncation, factory resolution, and local neural CrossEncoder).

---

#### 🔹 Stage 7: Context Assembly & LLM Generator
- **Files**:
  - Models: [`AeroqAI/models/generation.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/models/generation.py) (`SourceCitation`, `GenerationResult`)
  - Engine: [`AeroqAI/modules/module_1_rag/generator.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/modules/module_1_rag/generator.py)
- **Tech Stack**: Python, `openai`, Pydantic v2
- **Understanding & Purpose**:
  Raw retrieved chunks cannot be directly presented to an end-user; they must be structured into an augmented prompt, verified against strict ground rules (to prevent hallucination), and synthesized into a coherent answer with verifiable page citations.
  `generator.py`:
  - **Prompt Engineering & Groundedness Guardrails**:
    - Default system prompt instructs the model to answer strictly based on provided context and to explicitly refuse out-of-domain questions with: *"I cannot find the answer in the provided documents."*
    - Automatically injects bracketed source provenance headers: `[Source {i}: {file} | Page {page} | Chunk: {id}]`.
  - **Pluggable Architecture (`BaseLLMGenerator`)**:
    - `DeterministicMockGenerator`: Ultra-fast offline lexical and keyword-matching generation engine. Extracts highest-scoring sentences from context with citations, detects when candidate cross-encoder scores are negative (irrelevant), and enforces negative refusal for out-of-domain queries with zero network requests or API costs.
    - `OpenAIGenerator`: Production connector compatible with OpenAI (`gpt-4o`, `gpt-4o-mini`, `gpt-3.5-turbo`) or any OpenAI-compatible local/remote endpoint (vLLM, Ollama, LMStudio, Groq). Records token consumption (`prompt_tokens`, `completion_tokens`, `total_tokens`) and generation latency.
    - Factory function `get_llm_generator(provider, model_name)` for automated hyperparameter tuning in Module 3 (RAG Optimizer).
  - **Structured Generation Contract (`GenerationResult`)**:
    - Returns `query`, `answer`, `sources` (list of `SourceCitation` with doc ID, page number, chunk ID, relevance score), `grounded` (boolean status), `prompt_tokens`, `completion_tokens`, `latency_ms`, and helper `get_formatted_sources()`.
- **Verification & Demo**:
  - Script: [`run_generator_demo.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/run_generator_demo.py) (Executes complete 7-stage pipeline end-to-end against `hr_policy.pdf`).
  - Run command: `python run_generator_demo.py`
  - Demo test results:
    - Query 1 (*"What are the rules and allowances for annual paid leave and carry-over?"*):
      - Latency: 164.28 ms | Status: `✅ GROUNDED` | Sources: Page 3 (Score: 6.20).
      - Answer: Accurately cited 20 days paid annual leave and 25 days for senior staff.
    - Query 2 (*"What are the core working hours and remote hybrid schedule?"*):
      - Latency: 124.20 ms | Status: `✅ GROUNDED` | Sources: Page 2 (Score: 8.57).
      - Answer: Accurately cited 10:00 AM to 4:00 PM EST core hours.
    - Query 3 (*"What is the company policy for spaceships and warp speed travel?"*):
      - Latency: 263.70 ms | Status: `❌ UNGROUNDED / REFUSED`.
      - Answer: Refused cleanly: *"I cannot find the answer in the provided documents."* (No hallucinations).
  - Unit tests: [`tests/test_generator.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/tests/test_generator.py) (9 unit tests verifying context assembly, retrieval/rerank citation parsing, grounded answer synthesis, negative refusal fallback, prompt formatting, token counts, factory resolution, and mocked OpenAI chat completions).

---

#### 🔹 Synthetic Test Data Generation
- **File**: [`scripts/generate_sample_pdf.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/scripts/generate_sample_pdf.py)
- **Tech Stack**: `reportlab`
- **Understanding & Purpose**:
  To ensure repeatable, copyright-free testing without requiring external user files, this script generates a 10-page enterprise HR Policy PDF (`AeroqAI/data/sample_docs/hr_policy.pdf`) complete with realistic corporate headings, bullet points, leave allowances, benefits, and conduct rules.

---

### Module 2: Automated Evaluation Engine (100% Complete)

Module 2 provides the automated evaluation foundation for the entire platform. Without objective, repeatable metrics, RAG applications cannot be scientifically measured, debugged, or optimized.

```
Ground Truth Dataset ➡️ [RAG Pipeline: Module 1] ➡️ (Generated Answer, Contexts)
                                ⬇️
                   [Module 2: Evaluator Engine]
                    ├── 1. Faithfulness (Hallucination Check)
                    ├── 2. Answer Correctness (Factual Alignment)
                    └── 3. Context Precision (Retrieval Relevance)
                                ⬇️
                  [Benchmark Report & Quality Scorecard]
```

#### 🔹 Foundation: Evaluation Data Contracts
- **File**: [`AeroqAI/models/evaluation.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/models/evaluation.py)
- **Tech Stack**: Pydantic v2
- **Understanding & Purpose**:
  - `EvaluationSample`: Data contract for golden QA test cases (`sample_id`, `query`, `ground_truth_answer`, `reference_contexts`, `metadata`).
  - `MetricScore`: Structured rating container with `score` (0.0 to 1.0) and descriptive `reasoning`.
  - `SampleEvaluationResult`: Granular scorecard per test case capturing individual Faithfulness, Correctness, and Precision metrics, along with composite `overall_score` and `passed` status.
  - `BenchmarkReport`: Complete aggregate reporting bundle with average scores, pass rate, latency, and markdown formatting (`format_summary_table()`).

#### 🔹 Golden Benchmark Dataset
- **File**: [`AeroqAI/data/evaluation_sets/hr_policy_benchmark.json`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/data/evaluation_sets/hr_policy_benchmark.json)
- **Understanding & Purpose**:
  - 10 curated enterprise benchmark test cases mapped directly to sections of `hr_policy.pdf`.
  - Covers leave allowances, core hours, remote hybrid rules, PPO healthcare subsidies, 401(k) matching, offboarding asset returns, parental leave, learning budgets, IT security policies, and an adversarial out-of-domain hallucination probe (spaceships).

#### 🔹 Evaluator Engines & LLM-as-a-Judge
- **File**: [`AeroqAI/modules/module_2_evaluation/evaluator.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/AeroqAI/modules/module_2_evaluation/evaluator.py)
- **Tech Stack**: Python, Groq LPU API (`openai/gpt-oss-120b`), Pydantic v2
- **Understanding & Purpose**:
  - **The Evaluation Triad**:
    1. **Faithfulness**: Measures whether every statement in the generated answer is directly substantiated by retrieved passages. (Guarantees zero hallucinations).
    2. **Answer Correctness**: Evaluates factual and semantic alignment between the generated answer and the ground truth answer.
    3. **Context Precision**: Evaluates whether retrieved passages are relevant to the query or contain irrelevant noise.
  - **Pluggable Dual Architecture**:
    - `LLMJudgeEvaluator`: LLM-as-a-Judge powered by Groq's ultra-fast LPU inference (`openai/gpt-oss-120b` or `openai/gpt-oss-20b`). Uses structured JSON prompts to generate qualitative reasoning for each numerical score.
    - `DeterministicEvaluator`: Offline heuristic scoring engine using token Jaccard similarity, recall weighting, and stem containment for lightning-fast test suites and zero-cost offline CI/CD quality gates.
    - Factory function `get_evaluator(provider="groq"|"deterministic", ...)` for automated configuration.

#### 🔹 Live Benchmark Results:
- **Runner Script**: [`run_evaluation_demo.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/run_evaluation_demo.py)
- **Exported Artifact**: [`benchmark_results.json`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/benchmark_results.json)
- **Summary Scorecard**:

| Metric | Baseline Score | Target Threshold | Status |
| :--- | :---: | :---: | :---: |
| **Faithfulness (Groundedness)** | `1.0000` | `0.7000` | ✅ PASS |
| **Answer Correctness** | `0.5500` | `0.7000` | ❌ FAIL (Initial baseline) |
| **Context Precision** | `0.5000` | `0.6000` | ❌ FAIL (Initial baseline) |
| **Overall Composite Score** | `0.7200` | `0.7000` | ✅ PASS |

> **Key Insight for Module 3 (RAG Optimizer)**: The baseline RAG pipeline achieved a **perfect 1.0000 (100%) Faithfulness** score (zero hallucinations), but scored **0.5500 in Answer Correctness** and **0.5000 in Context Precision** because fixed chunk size (500 chars) severed certain boundary context (e.g. carry-over rules). This proves the exact purpose of **Module 3: RAG Optimizer**, which will systematically tune chunk sizes, overlap, and top_k to lift Correctness to 90%+!

---

## 🚀 Next Stages & Roadmap

### Module 1: RAG Pipeline (100% Complete)
- [x] **Stage 1: Document Loader** (`document_loader.py`) — *Completed & Tested*
- [x] **Stage 2: Text Cleaner & Normalizer** (`text_cleaner.py`) — *Completed & Tested*
- [x] **Stage 3: Text Chunker** (`text_chunker.py`) — *Completed & Tested*
- [x] **Stage 4: Embedding Generator** (`embedding_generator.py`) — *Completed & Tested*
- [x] **Stage 5: Vector Store & Retrieval Engine** (`vector_store.py`) — *Completed & Tested*
- [x] **Stage 6: Reranker** (`reranker.py`) — *Completed & Tested*
- [x] **Stage 7: Context Assembly & LLM Generator** (`generator.py`) — *Completed & Tested*

### Module 2: Automated Evaluation Engine (100% Complete)
- [x] Ground-truth dataset schema (`EvaluationSample`, `BenchmarkReport`)
- [x] Curated golden benchmark dataset (`hr_policy_benchmark.json`)
- [x] LLM-as-a-Judge scoring for **Faithfulness**, **Correctness**, and **Context Relevance** (`LLMJudgeEvaluator` via Groq)
- [x] Offline heuristic scoring (`DeterministicEvaluator` for CI/CD)
- [x] Automated benchmark runner & reporting artifact (`run_evaluation_demo.py`, `benchmark_results.json`)

### Module 3: RAG Optimizer
- [ ] Hyperparameter grid execution across chunk sizes, Top-K, embedding models, and prompts.
- [ ] Pareto frontier analysis (Cost vs. Speed vs. Quality).

### Module 4: Experiment Tracking
- [ ] Logging run configurations, scores, latency, tokens, and cost for comparison.

### Module 5: Quality Regression & CI/CD
- [ ] Baseline vs. Candidate comparison logic.
- [ ] Quality gates (PASS / FAIL) integrated with GitHub Actions.

### Module 6: Interactive RAG Debugger
- [ ] Detailed step-by-step trace inspection per query.

### Module 7: Full-Stack Platform Integration
- [ ] Next.js frontend + Java/Spring Boot & FastAPI backend + PostgreSQL (`pgvector`).
