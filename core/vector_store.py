"""
Vector Store and Hybrid Retrieval Engine for CourseCompass AI.
Combines ChromaDB vector similarity with BM25 keyword matching for state-of-the-art
RAG retrieval tailored to academic course materials.
"""

import os
from typing import List, Dict, Any, Optional
import numpy as np
from pathlib import Path
import json

from config import CHROMA_DIR, TOP_K_RETRIEVAL

# ChromaDB sqlite3 fix for Streamlit Community Cloud (Linux)
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except Exception:
    pass

# ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMA = True
except Exception:
    HAS_CHROMA = False

# BM25
try:
    from rank_bm25 import BM25Okapi
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False


class VectorStore:
    """
    Hybrid Vector Store maintaining both dense vector embeddings (ChromaDB)
    and an inverted BM25 index for high-precision academic retrieval.
    """

    def __init__(self, persist_dir: Path = CHROMA_DIR):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = None
        self.collection = None

        # Fallback local chunks store in case Chroma isn't available or for fast BM25
        self._chunks_cache: List[Dict[str, Any]] = []
        self._cache_file = self.persist_dir / "chunks_cache.json"

        self._init_chroma()
        self._load_cache()

    def _init_chroma(self):
        if HAS_CHROMA:
            try:
                self.client = chromadb.PersistentClient(path=str(self.persist_dir))
                self.collection = self.client.get_or_create_collection(
                    name="course_materials",
                    metadata={"description": "Student course lecture notes, textbooks, and slides"}
                )
            except Exception as e:
                # If Chroma encounters any environment issue, keep self.collection as None
                self.collection = None

    def _load_cache(self):
        if self._cache_file.exists():
            try:
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    self._chunks_cache = json.load(f)
            except Exception:
                self._chunks_cache = []

    def _save_cache(self):
        try:
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(self._chunks_cache, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Adds text chunks with metadata to ChromaDB and local cache.
        """
        if not chunks:
            return 0

        # Update cache (prevent duplicate ids)
        existing_ids = {c["id"] for c in self._chunks_cache}
        for chunk in chunks:
            if chunk["id"] not in existing_ids:
                self._chunks_cache.append(chunk)
                existing_ids.add(chunk["id"])
        self._save_cache()

        # Add to ChromaDB if available
        if self.collection is not None:
            ids = [c["id"] for c in chunks]
            documents = [c["text"] for c in chunks]
            metadatas = [
                {
                    "document_id": str(c["document_id"]),
                    "document_name": str(c["document_name"]),
                    "page_number": int(c["page_number"]),
                    "subject_id": str(c["subject_id"]),
                    "chunk_index": int(c["chunk_index"])
                }
                for c in chunks
            ]
            try:
                self.collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
            except Exception:
                # Fallback to local cache index
                pass

        return len(chunks)

    def delete_document_chunks(self, document_id: str):
        """Removes all chunks belonging to a specific document."""
        self._chunks_cache = [c for c in self._chunks_cache if c.get("document_id") != document_id]
        self._save_cache()

        if self.collection is not None:
            try:
                self.collection.delete(where={"document_id": str(document_id)})
            except Exception:
                pass

    def retrieve(
        self,
        query: str,
        subject_id: Optional[str] = None,
        top_k: int = TOP_K_RETRIEVAL
    ) -> List[Dict[str, Any]]:
        """
        Retrieves top_k most relevant chunks using hybrid search:
        Vector search (ChromaDB) + BM25 keyword matching with Reciprocal Rank Fusion (RRF).
        """
        if not query.strip():
            return []

        # Filter candidate pool by subject if specified
        candidates = self._chunks_cache
        if subject_id:
            candidates = [c for c in candidates if c.get("subject_id") == subject_id]

        if not candidates:
            return []

        # 1. BM25 Search
        bm25_scores = {}
        if HAS_BM25 and len(candidates) > 0:
            tokenized_corpus = [c["text"].lower().split() for c in candidates]
            bm25 = BM25Okapi(tokenized_corpus)
            query_tokens = query.lower().split()
            scores = bm25.get_scores(query_tokens)
            for idx, c in enumerate(candidates):
                bm25_scores[c["id"]] = float(scores[idx])
        else:
            # Fallback simple keyword frequency
            for c in candidates:
                q_words = [w for w in query.lower().split() if len(w) > 2]
                text_lower = c["text"].lower()
                matches = sum(1 for w in q_words if w in text_lower)
                bm25_scores[c["id"]] = float(matches)

        # 2. Dense Vector Search (ChromaDB)
        chroma_ranks = {}
        if self.collection is not None:
            try:
                where_clause = {"subject_id": str(subject_id)} if subject_id else None
                query_args = {
                    "query_texts": [query],
                    "n_results": min(top_k * 2, len(candidates))
                }
                if where_clause:
                    query_args["where"] = where_clause

                results = self.collection.query(**query_args)
                if results and "ids" in results and len(results["ids"]) > 0:
                    ret_ids = results["ids"][0]
                    for rank, cid in enumerate(ret_ids):
                        chroma_ranks[cid] = rank + 1
            except Exception:
                pass

        # 3. Reciprocal Rank Fusion (RRF)
        # RRF score = 1 / (60 + vector_rank) + 1 / (60 + bm25_rank)
        # Sort candidates by BM25
        sorted_by_bm25 = sorted(candidates, key=lambda c: bm25_scores.get(c["id"], 0.0), reverse=True)
        bm25_ranks = {c["id"]: rank + 1 for rank, c in enumerate(sorted_by_bm25)}

        fused_scores = {}
        candidate_dict = {c["id"]: c for c in candidates}

        for cid in candidate_dict.keys():
            score = 0.0
            if cid in bm25_ranks:
                score += 1.0 / (60.0 + bm25_ranks[cid])
            if cid in chroma_ranks:
                score += 1.5 / (60.0 + chroma_ranks[cid])  # Slight weight boost for dense similarity
            fused_scores[cid] = score

        # Sort by highest fused score
        top_cids = sorted(fused_scores.keys(), key=lambda cid: fused_scores[cid], reverse=True)[:top_k]
        
        results: List[Dict[str, Any]] = []
        for cid in top_cids:
            chunk = candidate_dict[cid].copy()
            chunk["score"] = round(fused_scores[cid], 4)
            results.append(chunk)

        return results

    def get_chunk_count(self, subject_id: Optional[str] = None) -> int:
        if subject_id:
            return sum(1 for c in self._chunks_cache if c.get("subject_id") == subject_id)
        return len(self._chunks_cache)


# Global vector store instance
vector_store = VectorStore()
