"""
InterviewAI — Flask microservice
=================================
Generates role-specific, experience-aware interview question sets via the
Google Gemini API, persists them as local JSON history, and exports any
session to a formatted Word (.docx) document.

Run with:  python app.py
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request, send_file

load_dotenv()

from docx_export import build_docx
from gemini_service import GeminiConfigError, GeminiGenerationError, generate_questions
import history_store

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

VALID_EXPERIENCE_LEVELS = {"beginner", "intermediate", "advanced"}
VALID_INTERVIEW_TYPES = {"technical", "behavioral", "situational", "mixed"}


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/generate", methods=["POST"])
def api_generate():
    body = request.get_json(silent=True) or {}

    role = (body.get("role") or "").strip()
    experience_level = (body.get("experience_level") or "intermediate").strip().lower()
    interview_type = (body.get("interview_type") or "mixed").strip().lower()
    notes = (body.get("notes") or "").strip()

    try:
        num_questions = int(body.get("num_questions", 5))
    except (TypeError, ValueError):
        num_questions = 5
    num_questions = max(1, min(num_questions, 15))

    if not role:
        return jsonify({"error": "Please provide a job role, e.g. 'Senior React Developer'."}), 400
    if experience_level not in VALID_EXPERIENCE_LEVELS:
        return jsonify({"error": f"experience_level must be one of {sorted(VALID_EXPERIENCE_LEVELS)}"}), 400
    if interview_type not in VALID_INTERVIEW_TYPES:
        return jsonify({"error": f"interview_type must be one of {sorted(VALID_INTERVIEW_TYPES)}"}), 400

    try:
        result = generate_questions(role, experience_level, interview_type, num_questions, notes)
    except GeminiConfigError as exc:
        return jsonify({"error": str(exc), "code": "missing_api_key"}), 500
    except GeminiGenerationError as exc:
        return jsonify({"error": str(exc), "code": "generation_failed"}), 502

    saved = history_store.save_session(result)
    return jsonify(saved), 201


@app.route("/api/history", methods=["GET"])
def api_history_list():
    return jsonify(history_store.list_sessions())


@app.route("/api/history/<session_id>", methods=["GET"])
def api_history_get(session_id):
    session = history_store.get_session(session_id)
    if session is None:
        return jsonify({"error": "Session not found."}), 404
    return jsonify(session)


@app.route("/api/history/<session_id>", methods=["DELETE"])
def api_history_delete(session_id):
    deleted = history_store.delete_session(session_id)
    if not deleted:
        return jsonify({"error": "Session not found."}), 404
    return jsonify({"deleted": session_id})


@app.route("/api/export/<session_id>", methods=["POST"])
def api_export(session_id):
    session = history_store.get_session(session_id)
    if session is None:
        return jsonify({"error": "Session not found."}), 404

    path = build_docx(session)
    return send_file(
        path,
        as_attachment=True,
        download_name=os.path.basename(path),
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({
        "status": "ok",
        "gemini_key_configured": bool(os.environ.get("GEMINI_API_KEY")),
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "True").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
