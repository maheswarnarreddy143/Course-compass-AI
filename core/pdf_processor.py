"""
PDF Text Extraction and Metadata Processing Component.
Uses PyMuPDF (fitz) with fallback to pypdf and optional pytesseract OCR for scanned pages.
Tracks exact page numbers to support verifiable academic citations.
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
import datetime

# PyMuPDF
try:
    import pymupdf
except ImportError:
    try:
        import fitz as pymupdf
    except ImportError:
        pymupdf = None

# Fallback pypdf
try:
    import pypdf
except ImportError:
    pypdf = None

# Optional OCR
try:
    import pytesseract
    from PIL import Image
    import io
    HAS_OCR_LIBS = True
except ImportError:
    HAS_OCR_LIBS = False


def _check_tesseract_available() -> bool:
    """Checks whether tesseract binary is actually executable on the host system."""
    if not HAS_OCR_LIBS:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


TESSERACT_AVAILABLE = _check_tesseract_available()


class PDFProcessor:
    """
    Extracts text, page numbers, and metadata from uploaded PDF documents.
    """

    @classmethod
    def extract_document(cls, pdf_path: Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Extracts all pages from a PDF.
        Returns:
            pages: List of dicts:
                {
                    "page_number": int (1-based),
                    "text": str,
                    "char_count": int,
                    "is_ocr": bool
                }
            metadata: Dict with file stats and PDF metadata.
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found at {pdf_path}")

        file_size_kb = round(os.path.getsize(pdf_path) / 1024, 2)
        pages: List[Dict[str, Any]] = []
        pdf_meta = {
            "filename": pdf_path.name,
            "file_size_kb": file_size_kb,
            "extracted_at": datetime.datetime.now().isoformat(),
            "extractor": "pymupdf",
            "ocr_used": False
        }

        # Try PyMuPDF first
        if pymupdf is not None:
            try:
                doc = pymupdf.open(str(pdf_path))
                pdf_meta["page_count"] = len(doc)
                pdf_meta["title"] = doc.metadata.get("title") or pdf_path.stem
                pdf_meta["author"] = doc.metadata.get("author") or "Unknown"

                for page_idx in range(len(doc)):
                    page_num = page_idx + 1
                    page = doc[page_idx]
                    page_text = page.get_text("text").strip()
                    is_ocr = False

                    # If page text is virtually empty, try OCR if available
                    if len(page_text) < 30 and TESSERACT_AVAILABLE:
                        try:
                            pix = page.get_pixmap(dpi=150)
                            img = Image.open(io.BytesIO(pix.tobytes("png")))
                            ocr_text = pytesseract.image_to_string(img).strip()
                            if len(ocr_text) > len(page_text):
                                page_text = ocr_text
                                is_ocr = True
                                pdf_meta["ocr_used"] = True
                        except Exception:
                            pass

                    pages.append({
                        "page_number": page_num,
                        "text": page_text,
                        "char_count": len(page_text),
                        "is_ocr": is_ocr
                    })

                doc.close()
                return pages, pdf_meta
            except Exception as e:
                # If pymupdf failed, proceed to pypdf fallback
                pass

        # Fallback: pypdf
        if pypdf is not None:
            try:
                reader = pypdf.PdfReader(str(pdf_path))
                pdf_meta["page_count"] = len(reader.pages)
                pdf_meta["extractor"] = "pypdf"
                pdf_meta["title"] = pdf_path.stem

                for idx, page in enumerate(reader.pages):
                    page_num = idx + 1
                    try:
                        text = (page.extract_text() or "").strip()
                    except Exception:
                        text = ""
                    pages.append({
                        "page_number": page_num,
                        "text": text,
                        "char_count": len(text),
                        "is_ocr": False
                    })
                return pages, pdf_meta
            except Exception as e:
                raise RuntimeError(f"Failed to extract PDF using both PyMuPDF and pypdf: {e}")

        raise RuntimeError("No PDF extraction library available (neither pymupdf nor pypdf installed).")
