"""
Persistent JSON-based storage manager for CourseCompass AI.
Manages subjects, document metadata, chat histories, quizzes, and student activity logs.
"""

import json
import uuid
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import threading

from config import STORAGE_FILE

_lock = threading.Lock()

def _hash_pw(password: str) -> str:
    """Computes salted SHA-256 hash of a password."""
    return hashlib.sha256(f"coursecompass_salt_{password}".encode("utf-8")).hexdigest()

DEFAULT_STATE = {
    "users": [
        {
            "id": "usr_demo",
            "name": "Alex Student",
            "email": "student@college.edu",
            "university": "College Academic Program",
            "major": "Computer Science",
            "password_hash": _hash_pw("student123"),
            "avatar": "🧑‍🎓",
            "auth_provider": "local",
            "created_at": datetime.now().isoformat()
        }
    ],
    "subjects": [
        {
            "id": "sub_cs101",
            "name": "Operating Systems",
            "code": "CS-301",
            "description": "Processes, Threads, CPU Scheduling, Virtual Memory, and File Systems",
            "color": "#3B82F6",
            "created_at": datetime.now().isoformat()
        },
        {
            "id": "sub_math201",
            "name": "Linear Algebra",
            "code": "MATH-201",
            "description": "Vector Spaces, Eigenvalues, Matrix Factorizations, and SVD",
            "color": "#10B981",
            "created_at": datetime.now().isoformat()
        }
    ],
    "documents": [],
    "chat_histories": {},   # subject_id -> list of message dicts
    "quizzes": {},          # subject_id -> list of quiz dicts
    "activity_log": [
        {
            "id": "act_init",
            "timestamp": datetime.now().isoformat(),
            "action": "System Initialized",
            "detail": "Welcome to CourseCompass AI! Upload course PDFs to start learning."
        }
    ]
}


