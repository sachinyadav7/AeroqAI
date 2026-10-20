"""
Module 1 — Stage 1: Document Loader

Responsible for loading PDF and text documents from disk, extracting page-by-page
text, capturing file metadata, and encapsulating the output into structured RawDocument instances.
"""

import os
from pathlib import Path
from typing import List, Union
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from AeroqAI.models.document import RawDocument, DocumentMetadata


class DocumentLoaderError(Exception):
    """Custom exception raised when document loading fails."""
    pass


class PDFDocumentLoader:
    """
    Production-ready Document Loader for PDF files.
    
    Reads PDF documents, extracts page-by-page text, tracks metadata,
    and returns a list of RawDocument models ready for Stage 2 (Text Cleaning).
    """

    def __init__(self, extract_empty_pages: bool = False):
        """
        Initialize the loader.
        
        Args:
            extract_empty_pages: If False, skips pages with zero extracted characters.
        """
        self.extract_empty_pages = extract_empty_pages

    def load_file(self, file_path: Union[str, Path]) -> List[RawDocument]:
        """
        Loads a single PDF file and returns a list of RawDocument instances (one per page).
        
        Args:
            file_path: Absolute or relative path to the target PDF file.
            
        Returns:
            List[RawDocument]: List of extracted pages wrapped as RawDocument objects.
            
        Raises:
            DocumentLoaderError: If file does not exist, is invalid, encrypted, or corrupted.
        """
        path = Path(file_path).resolve()
        
        # 1. Path & file existence validation
        if not path.exists():
            raise DocumentLoaderError(f"File not found: '{path}'")
        if not path.is_file():
            raise DocumentLoaderError(f"Path is not a file: '{path}'")
        if path.suffix.lower() != ".pdf":
            raise DocumentLoaderError(f"Unsupported file extension '{path.suffix}'. PDFDocumentLoader expects '.pdf'")
        if path.stat().st_size == 0:
            raise DocumentLoaderError(f"File is empty (0 bytes): '{path}'")

        file_size_bytes = path.stat().st_size
        file_name = path.name

        # 2. PDF Parsing via pypdf
        try:
            reader = PdfReader(str(path))
            total_pages = len(reader.pages)
            
            if total_pages == 0:
                raise DocumentLoaderError(f"PDF file contains 0 pages: '{file_name}'")

            if reader.is_encrypted:
                try:
                    # Attempt decryption with empty password
                    reader.decrypt("")
                except Exception as e:
                    raise DocumentLoaderError(f"PDF file is password-protected and could not be decrypted: '{file_name}'") from e

            raw_documents: List[RawDocument] = []
            doc_stem = path.stem.replace(" ", "_").lower()

            for page_idx, page in enumerate(reader.pages):
                page_num = page_idx + 1
                try:
                    text = page.extract_text() or ""
                except Exception as page_err:
                    text = f"[ERROR: Page text extraction failed: {str(page_err)}]"

                char_count = len(text)
                word_count = len(text.split())

                if not self.extract_empty_pages and char_count == 0:
                    continue

                metadata = DocumentMetadata(
                    source_file=file_name,
                    file_type="pdf",
                    page_number=page_num,
                    total_pages=total_pages,
                    char_count=char_count,
                    word_count=word_count,
                    file_size_bytes=file_size_bytes,
                    extra={"full_path": str(path)}
                )

                doc_id = f"doc_{doc_stem}_p{page_num}"
                raw_doc = RawDocument(
                    doc_id=doc_id,
                    content=text,
                    metadata=metadata
                )
                raw_documents.append(raw_doc)

            return raw_documents

        except PdfReadError as e:
            raise DocumentLoaderError(f"Corrupted or invalid PDF format in '{file_name}': {str(e)}") from e
        except Exception as e:
            if isinstance(e, DocumentLoaderError):
                raise e
            raise DocumentLoaderError(f"Unexpected error loading PDF '{file_name}': {str(e)}") from e

    def load_directory(self, directory_path: Union[str, Path]) -> List[RawDocument]:
        """
        Scans a directory and loads all PDF files found within it.
        
        Args:
            directory_path: Directory path to scan.
            
        Returns:
            List[RawDocument]: Aggregated list of RawDocument instances from all PDFs.
        """
        dir_path = Path(directory_path).resolve()
        if not dir_path.exists() or not dir_path.is_dir():
            raise DocumentLoaderError(f"Directory not found: '{dir_path}'")

        all_docs: List[RawDocument] = []
        pdf_files = sorted(list(dir_path.glob("*.pdf")))
        
        if not pdf_files:
            return []

        for pdf_file in pdf_files:
            try:
                docs = self.load_file(pdf_file)
                all_docs.extend(docs)
            except DocumentLoaderError as err:
                print(f"[WARNING] Skipping file '{pdf_file.name}': {err}")

        return all_docs
