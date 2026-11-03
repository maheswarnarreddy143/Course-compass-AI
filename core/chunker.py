"""
Text chunking component for CourseCompass AI.
Splits extracted document pages into semantic chunks while maintaining precise page citations and metadata.
"""

from typing import List, Dict, Any
import re
from config import CHUNK_SIZE, CHUNK_OVERLAP


class TextChunker:
    """
    Splits text pages into chunks with configurable character/word boundaries and overlap.
    """

    def __init__(self, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_document_pages(
        self,
        pages: List[Dict[str, Any]],
        doc_id: str,
        doc_name: str,
        subject_id: str
    ) -> List[Dict[str, Any]]:
        """
        Splits page text into indexed chunks while strictly preserving page numbers.
        Returns a list of chunk dictionaries:
        {
            "id": f"{doc_id}_p{page_num}_c{chunk_idx}",
            "text": str,
            "document_id": doc_id,
            "document_name": doc_name,
            "page_number": int,
            "subject_id": subject_id,
            "chunk_index": int,
            "char_count": int
        }
        """
        all_chunks: List[Dict[str, Any]] = []
        global_chunk_idx = 0

        for page in pages:
            page_num = page.get("page_number", 1)
            raw_text = page.get("text", "")
            cleaned = self._clean_text(raw_text)

            if not cleaned:
                continue

            # If the page text fits inside one chunk, keep it intact
            if len(cleaned) <= self.chunk_size:
                global_chunk_idx += 1
                all_chunks.append({
                    "id": f"{doc_id}_p{page_num}_c{global_chunk_idx}",
                    "text": cleaned,
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "page_number": page_num,
                    "subject_id": subject_id,
                    "chunk_index": global_chunk_idx,
                    "char_count": len(cleaned)
                })
                continue

            # Otherwise, split recursively by paragraphs / sentences
            sub_chunks = self._split_into_chunks(cleaned)
            for sub_text in sub_chunks:
                global_chunk_idx += 1
                all_chunks.append({
                    "id": f"{doc_id}_p{page_num}_c{global_chunk_idx}",
                    "text": sub_text,
                    "document_id": doc_id,
                    "document_name": doc_name,
                    "page_number": page_num,
                    "subject_id": subject_id,
                    "chunk_index": global_chunk_idx,
                    "char_count": len(sub_text)
                })

        return all_chunks

    def _split_into_chunks(self, text: str) -> List[str]:
        """
        Splits text with sliding window and overlap using sentence/paragraph boundaries.
        """
        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            if end >= text_len:
                chunk = text[start:].strip()
                if chunk:
                    chunks.append(chunk)
                break

            # Find reasonable break point (double newline > single newline > period > space)
            break_point = -1
            candidate_window = text[start:end]

            for delim in ["\n\n", "\n", ". ", "? ", "! ", " "]:
                last_idx = candidate_window.rfind(delim)
                if last_idx > int(self.chunk_size * 0.4):
                    break_point = start + last_idx + len(delim)
                    break

            if break_point == -1 or break_point <= start:
                break_point = end

            chunk = text[start:break_point].strip()
            if chunk:
                chunks.append(chunk)

            # Advance with overlap
            start = max(break_point - self.chunk_overlap, start + 1)

        return chunks

    @staticmethod
    def _clean_text(text: str) -> str:
        """Removes duplicate whitespace, non-printable characters, and fixes line breaks."""
        text = re.sub(r"\r\n|\r", "\n", text)
        text = re.sub(r"[ \t]+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()
