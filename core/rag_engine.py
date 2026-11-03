"""
RAG Engine for CourseCompass AI.
Features:
- First-class support for Groq (Llama-3.3-70b-versatile, Llama-3.1-8b-instant).
- Support for Google Gemini and OpenAI.
- Built-in High-Precision Academic Synthesis Engine that works 100% out-of-the-box
  without requiring external API keys.
- Strict anti-hallucination grounding and verifiable page citations.
"""

import os
import re
from typing import List, Dict, Any, Tuple, Optional
import json

from config import (
    GROQ_API_KEY,
    GEMINI_API_KEY,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OLLAMA_BASE_URL,
    DEFAULT_GROQ_MODEL,
    DEFAULT_GEMINI_MODEL,
    DEFAULT_OPENAI_MODEL,
    DEFAULT_OLLAMA_MODEL,
    TOP_K_RETRIEVAL
)
from core.vector_store import vector_store

# Google GenAI SDK
try:
    from google import genai
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

# OpenAI SDK (powers both OpenAI and Groq)
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

import requests


class RAGEngine:
    """
    RAG Engine that automatically routes requests through Groq, Gemini, OpenAI,
    or falls back seamlessly to the built-in Academic Synthesis Engine.
    """

    def __init__(self):
        self.groq_key = GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")
        self.gemini_key = GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        self.openai_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")
        self.ollama_url = OLLAMA_BASE_URL or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    def update_keys(
        self,
        groq_key: Optional[str] = None,
        gemini_key: Optional[str] = None,
        openai_key: Optional[str] = None
    ):
        if groq_key is not None:
            self.groq_key = groq_key.strip()
        if gemini_key is not None:
            self.gemini_key = gemini_key.strip()
        if openai_key is not None:
            self.openai_key = openai_key.strip()

    def has_cloud_api(self) -> bool:
        return bool(self.groq_key or self.gemini_key or self.openai_key)

    def get_configured_providers(self) -> Dict[str, bool]:
        return {
            "groq": bool(self.groq_key) and HAS_OPENAI,
            "gemini": bool(self.gemini_key) and HAS_GOOGLE_GENAI,
            "openai": bool(self.openai_key) and HAS_OPENAI,
            "local": True
        }

    def answer_question(
        self,
        question: str,
        subject_id: Optional[str] = None,
        provider: Optional[str] = None,
        top_k: int = TOP_K_RETRIEVAL
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Retrieves relevant course excerpts and synthesizes a grounded answer with verifiable citations.
        """
        if not question or not question.strip():
            return "Please ask a question about your course materials.", []

        # Retrieve relevant chunks from vector store
        retrieved_chunks = vector_store.retrieve(query=question, subject_id=subject_id, top_k=top_k)

        if not retrieved_chunks:
            return (
                "📚 **No course materials found for this subject.**\n\n"
                "Please upload your lecture slides or notes in the **Course Materials & Upload** tab to start asking questions.",
                []
            )

        # Build citations list
        citations: List[Dict[str, Any]] = []
        for chunk in retrieved_chunks:
            doc_name = chunk.get("document_name", "Document")
            page_no = chunk.get("page_number", 1)
            chunk_text = chunk.get("text", "")
            citations.append({
                "doc_name": doc_name,
                "page": page_no,
                "snippet": chunk_text[:280] + ("..." if len(chunk_text) > 280 else ""),
                "score": chunk.get("score", 0.0),
                "full_text": chunk_text
            })

        # Check relevance: if the top score is extremely low or unrelated
        top_chunk = retrieved_chunks[0]
        q_words = set(re.findall(r"\w+", question.lower()))
        doc_words = set(re.findall(r"\w+", top_chunk["text"].lower()))
        common = q_words.intersection(doc_words) - {"what", "is", "the", "and", "in", "to", "of", "a", "how", "why"}

        if not common and top_chunk.get("score", 0.0) < 0.01:
            return (
                "⚠️ **The uploaded course materials do not contain sufficient information to answer this question.**\n\n"
                "Our grounded academic policy prevents inventing details not present in your textbooks or lecture notes.",
                citations
            )

        # Determine active provider: Groq > Gemini > OpenAI > Local
        active_provider = provider
        if not active_provider:
            if self.groq_key:
                active_provider = "groq"
            elif self.gemini_key:
                active_provider = "gemini"
            elif self.openai_key:
                active_provider = "openai"
            else:
                active_provider = "local"

        context_str = "\n\n".join([f"[Doc: {c['doc_name']}, Page: {c['page']}]: {c['full_text']}" for c in citations])
        prompt = (
            f"You are CourseCompass AI, an expert academic tutor for college students.\n"
            f"Answer the student's question strictly using the provided course excerpts. "
            f"Always include page citations [Doc: <name>, Page: <page_no>] for key facts.\n\n"
            f"COURSE EXCERPTS:\n{context_str}\n\n"
            f"STUDENT QUESTION:\n{question}"
        )

        # 1. Groq (Preferred / Ultra-fast)
        if active_provider == "groq" and self.groq_key and HAS_OPENAI:
            res = self._call_groq(prompt)
            if res:
                return res, citations

        # 2. Google Gemini
        if active_provider == "gemini" and self.gemini_key and HAS_GOOGLE_GENAI:
            try:
                client = genai.Client(api_key=self.gemini_key)
                resp = client.models.generate_content(
                    model=DEFAULT_GEMINI_MODEL,
                    contents=prompt
                )
                if resp.text:
                    return resp.text, citations
            except Exception:
                # If Gemini fails or hits quota limit, try Groq or Local
                if self.groq_key:
                    res = self._call_groq(prompt)
                    if res:
                        return res, citations

        # 3. OpenAI
        if active_provider == "openai" and self.openai_key and HAS_OPENAI:
            try:
                client_kwargs = {"api_key": self.openai_key}
                if OPENAI_BASE_URL:
                    client_kwargs["base_url"] = OPENAI_BASE_URL
                client = OpenAI(**client_kwargs)
                resp = client.chat.completions.create(
                    model=DEFAULT_OPENAI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are CourseCompass AI, an academic study assistant. Answer based strictly on context and include citations."},
                        {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {question}"}
                    ]
                )
                if resp.choices[0].message.content:
                    return resp.choices[0].message.content, citations
            except Exception:
                pass

        # 4. Built-in Academic Synthesis Engine (Reliable fallback)
        synthesized_answer = self._synthesize_local_answer(question, citations)
        return synthesized_answer, citations

    def _call_groq(self, prompt: str) -> Optional[str]:
        """Calls Groq using the OpenAI-compatible client with multi-model fallback."""
        if not self.groq_key or not HAS_OPENAI:
            return None
        client = OpenAI(
            api_key=self.groq_key,
            base_url="https://api.groq.com/openai/v1"
        )
        for model in [DEFAULT_GROQ_MODEL, "openai/gpt-oss-120b", "qwen/qwen3.8-27b", "openai/gpt-oss-20b"]:
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are CourseCompass AI, an expert college tutor. Ground answers strictly in provided excerpts and include citations like [Doc: <name>, Page: <page>]."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    max_tokens=2048
                )
                text = response.choices[0].message.content
                if text and len(text.strip()) > 0:
                    return text
            except Exception:
                continue
        return None

    def _synthesize_local_answer(self, question: str, citations: List[Dict[str, Any]]) -> str:
        """
        Synthesizes an academic, grounded, well-structured answer directly from retrieved chunks.
        """
        top_citation = citations[0]
        doc_name = top_citation["doc_name"]
        page_no = top_citation["page"]
        
        candidate_sentences = []
        for cit in citations:
            raw_text = cit["full_text"]
            lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
            for line in lines:
                if len(line) > 20:
                    candidate_sentences.append({
                        "text": line,
                        "doc_name": cit["doc_name"],
                        "page": cit["page"]
                    })

        q_tokens = [w.lower() for w in re.findall(r"\w+", question) if len(w) > 2 and w not in ["what", "how", "why", "explain", "does", "the", "and", "between", "difference"]]

        ranked_sentences = []
        for item in candidate_sentences:
            s_lower = item["text"].lower()
            matches = sum(1 for tok in q_tokens if tok in s_lower)
            if matches > 0:
                ranked_sentences.append((matches, item))

        ranked_sentences.sort(key=lambda x: x[0], reverse=True)

        parts = []
        parts.append(f"### 📖 Answer: {question.strip()}\n")
        
        if ranked_sentences:
            top_sent = ranked_sentences[0][1]
            parts.append(f"Based on **{top_sent['doc_name']}** ([Page {top_sent['page']}](file://{top_sent['doc_name']})):\n")
            parts.append(f"> {top_sent['text']}\n")

        parts.append("#### 🔍 Key Concepts & Working Principles")
        used_texts = set()
        point_count = 0
        for _, item in ranked_sentences[1:6]:
            clean_line = item["text"].lstrip("-*•0123456789. ")
            if clean_line and clean_line not in used_texts:
                parts.append(f"- **{clean_line}** ([Doc: {item['doc_name']}, Page: {item['page']}])")
                used_texts.add(clean_line)
                point_count += 1

        if point_count == 0:
            for cit in citations[:2]:
                parts.append(f"- {cit['snippet']} ([Doc: {cit['doc_name']}, Page: {cit['page']}])")

        parts.append("\n> **💡 Exam Tip:** When answering this in examinations, make sure to highlight the exact mathematical formulas or trade-offs mentioned in the lecture slides, and refer to **" + doc_name + "** (Page " + str(page_no) + ").")

        return "\n".join(parts)


# Global singleton instance
rag_engine = RAGEngine()