class StorageManager:
    def __init__(self, storage_path: Path = STORAGE_FILE):
        self.path = storage_path
        self._init_storage()

    def _init_storage(self):
        if not self.path.exists():
            self._save_raw(DEFAULT_STATE)

    def _load_raw(self) -> Dict[str, Any]:
        with _lock:
            try:
                if self.path.exists():
                    with open(self.path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        # Ensure all keys exist
                        for k, v in DEFAULT_STATE.items():
                            if k not in data or not data.get(k):
                                data[k] = v
                        return data
                return DEFAULT_STATE.copy()
            except Exception:
                return DEFAULT_STATE.copy()

    def _save_raw(self, data: Dict[str, Any]):
        with _lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

    # ---------------- Subjects ----------------
    def get_subjects(self) -> List[Dict[str, Any]]:
        data = self._load_raw()
        return data.get("subjects", [])

    def get_subject(self, subject_id: str) -> Optional[Dict[str, Any]]:
        for s in self.get_subjects():
            if s["id"] == subject_id:
                return s
        return None

    def add_subject(self, name: str, code: str, description: str = "", color: str = "#3B82F6") -> Dict[str, Any]:
        data = self._load_raw()
        subject_id = f"sub_{uuid.uuid4().hex[:8]}"
        new_sub = {
            "id": subject_id,
            "name": name.strip(),
            "code": code.strip(),
            "description": description.strip(),
            "color": color,
            "created_at": datetime.now().isoformat()
        }
        data["subjects"].append(new_sub)
        self.log_activity("Created Subject", f"Added course {code}: {name}")
        self._save_raw(data)
        return new_sub

    def delete_subject(self, subject_id: str) -> bool:
        data = self._load_raw()
        initial_len = len(data["subjects"])
        data["subjects"] = [s for s in data["subjects"] if s["id"] != subject_id]
        if len(data["subjects"]) < initial_len:
            # Also clean up documents for this subject
            data["documents"] = [d for d in data["documents"] if d.get("subject_id") != subject_id]
            data["chat_histories"].pop(subject_id, None)
            data["quizzes"].pop(subject_id, None)
            self._save_raw(data)
            return True
        return False

    # ---------------- Documents ----------------
    def get_documents(self, subject_id: Optional[str] = None) -> List[Dict[str, Any]]:
        data = self._load_raw()
        docs = data.get("documents", [])
        if subject_id:
            docs = [d for d in docs if d.get("subject_id") == subject_id]
        return docs

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        for d in self.get_documents():
            if d["id"] == doc_id:
                return d
        return None

    def add_document(self, doc_meta: Dict[str, Any]):
        data = self._load_raw()
        data["documents"].append(doc_meta)
        self.log_activity("Uploaded Document", f"Uploaded {doc_meta.get('filename')} ({doc_meta.get('page_count', 0)} pages)")
        self._save_raw(data)

    def delete_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        data = self._load_raw()
        target = None
        new_docs = []
        for d in data.get("documents", []):
            if d["id"] == doc_id:
                target = d
            else:
                new_docs.append(d)
        if target:
            data["documents"] = new_docs
            self.log_activity("Deleted Document", f"Removed {target.get('filename')}")
            self._save_raw(data)
        return target

    def update_document_status(self, doc_id: str, status: str, chunk_count: Optional[int] = None):
        data = self._load_raw()
        for d in data.get("documents", []):
            if d["id"] == doc_id:
                d["status"] = status
                if chunk_count is not None:
                    d["chunk_count"] = chunk_count
                break
        self._save_raw(data)

    # ---------------- Chat History ----------------
    def get_chat_history(self, subject_id: str) -> List[Dict[str, Any]]:
        data = self._load_raw()
        return data.get("chat_histories", {}).get(subject_id, [])

    def add_chat_message(self, subject_id: str, role: str, content: str, citations: Optional[List[Dict[str, Any]]] = None):
        data = self._load_raw()
        if "chat_histories" not in data:
            data["chat_histories"] = {}
        if subject_id not in data["chat_histories"]:
            data["chat_histories"][subject_id] = []
        
        msg = {
            "id": f"msg_{uuid.uuid4().hex[:8]}",
            "role": role,
            "content": content,
            "citations": citations or [],
            "timestamp": datetime.now().isoformat()
        }
        data["chat_histories"][subject_id].append(msg)
        if role == "user":
            sub_name = next((s["name"] for s in data["subjects"] if s["id"] == subject_id), "Subject")
            self.log_activity("Asked Question", f"Asked about '{content[:40]}...' in {sub_name}")
        self._save_raw(data)
        return msg

    def clear_chat_history(self, subject_id: str):
        data = self._load_raw()
        if "chat_histories" in data and subject_id in data["chat_histories"]:
            data["chat_histories"][subject_id] = []
            self.log_activity("Cleared Chat", f"Reset conversation for course {subject_id}")
            self._save_raw(data)

    # ---------------- Quizzes & Study Materials ----------------
    def get_quizzes(self, subject_id: str) -> List[Dict[str, Any]]:
        data = self._load_raw()
        return data.get("quizzes", {}).get(subject_id, [])

    def save_quiz(self, subject_id: str, quiz_data: Dict[str, Any]):
        data = self._load_raw()
        if "quizzes" not in data:
            data["quizzes"] = {}
        if subject_id not in data["quizzes"]:
            data["quizzes"][subject_id] = []
        data["quizzes"][subject_id].append(quiz_data)
        self.log_activity("Generated Quiz", f"Created quiz: {quiz_data.get('title', 'Study Quiz')}")
        self._save_raw(data)

    # ---------------- Activity Log ----------------
    def log_activity(self, action: str, detail: str):
        data = self._load_raw()
        if "activity_log" not in data:
            data["activity_log"] = []
        act = {
            "id": f"act_{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "detail": detail
        }
        data["activity_log"].insert(0, act)
        # Keep last 50 activities
        data["activity_log"] = data["activity_log"][:50]
        self._save_raw(data)

    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        data = self._load_raw()
        return data.get("activity_log", [])[:limit]

    # ---------------- User Authentication ----------------
    def get_users(self) -> List[Dict[str, Any]]:
        data = self._load_raw()
        return data.get("users", [])

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        clean_email = email.strip().lower()
        for u in self.get_users():
            if u.get("email", "").strip().lower() == clean_email:
                return u
        return None

    def authenticate_user(self, email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Authenticates user by email and password."""
        user = self.get_user_by_email(email)
        if not user:
            return False, "No student account found with this email. Please create an account.", None

        if user.get("password_hash") != _hash_pw(password):
            return False, "Incorrect password. Please try again.", None

        self.log_activity("Student Login", f"{user.get('name')} signed in.")
        return True, "Login successful!", user

    def register_user(
        self,
        name: str,
        email: str,
        password: str,
        university: str = "",
        major: str = ""
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Registers a new student account."""
        clean_email = email.strip().lower()
        if not name.strip():
            return False, "Please enter your full name.", None
        if not clean_email or "@" not in clean_email:
            return False, "Please enter a valid academic or personal email.", None
        if len(password) < 6:
            return False, "Password must be at least 6 characters long.", None

        if self.get_user_by_email(clean_email):
            return False, "An account with this email already exists. Please sign in.", None

        data = self._load_raw()
        new_user = {
            "id": f"usr_{uuid.uuid4().hex[:8]}",
            "name": name.strip(),
            "email": clean_email,
            "university": university.strip() or "University Student",
            "major": major.strip() or "General Studies",
            "password_hash": _hash_pw(password),
            "avatar": "🎓",
            "auth_provider": "local",
            "created_at": datetime.now().isoformat()
        }
        if "users" not in data:
            data["users"] = []
        data["users"].append(new_user)
        self.log_activity("Account Created", f"New student registered: {name} ({clean_email})")
        self._save_raw(data)
        return True, "Account created successfully!", new_user

    def google_auth_user(
        self,
        email: str,
        name: str,
        avatar_url: str = "https://lh3.googleusercontent.com/a/default-user"
    ) -> Dict[str, Any]:
        """Handles 1-click Google authentication (creates or logs in existing user)."""
        clean_email = email.strip().lower()
        existing = self.get_user_by_email(clean_email)
        if existing:
            self.log_activity("Google Login", f"{existing.get('name')} signed in via Google.")
            return existing

        # Create new Google student user
        data = self._load_raw()
        new_user = {
            "id": f"usr_g_{uuid.uuid4().hex[:8]}",
            "name": name.strip(),
            "email": clean_email,
            "university": "Google Verified Student",
            "major": "Computer Science & Engineering",
            "password_hash": "",
            "avatar": "https://www.gstatic.com/images/branding/product/2x/googleg_48dp.png",
            "auth_provider": "google",
            "created_at": datetime.now().isoformat()
        }
        if "users" not in data:
            data["users"] = []
        data["users"].append(new_user)
        self.log_activity("Google Signup", f"New student joined via Google: {name} ({clean_email})")
        self._save_raw(data)
        return new_user


# Global singleton instance
storage = StorageManager()
