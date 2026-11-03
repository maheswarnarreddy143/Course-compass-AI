# 🎓 CourseCompass AI — College Study Assistant MVP

CourseCompass AI is an AI-powered study assistant for college students. Students upload course materials (lecture slides, textbook chapters, study notes) and ask questions. The app uses Retrieval-Augmented Generation (RAG) with verifiable page citations, exam-style answer blueprinting (2-mark, 5-mark, 10-mark), and interactive quizzes.

---

## 🌟 Key Features

1. **Academic Dashboard**
   - Track enrolled courses, uploaded documents, total indexed knowledge chunks, and recent study activity.
   - One-click sample loader pre-bundled with an Operating Systems: Virtual Memory & Paging lecture note.

2. **Document Management & PDF Processing**
   - Upload multiple PDF files per course.
   - Text extraction powered by **PyMuPDF** (`pymupdf`), with fallback to `pypdf` and optional OCR fallback via `pytesseract`.
   - Exact page number tracking for verifiable citations.
   - Real-time indexing progress and document status indicators.

3. **Grounded RAG Question Answering**
   - Hybrid Vector Retrieval combining **ChromaDB** dense vector embeddings with **BM25 keyword search** (Reciprocal Rank Fusion).
   - Multi-provider LLM support: **Google Gemini** (Gemini 2.5 Flash / 1.5 Flash), **OpenAI** (GPT-4o-mini), or **Ollama** (Local models).
   - **Zero-Hallucination Policy**: If course materials do not contain the answer, the assistant states so explicitly.
   - Verifiable source citation cards showing document name, page number, and source excerpts.

4. **Academic Study Tools**
   - **Structured Revision Summaries**: Executive overview, core concepts, formulas, exam pitfalls, and revision checklists.
   - **Exam Answer Blueprint**: Generates answers tailored for university exam marking schemes:
     - **2 Marks**: Crisp definition and 2 bullet points (40–60 words).
     - **5 Marks**: Working principle, mechanism, and diagram description (150–250 words).
     - **10 Marks**: Comprehensive essay structure with intro, theory, architecture, trade-offs, case study, and conclusion (400–600 words).
   - **Interactive Practice Quizzes**: Generates MCQs with immediate feedback, scoring, and page citations.

5. **Chat History**
   - Saves conversations per subject so students can continue past sessions.
   - Clear chat and export options.

---

## 🏗️ Architecture & Project Structure

```
GENAI.PY/
├── app.py                 # Streamlit web application & UI views
├── config.py              # Configuration & environment variable loading
├── requirements.txt       # Dependencies
├── .env.example           # Example environment variables
├── README.md              # Project documentation
├── core/
│   ├── __init__.py
│   ├── pdf_processor.py   # PDF text extraction & page tracking
│   ├── chunker.py         # Recursive text chunking with page attribution
│   ├── vector_store.py    # Hybrid retrieval (ChromaDB + BM25)
│   ├── rag_engine.py      # LLM orchestration, anti-hallucination prompt, citations
│   ├── study_tools.py     # Summaries, 2/5/10-mark answers, and quizzes
│   └── storage.py         # Persistent JSON storage for subjects, docs, chats
├── sample_docs/
│   └── os_memory_management_sample.pdf # Sample 4-page lecture notes
└── tests/
    └── test_core.py       # Automated unit & integration tests
```

---

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.10+ (Tested and verified on Python 3.14)
- (Optional) Free Google Gemini API Key from [Google AI Studio](https://aistudio.google.com/) or OpenAI API Key.

### 2. Installation
Clone the repository and install requirements:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```
Open `.env` and set your API key:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Note: You can also enter or update your API key directly inside the web UI under **Settings & API Keys**!)*

### 4. Run the Application
Launch the Streamlit app:
```bash
streamlit run app.py
```
Open your browser at:
👉 **http://localhost:8501**

---

## 🧪 Running Tests

To run the automated test suite:
```bash
py -m unittest tests/test_core.py
```
Tests cover:
- PDF extraction and page numbering
- Chunking and metadata retention
- Vector store indexing and BM25/Chroma retrieval
- Persistent storage operations
- Quiz JSON parsing and validation
