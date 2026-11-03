"""
CourseCompass AI - The Intelligent Study Assistant for College Students.
Modern, Real-World Web Application Interface (Zero-Sidebar Full-Width Architecture).
Grounded RAG, Verifiable Citations, Exam Blueprinting, and Interactive Quizzes.
"""

import os
import io
import json
import shutil
from pathlib import Path
import datetime
import streamlit as st

# Configure page layout and metadata
st.set_page_config(
    page_title="CourseCompass AI | College Study Assistant",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Core imports
from config import (
    DOCS_DIR,
    SAMPLE_DOCS_DIR,
    GROQ_API_KEY,
    TOP_K_RETRIEVAL
)
from core.storage import storage
from core.pdf_processor import PDFProcessor
from core.chunker import TextChunker
from core.vector_store import vector_store
from core.rag_engine import rag_engine
from core.study_tools import StudyTools


# ---------------- MODERN FULL-WIDTH WEB APPLICATION CSS ----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Completely hide the clunky Streamlit default sidebar and collapse arrow */
    [data-testid="stSidebar"], 
    [data-testid="collapsedControl"],
    section[data-testid="stSidebar"] {
        display: none !important;
    }

    /* Clean container padding */
    .main .block-container {
        padding-top: 1.2rem;
        padding-bottom: 4rem;
        max-width: 1240px;
    }

    /* Modern SaaS Top Navbar */
    .saas-navbar {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 18px;
        padding: 0.9rem 1.6rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 20px -3px rgba(15, 23, 42, 0.05);
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 1rem;
    }
    .brand-cluster {
        display: flex;
        align-items: center;
        gap: 0.9rem;
    }
    .brand-logo-badge {
        background: linear-gradient(135deg, #3B82F6 0%, #1D4ED8 100%);
        color: #FFFFFF;
        width: 44px;
        height: 44px;
        border-radius: 14px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.4rem;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28);
    }
    .brand-heading {
        font-size: 1.35rem;
        font-weight: 800;
        color: #0F172A;
        letter-spacing: -0.5px;
        line-height: 1.1;
    }
    .brand-subtext {
        font-size: 0.8rem;
        color: #64748B;
        font-weight: 500;
    }
    .nav-status-pill {
        display: inline-flex;
        align-items: center;
        gap: 0.45rem;
        background: #F0FDF4;
        color: #166534;
        font-size: 0.8rem;
        font-weight: 600;
        padding: 0.4rem 0.9rem;
        border-radius: 9999px;
        border: 1px solid #BBF7D0;
    }

    /* Hero Banner */
    .hero-glass-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 45%, #2563EB 100%);
        border-radius: 20px;
        padding: 2.2rem 2.6rem;
        color: #FFFFFF;
        margin-bottom: 1.8rem;
        box-shadow: 0 12px 32px -4px rgba(15, 23, 42, 0.18);
    }
    .hero-glass-banner h1 {
        color: #FFFFFF !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.8px !important;
        margin-bottom: 0.4rem !important;
    }
    .hero-glass-banner p {
        color: #CBD5E1 !important;
        font-size: 1.05rem;
        max-width: 720px;
        line-height: 1.6;
        margin-bottom: 0;
    }

    /* Metric Stat Box */
    .metric-card-modern {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.3rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        transition: transform 0.18s ease, box-shadow 0.18s ease;
    }
    .metric-card-modern:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
    }
    .metric-top {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.5rem;
    }
    .metric-label {
        font-size: 0.76rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #64748B;
        letter-spacing: 0.5px;
    }
    .metric-icon-wrap {
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.1rem;
    }
    .metric-value {
        font-size: 2.1rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1;
    }
    .metric-sub {
        font-size: 0.8rem;
        color: #94A3B8;
        margin-top: 0.4rem;
    }

    /* Course Cards */
    .course-card-pro {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.4rem;
        margin-bottom: 1rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.02);
        transition: border-color 0.18s ease, box-shadow 0.18s ease;
    }
    .course-card-pro:hover {
        border-color: #3B82F6;
        box-shadow: 0 8px 20px rgba(59, 130, 246, 0.08);
    }
    .course-code-pill {
        background: #EFF6FF;
        color: #2563EB;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 0.25rem 0.65rem;
        border-radius: 6px;
    }
    .course-title-pro {
        font-size: 1.2rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0.3rem 0;
    }
    .course-desc-pro {
        font-size: 0.88rem;
        color: #475569;
        line-height: 1.5;
        margin-bottom: 0.8rem;
    }
    .course-meta-row {
        display: flex;
        align-items: center;
        gap: 1.2rem;
        font-size: 0.82rem;
        color: #64748B;
        border-top: 1px solid #F1F5F9;
        padding-top: 0.7rem;
    }

    /* Citation Card */
    .citation-drawer-pro {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-left: 4px solid #2563EB;
        border-radius: 12px;
        padding: 0.9rem 1.2rem;
        margin-top: 0.8rem;
        font-size: 0.88rem;
    }
    .citation-badge-file {
        background: #EFF6FF;
        color: #1D4ED8;
        font-weight: 700;
        font-size: 0.76rem;
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
    }
    .citation-badge-pg {
        background: #F1F5F9;
        color: #0F172A;
        font-weight: 700;
        font-size: 0.76rem;
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
        border: 1px solid #CBD5E1;
    }

    /* Question Bubble */
    .chat-bubble-user {
        background: #2563EB;
        color: white;
        padding: 0.9rem 1.3rem;
        border-radius: 16px 16px 4px 16px;
        margin-bottom: 1rem;
        font-size: 0.98rem;
        max-width: 85%;
        margin-left: auto;
    }

    /* Quiz Card */
    .quiz-card-pro {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 16px;
        padding: 1.6rem;
        margin-bottom: 1.3rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.03);
    }
