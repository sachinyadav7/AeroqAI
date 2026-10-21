"""System health, metadata, and status routes."""
import shutil
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException
from AeroqAI.api.state import pipeline_state

router = APIRouter(prefix="/api/system", tags=["System"])


@router.get("/health")
def get_health():
    """Return health status, loaded models, and corpus statistics."""
    vector_count = pipeline_state.vector_store.count() if pipeline_state.vector_store else 0
    return {
        "status": "healthy",
        "service": "AeroqAI AI Evaluation & Optimization Engine",
        "version": "1.0.0",
        "initialized": pipeline_state.is_initialized,
        "active_document": getattr(pipeline_state, "active_document_name", "hr_policy.pdf"),
        "models": {
            "embedder": pipeline_state.embedder.model_name if pipeline_state.embedder else None,
            "reranker": pipeline_state.reranker.model_name if pipeline_state.reranker else None,
            "generator": pipeline_state.generator.model_name if pipeline_state.generator else None,
            "evaluator": pipeline_state.evaluator.model_name if pipeline_state.evaluator else None,
        },
        "corpus": {
            "pages_loaded": len(pipeline_state.cleaned_documents),
            "vector_chunks_indexed": vector_count
        }
    }


@router.get("/corpus")
def get_corpus():
    """Return detailed document pages and indexed chunks for knowledge base inspection."""
    doc_name = getattr(pipeline_state, "active_document_name", "hr_policy.pdf")
    docs = [
        {
            "page_number": getattr(getattr(d, "metadata", None), "page_number", idx + 1),
            "source_file": Path(getattr(getattr(d, "metadata", None), "source_file", doc_name)).name,
            "char_count": len(getattr(d, "content", "")),
            "preview": getattr(d, "content", "")[:300] + ("..." if len(getattr(d, "content", "")) > 300 else "")
        }
        for idx, d in enumerate(pipeline_state.cleaned_documents)
    ]
    chunks = [
        {
            "chunk_id": getattr(c, "chunk_id", f"chk_{i+1:03d}"),
            "page_number": getattr(getattr(c, "metadata", None), "page_number", 1),
            "char_count": len(getattr(c, "content", "")),
            "preview": getattr(c, "content", "")[:250] + ("..." if len(getattr(c, "content", "")) > 250 else "")
        }
        for i, c in enumerate(getattr(pipeline_state, "indexed_chunks", []))
    ]
    return {
        "document_name": doc_name,
        "total_pages": len(docs),
        "total_chunks": len(chunks),
        "documents": docs,
        "chunks": chunks
    }


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a custom PDF document, extract text pages, clean text,
    create vector embeddings, and index into the live AeroqAI pipeline.
    """
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files (.pdf) are supported for document analysis.")

    upload_dir = Path("AeroqAI/data/uploaded_docs")
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / file.filename

    try:
        with open(saved_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

    try:
        res = pipeline_state.ingest_pdf(saved_path, file.filename, clear_existing=True)
        return res
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Error ingesting PDF: {str(e)}")

