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
├── AeroqAI/                            # Core AeroqAI Python package
│   ├── __init__.py                     # Package entry point
│   ├── models/                         # Structured Pydantic data models
│   │   ├── __init__.py
│   │   ├── document.py                 # DocumentMetadata, RawDocument, CleanedDocument
│   │   └── chunk.py                    # ChunkMetadata, TextChunk
│   ├── modules/                        # Core system modules
│   │   ├── __init__.py
│   │   └── module_1_rag/               # Module 1: Core RAG Pipeline
│   │       ├── __init__.py
│   │       ├── document_loader.py      # Stage 1: PDF ingestion & metadata extraction
│   │       ├── text_cleaner.py         # Stage 2: Normalization & cleaning engine
│   │       └── text_chunker.py         # Stage 3: Recursive & fixed-size text chunker
│   └── data/
│       └── sample_docs/
│           └── hr_policy.pdf           # 10-page enterprise test document
├── scripts/
│   └── generate_sample_pdf.py          # Script generating multi-page test PDF
└── tests/                              # Automated test suites
    ├── test_document_loader.py         # Stage 1 unit tests
    ├── test_text_cleaner.py            # Stage 2 unit tests
    └── test_text_chunker.py            # Stage 3 unit tests
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

#### 🔹 Synthetic Test Data Generation
- **File**: [`scripts/generate_sample_pdf.py`](file:///c:/Users/Admin/OneDrive/Desktop/Major-Project/scripts/generate_sample_pdf.py)
- **Tech Stack**: `reportlab`
- **Understanding & Purpose**:
  To ensure repeatable, copyright-free testing without requiring external user files, this script generates a 10-page enterprise HR Policy PDF (`AeroqAI/data/sample_docs/hr_policy.pdf`) complete with realistic corporate headings, bullet points, leave allowances, benefits, and conduct rules.

---

## 🚀 Next Stages & Roadmap

### Module 1: RAG Pipeline
- [x] **Stage 1: Document Loader** (`document_loader.py`) — *Completed & Tested*
- [x] **Stage 2: Text Cleaner & Normalizer** (`text_cleaner.py`) — *Completed & Tested*
- [x] **Stage 3: Text Chunker** (`text_chunker.py`) — *Completed & Tested*
- [ ] **Stage 4: Embedding Generator** (`embedding_generator.py`):
  - Vector representation of chunks using SentenceTransformers / HuggingFace / OpenAI models.
- [ ] **Stage 5: Vector Store & Retrieval Engine** (`vector_store.py`):
  - In-memory & `pgvector` cosine similarity search. Top-K extraction.
- [ ] **Stage 6: Reranker** (`reranker.py`):
  - Cross-Encoder score refinement.
- [ ] **Stage 7: Context Assembly & LLM Generator** (`generator.py`):
  - Prompt construction and context-augmented response generation.

### Module 2: Automated Evaluation Engine
- [ ] Ground-truth dataset schema (Question, Expected Answer, Reference Context).
- [ ] LLM-as-a-Judge scoring for **Faithfulness**, **Correctness**, and **Context Relevance**.

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