</style>
""", unsafe_allow_html=True)


# ---------------- SESSION STATE ----------------
if "selected_subject_id" not in st.session_state:
    subjects = storage.get_subjects()
    st.session_state.selected_subject_id = subjects[0]["id"] if subjects else None

if "groq_api_key" not in st.session_state:
    st.session_state.groq_api_key = GROQ_API_KEY

rag_engine.update_keys(groq_key=st.session_state.groq_api_key)

if "nav_tab" not in st.session_state:
    st.session_state.nav_tab = "📊 Dashboard"

if "active_quiz" not in st.session_state:
    st.session_state.active_quiz = []

if "quiz_submitted" not in st.session_state:
    st.session_state.quiz_submitted = False

if "quiz_answers" not in st.session_state:
    st.session_state.quiz_answers = {}


# Helper: Load pre-bundled sample PDF
def load_sample_document(target_subject_id: str):
    sample_pdf_path = SAMPLE_DOCS_DIR / "os_memory_management_sample.pdf"
    if not sample_pdf_path.exists():
        st.error("Sample PDF not found.")
        return

    dest_path = DOCS_DIR / "os_memory_management_sample.pdf"
    shutil.copy(sample_pdf_path, dest_path)

    doc_id = "doc_sample_os"
    pages, meta = PDFProcessor.extract_document(dest_path)

    chunker = TextChunker()
    chunks = chunker.chunk_document_pages(
        pages=pages,
        doc_id=doc_id,
        doc_name=meta["filename"],
        subject_id=target_subject_id
    )

    vector_store.add_chunks(chunks)

    doc_record = {
        "id": doc_id,
        "filename": meta["filename"],
        "original_name": meta["filename"],
        "subject_id": target_subject_id,
        "page_count": meta["page_count"],
        "chunk_count": len(chunks),
        "file_size_kb": meta["file_size_kb"],
        "uploaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "status": "Indexed"
    }
    storage.add_document(doc_record)
    st.toast("✅ Sample Lecture Notes successfully loaded and indexed!")


# ---------------- TOP HEADER NAVBAR ----------------
subjects = storage.get_subjects()
active_sub = storage.get_subject(st.session_state.selected_subject_id) if st.session_state.selected_subject_id else (subjects[0] if subjects else None)
active_code_name = f"{active_sub['code']}: {active_sub['name']}" if active_sub else "General Studies"
active_chunks_count = vector_store.get_chunk_count(st.session_state.selected_subject_id)

engine_badge = "⚡ Groq Llama-3.3 Active" if st.session_state.groq_api_key else "● Built-in Academic Engine"
engine_bg = "#ECFDF5" if st.session_state.groq_api_key else "#F0FDF4"
engine_color = "#047857" if st.session_state.groq_api_key else "#166534"

st.markdown(f"""
<div class="saas-navbar">
    <div class="brand-cluster">
        <div class="brand-logo-badge">🧭</div>
        <div>
            <div class="brand-heading">CourseCompass AI</div>
            <div class="brand-subtext">College Study Assistant & Grounded RAG Copilot</div>
        </div>
    </div>
    <div style="display: flex; align-items: center; gap: 0.9rem; flex-wrap: wrap;">
        <div class="nav-status-pill" style="background: {engine_bg}; color: {engine_color};">
            <span>●</span> {engine_badge}
        </div>
        <div style="font-size: 0.82rem; font-weight: 600; color: #1E40AF; background: #EFF6FF; padding: 0.4rem 0.9rem; border-radius: 9999px; border: 1px solid #DBEAFE;">
            📖 {active_code_name} ({active_chunks_count} chunks)
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ---------------- HORIZONTAL SEGMENTED NAVIGATION ----------------
nav_selection = st.segmented_control(
    "Navigation",
    options=[
        "📊 Dashboard",
        "💬 Study Chat",
        "🎯 Exam Blueprint",
        "🧠 Quizzes",
        "📚 Course Materials"
    ],
    default="📊 Dashboard",
    label_visibility="collapsed"
)

