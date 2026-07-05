"""
history_store.py
-----------------
Very small, dependency-free persistence layer for InterviewAI.

Every generated question-set is written to disk as its own JSON file inside
HISTORY_DIR. This gives the app "free" persistence (no database to run)
while still letting a recruiter reopen a past session instantly, without
spending another Gemini API call/quota.
"""

import json
import os
import uuid
from datetime import datetime

HISTORY_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "history")
os.makedirs(HISTORY_DIR, exist_ok=True)


def _path_for(session_id: str) -> str:
    return os.path.join(HISTORY_DIR, f"{session_id}.json")


def save_session(payload: dict) -> dict:
    """Persist a newly generated question set and return the stored record."""
    session_id = str(uuid.uuid4())
    record = {
        "id": session_id,
        "created_at": datetime.utcnow().isoformat() + "Z",
        **payload,
    }
    with open(_path_for(session_id), "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
    return record


def list_sessions() -> list:
    """Return lightweight summaries of every saved session, newest first."""
    summaries = []
    for filename in os.listdir(HISTORY_DIR):
        if not filename.endswith(".json"):
            continue
        try:
            with open(os.path.join(HISTORY_DIR, filename), "r", encoding="utf-8") as f:
                data = json.load(f)
            summaries.append({
                "id": data.get("id"),
                "role": data.get("role"),
                "experience_level": data.get("experience_level"),
                "interview_type": data.get("interview_type"),
                "num_questions": len(data.get("questions", [])),
                "created_at": data.get("created_at"),
            })
        except (json.JSONDecodeError, OSError):
            # Skip corrupt / unreadable files instead of crashing the app
            continue
    summaries.sort(key=lambda s: s.get("created_at") or "", reverse=True)
    return summaries


def get_session(session_id: str):
    path = _path_for(session_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_session(session_id: str) -> bool:
    path = _path_for(session_id)
    if not os.path.exists(path):
        return False
    os.remove(path)
    return True
