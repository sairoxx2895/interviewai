"""
gemini_service.py
------------------
All interaction with the Google Gemini API lives here. The rest of the app
never talks to the model directly - it just calls generate_questions() and
gets back clean, already-validated Python data.
"""

import json
import os
import re

import google.generativeai as genai

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class GeminiConfigError(RuntimeError):
    """Raised when the service is asked to run without a configured API key."""


class GeminiGenerationError(RuntimeError):
    """Raised when Gemini responds but the output can't be turned into valid data."""


SYSTEM_INSTRUCTIONS = """You are InterviewAI, an expert technical recruiter and interview
designer. You write sharp, role-specific interview questions and give
recruiters (who may not be technical experts themselves) the context they
need to judge an answer fairly. You always respond with STRICT JSON only -
no markdown fences, no commentary, no leading or trailing text."""


def _build_prompt(role: str, experience_level: str, interview_type: str, num_questions: int, notes: str) -> str:
    focus = {
        "technical": "purely technical / hands-on skill questions",
        "behavioral": "behavioral and soft-skill questions using formats like STAR",
        "situational": "hypothetical, scenario-based / situational judgement questions",
        "mixed": "a balanced mix of technical, behavioral, and situational questions",
    }.get(interview_type.lower(), "a balanced mix of technical, behavioral, and situational questions")

    extra_context = f"\nAdditional organizational context to weave in: {notes.strip()}" if notes else ""

    return f"""Generate exactly {num_questions} interview questions for a "{role}" role,
targeting a candidate at the "{experience_level}" experience level.
Focus on {focus}.{extra_context}

For EACH question return an object with these exact keys:
- "category": one of "Technical", "Behavioral", "Situational"
- "question": the interview question itself, written to be asked out loud
- "follow_up": one natural follow-up/probing question an interviewer can use
- "evaluation_tip": one or two sentences telling a recruiter (even a non-technical one) what a strong answer sounds like
- "green_flags": an array of 3 short strings describing positive signals to watch for
- "red_flags": an array of 3 short strings describing warning signs to watch for
- "scoring_guide": an object with keys "1_2", "3", "4_5" mapping to short descriptions of what that score range looks like on a 1-5 scale

Return ONLY a single JSON object with this exact top-level shape, nothing else:
{{
  "role": "{role}",
  "experience_level": "{experience_level}",
  "interview_type": "{interview_type}",
  "overall_evaluation_notes": "2-3 sentences of general guidance for whoever runs this interview",
  "questions": [ /* {num_questions} question objects as described above */ ]
}}"""


def _extract_json(raw_text: str) -> dict:
    """Gemini almost always returns clean JSON, but defensively strip any
    accidental ```json fences or stray text around the object."""
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fall back to grabbing the outermost { ... } block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise GeminiGenerationError("Gemini's response did not contain valid JSON.")
        return json.loads(match.group(0))


def generate_questions(role: str, experience_level: str, interview_type: str,
                        num_questions: int = 5, notes: str = "") -> dict:
    if not GEMINI_API_KEY:
        raise GeminiConfigError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=SYSTEM_INSTRUCTIONS,
        generation_config={
            "temperature": 0.7,
            "response_mime_type": "application/json",
        },
    )

    prompt = _build_prompt(role, experience_level, interview_type, num_questions, notes)

    try:
        response = model.generate_content(prompt)
    except Exception as exc:  # network / auth / quota errors from the SDK
        raise GeminiGenerationError(f"Gemini API request failed: {exc}") from exc

    if not getattr(response, "text", None):
        raise GeminiGenerationError("Gemini returned an empty response.")

    data = _extract_json(response.text)

    # Light validation / normalization so the frontend can rely on the shape
    data.setdefault("role", role)
    data.setdefault("experience_level", experience_level)
    data.setdefault("interview_type", interview_type)
    data["questions"] = data.get("questions", [])[:num_questions] or data.get("questions", [])
    for i, q in enumerate(data["questions"], start=1):
        q.setdefault("id", i)
        q.setdefault("green_flags", [])
        q.setdefault("red_flags", [])
        q.setdefault("scoring_guide", {})

    return data
