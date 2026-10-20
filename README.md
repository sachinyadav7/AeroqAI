# AeroqAI 🚀

**AI Application Evaluation, RAG Optimization & Automated Quality Assurance Platform**

AeroqAI is an enterprise-grade platform designed to evaluate, optimize, track, and debug Retrieval-Augmented Generation (RAG) and LLM-powered applications. It eliminates blind trial-and-error in AI development by providing automated configuration tuning, regression testing, and CI/CD quality gates.

---

## 📌 Key Highlights

- **Modular RAG Pipeline**: Ingestion, intelligent cleaning, recursive chunking, embedding, vector search, and generation.
- **Automated RAG Optimizer**: Grid search over chunk sizes, Top-K, embedding models, and rerankers with Pareto frontier analysis.
- **LLM-as-a-Judge Evaluation Engine**: Multi-metric evaluation including Correctness, Faithfulness, Context Relevance, and Safety.
- **Experiment Tracking**: Centralized logging of configurations, scores, latency, token usage, and cost.
- **CI/CD Quality Gates**: Automated regression detection that fails PRs when AI response quality drops.
- **Interactive RAG Debugger**: Trace inspection pinpointing exact retrieval or generation bottlenecks.

---

## ⚡ Quick Start

### 1. Installation
```bash
git clone https://github.com/sachinyadav7/AeroqAI.git
cd AeroqAI
pip install -r requirements.txt
```

### 2. Run Demos
```bash
# Module 1 - Stage 1: Document Loader Demo
python run_loader_demo.py

# Module 1 - Stage 2: Text Cleaner Demo
python run_cleaner_demo.py
```

### 3. Run Test Suite
```bash
python -m pytest -v
```

---

## 📖 Documentation & Progress

For full technical specifications, architecture diagrams, data contracts, and detailed step-by-step progress, see **[`PROJECT_PROGRESS.md`](PROJECT_PROGRESS.md)**.
