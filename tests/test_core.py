"""
Unit and integration tests for CourseCompass AI core components.
"""

import unittest
from pathlib import Path

from config import SAMPLE_DOCS_DIR
from core.pdf_processor import PDFProcessor
from core.chunker import TextChunker
from core.vector_store import VectorStore
from core.storage import StorageManager
from core.study_tools import StudyTools


class TestCourseCompassCore(unittest.TestCase):

    def setUp(self):
        self.sample_pdf = SAMPLE_DOCS_DIR / "os_memory_management_sample.pdf"
        self.assertTrue(self.sample_pdf.exists(), "Sample PDF must exist.")

    def test_pdf_extraction(self):
        pages, meta = PDFProcessor.extract_document(self.sample_pdf)
        self.assertEqual(len(pages), 4, "Should extract exactly 4 pages.")
        self.assertEqual(pages[0]["page_number"], 1)
        self.assertIn("Virtual Memory", pages[0]["text"])
        self.assertIn("Translation Lookaside Buffer", pages[1]["text"])
        self.assertIn("Page Replacement Algorithms", pages[2]["text"])
        self.assertIn("Thrashing", pages[3]["text"])
        self.assertEqual(meta["page_count"], 4)

    def test_chunking(self):
        pages, _ = PDFProcessor.extract_document(self.sample_pdf)
        chunker = TextChunker(chunk_size=400, chunk_overlap=80)
        chunks = chunker.chunk_document_pages(
            pages=pages,
            doc_id="doc_test_1",
            doc_name="os_memory_management_sample.pdf",
            subject_id="sub_cs101"
        )
        self.assertGreater(len(chunks), 4, "Should produce multiple chunks.")
        # Ensure page attribution is preserved
        first_chunk = chunks[0]
        self.assertEqual(first_chunk["document_id"], "doc_test_1")
        self.assertEqual(first_chunk["page_number"], 1)
        self.assertEqual(first_chunk["subject_id"], "sub_cs101")
        self.assertIn("Virtual Memory", first_chunk["text"])

    def test_vector_store_retrieval(self):
        pages, _ = PDFProcessor.extract_document(self.sample_pdf)
        chunker = TextChunker(chunk_size=500, chunk_overlap=100)
        chunks = chunker.chunk_document_pages(
            pages=pages,
            doc_id="doc_test_1",
            doc_name="os_memory_management_sample.pdf",
            subject_id="sub_cs101"
        )

        test_store = VectorStore(persist_dir=Path("data/test_chroma"))
        test_store.add_chunks(chunks)

        # Query 1: Thrashing causes
        thrashing_results = test_store.retrieve(query="What causes thrashing in operating systems?", subject_id="sub_cs101", top_k=2)
        self.assertTrue(len(thrashing_results) > 0)
        top_text = thrashing_results[0]["text"]
        self.assertTrue("thrashing" in top_text.lower() or "page fault" in top_text.lower())
        self.assertEqual(thrashing_results[0]["page_number"], 4, "Thrashing content is on Page 4")

        # Query 2: Belady's Anomaly
        belady_results = test_store.retrieve(query="Belady's Anomaly and FIFO", subject_id="sub_cs101", top_k=2)
        self.assertTrue(len(belady_results) > 0)
        self.assertEqual(belady_results[0]["page_number"], 3, "Belady's Anomaly is on Page 3")

    def test_storage_manager(self):
        test_storage_file = Path("data/test_storage.json")
        if test_storage_file.exists():
            test_storage_file.unlink()

        sm = StorageManager(storage_path=test_storage_file)
        subjects = sm.get_subjects()
        self.assertGreaterEqual(len(subjects), 2)

        # Add course
        new_course = sm.add_subject(name="Database Systems", code="CS-401")
        self.assertEqual(new_course["code"], "CS-401")
        self.assertIsNotNone(sm.get_subject(new_course["id"]))

        # Add chat message
        sm.add_chat_message(subject_id=new_course["id"], role="user", content="What is ACID?")
        msgs = sm.get_chat_history(subject_id=new_course["id"])
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]["content"], "What is ACID?")

        # Clear chat
        sm.clear_chat_history(subject_id=new_course["id"])
        self.assertEqual(len(sm.get_chat_history(subject_id=new_course["id"])), 0)

        # Test User Auth
        ok, msg, user = sm.authenticate_user("student@college.edu", "student123")
        self.assertTrue(ok)
        self.assertEqual(user["email"], "student@college.edu")

        # Wrong password
        ok_fail, msg_fail, _ = sm.authenticate_user("student@college.edu", "wrongpw")
        self.assertFalse(ok_fail)

        # Register new student
        ok_reg, _, new_student = sm.register_user(
            name="Priya Sharma",
            email="priya@mit.edu",
            password="securepassword123",
            university="MIT",
            major="AI & Data Science"
        )
        self.assertTrue(ok_reg)
        self.assertEqual(new_student["name"], "Priya Sharma")

        # Duplicate email registration should fail
        ok_dup, _, _ = sm.register_user(
            name="Priya Duplicate",
            email="priya@mit.edu",
            password="securepassword123"
        )
        self.assertFalse(ok_dup)

        # Google 1-Click Auth
        g_user = sm.google_auth_user(
            email="google.scholar@gmail.com",
            name="Scholar Jordan"
        )
        self.assertEqual(g_user["auth_provider"], "google")
        self.assertEqual(g_user["email"], "google.scholar@gmail.com")

        # Cleanup
        if test_storage_file.exists():
            test_storage_file.unlink()

    def test_quiz_json_parsing(self):
        sample_raw = """
        ```json
        [
            {
                "id": "q1",
                "question": "Which algorithm suffers from Belady's Anomaly?",
                "options": ["A) FIFO", "B) LRU", "C) Optimal", "D) Working Set"],
                "correct_option": "A",
                "explanation": "FIFO is known to suffer from Belady's anomaly.",
                "source": "OS Lecture (Page 3)"
            }
        ]
        ```
        """
        parsed = StudyTools._parse_quiz_json(sample_raw)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["correct_option"], "A")


if __name__ == "__main__":
    unittest.main()