# Course quick selector on top right of views
c_top_info, c_top_select = st.columns([2.5, 1.5])
with c_top_select:
    if subjects:
        sub_options = {s["id"]: f"{s['code']} · {s['name']}" for s in subjects}
        new_active = st.selectbox(
            "Switch Course Context",
            options=list(sub_options.keys()),
            format_func=lambda sid: sub_options[sid],
            index=list(sub_options.keys()).index(st.session_state.selected_subject_id) if st.session_state.selected_subject_id in sub_options else 0,
            label_visibility="collapsed"
        )
        if new_active != st.session_state.selected_subject_id:
            st.session_state.selected_subject_id = new_active
            st.rerun()

st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)


# ---------------- TAB 1: DASHBOARD ----------------
if nav_selection == "📊 Dashboard":
    st.markdown("""
    <div class="hero-glass-banner">
        <h1>Intelligent Academic Study Copilot</h1>
        <p>Grounded in your course documents. Ask deep conceptual questions with verified page citations, generate exam-ready answers according to marking rubrics, and master your subjects with AI-driven active recall.</p>
    </div>
    """, unsafe_allow_html=True)

    # 4 Real-World Metrics
    docs = storage.get_documents()
    total_chunks = vector_store.get_chunk_count()
    recent_acts = storage.get_recent_activities(limit=5)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card-modern">
            <div class="metric-top">
                <span class="metric-label">Enrolled Courses</span>
                <div class="metric-icon-wrap" style="background: #EFF6FF; color: #2563EB;">📚</div>
            </div>
            <div class="metric-value">{len(subjects)}</div>
            <div class="metric-sub">Active subjects</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card-modern">
            <div class="metric-top">
                <span class="metric-label">Course Documents</span>
                <div class="metric-icon-wrap" style="background: #F0FDF4; color: #16A34A;">📄</div>
            </div>
            <div class="metric-value">{len(docs)}</div>
            <div class="metric-sub">PDF lecture notes & slides</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card-modern">
            <div class="metric-top">
                <span class="metric-label">Knowledge Base</span>
                <div class="metric-icon-wrap" style="background: #FAF5FF; color: #9333EA;">🧩</div>
            </div>
            <div class="metric-value">{total_chunks}</div>
            <div class="metric-sub">Semantic indexed chunks</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card-modern">
            <div class="metric-top">
                <span class="metric-label">Citation Grounding</span>
                <div class="metric-icon-wrap" style="background: #FEF3C7; color: #D97706;">🎯</div>
            </div>
            <div class="metric-value">100%</div>
            <div class="metric-sub">Strict page references</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Quick One-Click Starter if empty
    if total_chunks == 0:
        st.info("💡 **Ready to Study?** Load the sample 4-page Operating Systems lecture material to test the RAG engine immediately.")
        if st.button("⚡ Load Bundled OS Lecture Notes", type="primary"):
            load_sample_document(st.session_state.selected_subject_id)
            st.rerun()

    c_left, c_right = st.columns([1.4, 1])

    with c_left:
        st.subheader("📚 Your Enrolled Courses")
        for sub in subjects:
            sub_docs = storage.get_documents(subject_id=sub["id"])
            sub_chunks = vector_store.get_chunk_count(subject_id=sub["id"])
            st.markdown(f"""
            <div class="course-card-pro">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span class="course-code-pill">{sub['code']}</span>
                    <span style="font-size: 0.8rem; color: #94A3B8;">Semester VI</span>
                </div>
                <div class="course-title-pro">{sub['name']}</div>
                <div class="course-desc-pro">{sub.get('description', 'Comprehensive lecture notes, slides, and syllabus topics.')}</div>
                <div class="course-meta-row">
                    <span>📄 <b>{len(sub_docs)}</b> Documents</span>
                    <span>🧩 <b>{sub_chunks}</b> Chunks Indexed</span>
                    <span style="color: #10B981; font-weight: 600;">● Active</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with c_right:
        st.subheader("🕒 Recent Study Activity")
        if not recent_acts:
            st.write("No study activity logged yet.")
        else:
            for act in recent_acts:
                st.markdown(f"""
                <div style="padding: 0.8rem 1rem; margin-bottom: 0.6rem; background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px;">
                    <div style="font-size: 0.82rem; font-weight: 700; color: #1E3A8A;">{act.get('action')}</div>
                    <div style="font-size: 0.85rem; color: #475569; margin-top: 0.2rem;">{act.get('detail')}</div>
                </div>
                """, unsafe_allow_html=True)


# ---------------- TAB 2: STUDY CHAT (RAG) ----------------
elif nav_selection == "💬 Study Chat":
    st.markdown(f"## 💬 Academic Study Chat")
    st.caption(f"Currently grounded in **{active_code_name}**. Answers are drawn strictly from your materials with verified page citations.")

    # High-Yield Suggestion Chips
    st.markdown("**💡 High-Yield Questions from your Materials:**")
    p1, p2, p3 = st.columns(3)
    suggested_q = None
    with p1:
        if st.button("❓ What causes thrashing in an OS?"):
            suggested_q = "What causes thrashing in an operating system and how can it be resolved?"
    with p2:
        if st.button("❓ How does the TLB improve memory speed?"):
            suggested_q = "How does the Translation Lookaside Buffer (TLB) improve memory access speed?"
    with p3:
        if st.button("❓ Compare FIFO and LRU page replacement"):
            suggested_q = "Compare FIFO and LRU page replacement algorithms. Mention Belady's Anomaly."

    st.markdown("---")

    # Chat history
    chat_history = storage.get_chat_history(st.session_state.selected_subject_id) if st.session_state.selected_subject_id else []

    for msg in chat_history:
        role = msg.get("role")
        content = msg.get("content", "")
        citations = msg.get("citations", [])

        if role == "user":
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(content)
        else:
            with st.chat_message("assistant", avatar="🧭"):
                st.markdown(content)
                if citations:
                    with st.expander(f"📚 Verified Source Citations ({len(citations)} references found)", expanded=False):
                        for c in citations:
                            st.markdown(f"""
                            <div class="citation-drawer-pro">
                                <span class="citation-badge-file">📄 {c.get('doc_name')}</span>
                                <span class="citation-badge-pg">Page {c.get('page')}</span>
                                <div style="margin-top: 0.4rem; color: #334155; font-style: italic;">
                                    "{c.get('snippet')}"
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

    # Input Box
    user_query = st.chat_input("Ask any concept, algorithm, formula, or exam question...")
    query_to_send = suggested_q or user_query

    if query_to_send:
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(query_to_send)

        storage.add_chat_message(st.session_state.selected_subject_id, role="user", content=query_to_send)

        with st.chat_message("assistant", avatar="🧭"):
            with st.spinner("Searching course materials & synthesizing verified answer..."):
                answer_md, citations = rag_engine.answer_question(
                    question=query_to_send,
                    subject_id=st.session_state.selected_subject_id,
                    top_k=4
                )
                st.markdown(answer_md)

                if citations:
                    with st.expander(f"📚 Verified Source Citations ({len(citations)} references found)", expanded=False):
                        for c in citations:
                            st.markdown(f"""
                            <div class="citation-drawer-pro">
                                <span class="citation-badge-file">📄 {c.get('doc_name')}</span>
                                <span class="citation-badge-pg">Page {c.get('page')}</span>
                                <div style="margin-top: 0.4rem; color: #334155; font-style: italic;">
                                    "{c.get('snippet')}"
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

        storage.add_chat_message(st.session_state.selected_subject_id, role="assistant", content=answer_md, citations=citations)
        st.rerun()

    if chat_history:
        if st.button("🧹 Clear Chat History"):
            storage.clear_chat_history(st.session_state.selected_subject_id)
            st.rerun()


# ---------------- TAB 3: EXAM BLUEPRINT ----------------
elif nav_selection == "🎯 Exam Blueprint":
    st.markdown(f"## 🎯 University Exam Answer Blueprint")
    st.write(f"Generate benchmark answers for **{active_code_name}** matching university marking schemes.")

    exam_q = st.text_input(
        "Enter Exam Question",
        value="Explain Virtual Memory and the working of Paging with address translation.",
        help="Type any question from past exam papers or syllabus"
    )

    marks_choice = st.radio(
        "Select Mark Weighting",
        options=[2, 5, 10],
        format_func=lambda m: f"{m} Marks ({'Crisp Definition & Formula' if m==2 else 'Mechanism & Diagram' if m==5 else 'Comprehensive Long Essay Benchmark'})",
        horizontal=True
    )

    if st.button("📝 Generate Model Exam Answer", type="primary"):
        with st.spinner(f"Drafting benchmark {marks_choice}-mark university answer..."):
            ans = StudyTools.generate_exam_answer(
                question=exam_q,
                marks=marks_choice,
                subject_id=st.session_state.selected_subject_id
            )
            st.markdown(ans)


# ---------------- TAB 4: INTERACTIVE QUIZZES & EXAM PREP ----------------
elif nav_selection == "🧠 Quizzes":
    st.markdown("## 🧠 University Quiz & Exam Preparation Studio")
    st.write(f"Generate novel, dynamically varied assessments and university prep questions for **{active_code_name}**.")

    tab_mcq_quiz, tab_prep_bank = st.tabs(["🎯 Interactive MCQ Assessment", "📚 Exam Preparation Question Bank"])

    with tab_mcq_quiz:
        st.subheader("🎯 Dynamic Multiple-Choice Practice Test")
        st.caption("Each generation creates completely fresh questions testing different angles, mechanisms, and formulas.")

        col_q1, col_q2, col_q3 = st.columns([2, 1.2, 1.2])
        with col_q1:
            quiz_topic = st.text_input(
                "Quiz Topic or Chapter",
                placeholder="e.g. Page replacement, TLB hit ratio, Thrashing causes, Paging offsets",
                help="Leave blank to cover all course material or specify a topic"
            )
        with col_q2:
            num_q = st.select_slider(
                "Questions Count",
                options=[3, 5, 8, 10, 12, 15],
                value=5,
                help="Select how many questions you want in this test"
            )
        with col_q3:
            diff_level = st.selectbox(
                "Assessment Focus",
                options=[
                    "Mixed Exam Focus",
                    "Deep Conceptual & Trade-offs",
                    "Formulas & EMAT Calculations",
                    "Edge Cases & Anomalies"
                ]
            )

        col_btn_gen, col_btn_reset = st.columns([1, 1])
        with col_btn_gen:
            if st.button("🎲 Generate Fresh Quiz (New Questions)", type="primary"):
                with st.spinner("Generating unique, grounded questions via AI..."):
                    quiz_items = StudyTools.generate_quiz(
                        subject_id=st.session_state.selected_subject_id,
                        topic=quiz_topic,
                        num_questions=num_q,
                        difficulty=diff_level
                    )
                    st.session_state.active_quiz = quiz_items
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                    st.toast(f"✅ Generated {len(quiz_items)} unique questions!")
                    st.rerun()

        with col_btn_reset:
            if st.session_state.active_quiz:
                if st.button("🔄 Retake / Reset Answers"):
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
                    st.rerun()

        # Render Active Quiz Questions
        if st.session_state.active_quiz:
            st.markdown("---")
            st.markdown(f"### 📝 Test Paper ({len(st.session_state.active_quiz)} Questions • {diff_level})")

            for idx, q_data in enumerate(st.session_state.active_quiz):
                q_num = idx + 1
                st.markdown(f"""
                <div class="quiz-card-pro">
                    <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin-bottom: 0.8rem;">
                        Q{q_num}: {q_data.get('question')}
                    </div>
                </div>
                """, unsafe_allow_html=True)

                opts = q_data.get("options", [])
                user_choice = st.radio(
                    f"Options for Q{q_num}:",
                    options=opts,
                    key=f"quiz_opt_{idx}_{q_data.get('id', idx)}",
                    disabled=st.session_state.quiz_submitted,
                    label_visibility="collapsed"
                )
                st.session_state.quiz_answers[idx] = user_choice

                if st.session_state.quiz_submitted:
                    correct_letter = q_data.get("correct_option", "A").strip()
                    chosen_letter = user_choice[0] if user_choice else ""

                    if chosen_letter.upper() == correct_letter.upper():
                        st.success(f"✅ **Correct!** (Answer: {correct_letter})")
                    else:
                        st.error(f"❌ **Incorrect.** (Correct Answer: {correct_letter})")

                    st.markdown(f"""
                    <div class="citation-drawer-pro" style="border-left-color: #10B981; margin-bottom: 1.5rem;">
                        <b>💡 Explanation:</b> {q_data.get('explanation')}<br>
                        <span style="font-size: 0.8rem; color: #64748B;">Source Citation: {q_data.get('source')}</span>
                    </div>
                    """, unsafe_allow_html=True)

            if not st.session_state.quiz_submitted:
                if st.button("🏁 Submit Test & View Score", type="primary"):
                    st.session_state.quiz_submitted = True
                    st.rerun()
            else:
                score = 0
                for idx, q_data in enumerate(st.session_state.active_quiz):
                    chosen = st.session_state.quiz_answers.get(idx, "")
                    if chosen and chosen[0].upper() == q_data.get("correct_option", "").strip().upper():
                        score += 1
                total = len(st.session_state.active_quiz)
                pct = int((score / total) * 100) if total > 0 else 0

                grade = "Outstanding! 🌟" if pct >= 85 else "Well Done! 👍" if pct >= 65 else "Needs Revision 📖"
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #EFF6FF, #DBEAFE); border: 2px solid #3B82F6; border-radius: 16px; padding: 1.8rem; text-align: center; margin-top: 1.5rem;">
                    <div style="font-size: 0.9rem; font-weight: 700; color: #2563EB; text-transform: uppercase;">Assessment Complete</div>
                    <h2 style="margin: 0.3rem 0; color: #1E3A8A; font-weight: 800; font-size: 2.3rem;">{score} / {total} ({pct}%)</h2>
                    <p style="color: #475569; margin: 0.3rem 0 0 0; font-size: 1.1rem; font-weight: 600;">{grade}</p>
                    <p style="color: #64748B; font-size: 0.88rem; margin-top: 0.5rem;">Review the verified source citations and detailed explanations above to master these concepts.</p>
                </div>
                """, unsafe_allow_html=True)

    with tab_prep_bank:
        st.subheader("📚 University Exam Preparation Question Bank")
        st.caption("Generate a diverse bank of past-paper style questions across 2-mark, 5-mark, and 10-mark weights with benchmark solution outlines.")

        p_col1, p_col2 = st.columns([3, 1])
        with p_col1:
            prep_topic = st.text_input("Focus Area (Optional)", placeholder="e.g. Memory management, Thrashing, Page replacement", key="prep_topic_input")
        with p_col2:
            prep_count = st.select_slider("Question Count", options=[3, 5, 8, 10], value=5, key="prep_count_slider")

        if st.button("📋 Generate Preparation Questions", type="primary"):
            with st.spinner("Extracting high-yield university exam questions from course materials..."):
                st.session_state.prep_items = StudyTools.generate_prep_questions(
                    subject_id=st.session_state.selected_subject_id,
                    topic=prep_topic,
                    count=prep_count
                )
                st.rerun()

        if "prep_items" in st.session_state and st.session_state.prep_items:
            st.markdown("---")
            st.markdown(f"### 📖 Exam Practice Questions ({len(st.session_state.prep_items)} Questions)")

            for idx, p_item in enumerate(st.session_state.prep_items):
                p_num = idx + 1
                marks_badge = f"{p_item.get('marks', 5)} Marks"
                st.markdown(f"""
                <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-left: 5px solid #3B82F6; border-radius: 12px; padding: 1.2rem; margin-bottom: 1rem;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem;">
                        <span style="font-size: 0.75rem; font-weight: 700; background: #EFF6FF; color: #2563EB; padding: 0.2rem 0.6rem; border-radius: 6px;">{p_item.get('topic', 'Core Topic')}</span>
                        <span style="font-size: 0.8rem; font-weight: 700; background: #FEF3C7; color: #B45309; padding: 0.2rem 0.6rem; border-radius: 6px;">Weight: {marks_badge}</span>
                    </div>
                    <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A; margin: 0.4rem 0;">
                        Q{p_num}: {p_item.get('question')}
                    </div>
                    <div style="font-size: 0.82rem; color: #64748B;">Citation: <i>{p_item.get('source')}</i></div>
                </div>
                """, unsafe_allow_html=True)

                with st.expander(f"👁️ View Benchmark Solution Outline & Scoring Rubric (Q{p_num})"):
                    st.markdown(f"**Marking Criteria / Key Points Required for Full Marks:**")
                    st.markdown(p_item.get("solution_outline", "Review the course lecture slides for full derivation."))
                    st.caption(f"Source Document Reference: {p_item.get('source')}")



# ---------------- TAB 5: COURSE MATERIALS & PDF UPLOAD ----------------
elif nav_selection == "📚 Course Materials":
    st.markdown("## 📚 Course Materials & PDF Upload")
    st.write("Manage your courses and upload course PDFs (lecture notes, textbooks, slides).")

    tab_library, tab_new_course = st.tabs(["📑 Document Library", "➕ Add New Course"])

    with tab_library:
        if not active_sub:
            st.warning("Please select or create a course.")
        else:
            st.markdown(f"### Current Course: **{active_sub['code']} · {active_sub['name']}**")

            with st.expander("📤 Upload PDF Course Notes", expanded=True):
                uploaded_files = st.file_uploader(
                    "Drop PDF files here",
                    type=["pdf"],
                    accept_multiple_files=True
                )

                col_btn1, col_btn2 = st.columns([1, 1])
                with col_btn1:
                    process_btn = st.button("🚀 Process & Index Materials", type="primary", disabled=not uploaded_files)
                with col_btn2:
                    sample_btn = st.button("⚡ Load Bundled Sample PDF")

                if sample_btn:
                    load_sample_document(st.session_state.selected_subject_id)
                    st.rerun()

                if process_btn and uploaded_files:
                    with st.spinner("Extracting text with PyMuPDF, chunking, and indexing into vector store..."):
                        for i, uploaded_file in enumerate(uploaded_files):
                            doc_id = f"doc_{int(datetime.datetime.now().timestamp())}_{i}"
                            save_path = DOCS_DIR / f"{doc_id}_{uploaded_file.name}"
                            with open(save_path, "wb") as f:
                                f.write(uploaded_file.getbuffer())

                            pages, meta = PDFProcessor.extract_document(save_path)
                            chunker = TextChunker()
                            chunks = chunker.chunk_document_pages(
                                pages=pages,
                                doc_id=doc_id,
                                doc_name=uploaded_file.name,
                                subject_id=st.session_state.selected_subject_id
                            )
                            vector_store.add_chunks(chunks)
                            storage.add_document({
                                "id": doc_id,
                                "filename": uploaded_file.name,
                                "original_name": uploaded_file.name,
                                "subject_id": st.session_state.selected_subject_id,
                                "page_count": meta.get("page_count", len(pages)),
                                "chunk_count": len(chunks),
                                "file_size_kb": meta.get("file_size_kb", round(len(uploaded_file.getvalue()) / 1024, 2)),
                                "uploaded_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                                "status": "Indexed"
                            })
                    st.success(f"Indexed {len(uploaded_files)} PDF(s) successfully!")
                    st.rerun()

            st.markdown("### 📄 Uploaded Course Documents")
            course_docs = storage.get_documents(subject_id=st.session_state.selected_subject_id)

            if not course_docs:
                st.info("No documents uploaded for this course yet.")
            else:
                for doc in course_docs:
                    c_doc_info, c_doc_del = st.columns([5, 1])
                    with c_doc_info:
                        st.markdown(f"""
                        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 12px; padding: 1rem; margin-bottom: 0.8rem;">
                            <div style="font-weight: 700; font-size: 1.05rem; color: #0F172A;">📄 {doc.get('filename')}</div>
                            <div style="font-size: 0.84rem; color: #64748B; margin-top: 0.3rem;">
                                📖 <b>{doc.get('page_count', 0)}</b> Pages &nbsp;|&nbsp;
                                🧩 <b>{doc.get('chunk_count', 0)}</b> Chunks Indexed &nbsp;|&nbsp;
                                💾 <b>{doc.get('file_size_kb', 0)}</b> KB &nbsp;|&nbsp;
                                <span style="color: #10B981; font-weight: 600;">● Active</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    with c_doc_del:
                        st.write("")
                        if st.button("🗑️ Delete", key=f"del_doc_{doc['id']}"):
                            storage.delete_document(doc['id'])
                            vector_store.delete_document_chunks(doc['id'])
                            st.rerun()

    with tab_new_course:
        st.subheader("➕ Create a New Course")
        with st.form("add_course_form"):
            new_code = st.text_input("Course Code (e.g. CS-401, MATH-201)")
            new_name = st.text_input("Course Name (e.g. Database Systems, Linear Algebra)")
            new_desc = st.text_area("Course Description / Topics Covered")
            create_btn = st.form_submit_button("Create Course", type="primary")

            if create_btn:
                if not new_code.strip() or not new_name.strip():
                    st.error("Please provide both Course Code and Name.")
                else:
                    new_sub = storage.add_subject(name=new_name, code=new_code, description=new_desc)
                    st.session_state.selected_subject_id = new_sub["id"]
                    st.success(f"Course '{new_code}: {new_name}' created successfully!")
                    st.rerun()
