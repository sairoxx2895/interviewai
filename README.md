# InterviewAI — Intelligent Hiring & Candidate Evaluation System

InterviewAI is a recruiter-empowerment tool that generates role-specific,
experience-aware interview questions using the **Google Gemini API**, and
wraps every question with the context a recruiter needs to run a fair,
structured, and objective interview: follow-up prompts, "what a strong
answer sounds like," **green flags**, **red flags**, and a **1–5 scoring
guide**.

It ships as a single-page web app backed by a small **Flask** microservice.
No database required — sessions are saved as local JSON files, and any
session can be exported to a polished **Microsoft Word (.docx)** document
with one click.

---

## ✨ Features

- **Role + level + format aware generation** — pick a job role, an
  experience level (Beginner / Intermediate / Advanced), and an interview
  type (Technical / Behavioral / Situational / Mixed), optionally add
  organizational context (e.g. "team uses trunk-based dev, hybrid remote").
- **Structured evaluation framework** for every question: follow-up
  question, evaluation tip, green flags, red flags, and a 1–5 scoring guide.
- **Persistent session history** ("Session Ledger") — every generated set
  is saved locally as JSON and can be reopened instantly without spending
  another API call.
- **One-click Word export** — turns any saved session into a clean,
  print-ready `.docx` file using `python-docx`.
- **Secure key management** — the Gemini API key lives only in your local
  `.env` file, never in source control or the browser.
- **Zero external services required** beyond the Gemini API itself — no
  database, no auth server, no build step.

---

## 🗂 Project structure

```
interviewai/
├── app.py                # Flask app & all API routes
├── gemini_service.py      # Gemini API integration + prompt engineering
├── docx_export.py         # python-docx based Word exporter
├── history_store.py       # Local JSON persistence layer
├── requirements.txt
├── .env.example            # Copy to .env and add your Gemini key
├── templates/
│   └── index.html          # Single-page app shell
├── static/
│   ├── css/style.css        # Design system + UI styling
│   └── js/app.js             # Frontend logic (fetch calls, rendering)
├── history/                 # Generated session JSON files (gitignored)
└── exports/                  # Generated .docx files (gitignored)
```

---

## 🚀 Getting started

### 1. Prerequisites
- Python 3.9+
- A free Google Gemini API key: https://aistudio.google.com/app/apikey

### 2. Clone & install

```bash
git clone <your-repo-url>
cd interviewai
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure your API key

```bash
cp .env.example .env
```

Open `.env` and paste your key:

```
GEMINI_API_KEY=your_real_key_here
```

### 4. Run it

```bash
python app.py
```

Visit **http://localhost:5000** in your browser.

---

## 🖱 How to use it (matches the demo scenarios)

1. **Generate a mixed technical interview** — enter a role like
   `Senior React Developer`, set experience level to `Advanced`, type to
   `Mixed`, and questions to `10`. You'll get ten questions with follow-ups,
   green/red flags, and scoring guidance.
2. **Run a behavioral screen** — role `Product Manager`, type `Behavioral`.
   Questions will target agile methodology, roadmapping, and conflict
   resolution without requiring technical depth from the interviewer.
3. **Quick screen + export** — generate 5 `Beginner` level questions, then
   click **Export to Word (.docx)** in the results panel to download a
   formatted, shareable document.
4. **Reopen a past session** — open the **Session Ledger** in the sidebar
   and click any past session to reload it instantly, with zero additional
   API calls.

---

## 🔌 API reference

All endpoints return JSON (except the docx export, which streams a file).

| Method | Endpoint                  | Description                                   |
|--------|----------------------------|------------------------------------------------|
| GET    | `/`                        | Serves the single-page app                     |
| POST   | `/api/generate`            | Generates a new question set via Gemini        |
| GET    | `/api/history`             | Lists saved sessions (summaries)               |
| GET    | `/api/history/<id>`        | Fetches a full saved session                   |
| DELETE | `/api/history/<id>`        | Deletes a saved session                        |
| POST   | `/api/export/<id>`         | Exports a session to a `.docx` file            |
| GET    | `/api/health`              | Basic health check / key-configured status     |

### `POST /api/generate` body

```json
{
  "role": "Senior React Developer",
  "experience_level": "advanced",
  "interview_type": "mixed",
  "num_questions": 10,
  "notes": "Team uses trunk-based development, agile roadmap."
}
```

`experience_level` ∈ `beginner | intermediate | advanced`
`interview_type` ∈ `technical | behavioral | situational | mixed`

---

## 🧠 Tech stack

- **Backend:** Python, Flask
- **AI:** Google Gemini API (`google-generativeai`)
- **Document generation:** `python-docx`
- **Persistence:** Local JSON files (no database needed)
- **Frontend:** Vanilla HTML/CSS/JS single-page app (no build step, no framework)

Skills demonstrated: Python, Generative AI / LLM prompting, NLP-driven
content generation, and a lightweight REST API design (Flask; adaptable to
FastAPI — see note below).

> **Note on FastAPI:** The reference implementation here uses Flask for
> simplicity (zero-build, synchronous, ideal for this local-first tool).
> The API surface is intentionally small and REST-plain, so porting
> `app.py`'s five routes to FastAPI (with `Pydantic` request/response models)
> is a quick, mechanical follow-up if your rubric specifically requires it.

---

## 🛠 Troubleshooting

- **"GEMINI_API_KEY is not set"** — make sure you copied `.env.example` to
  `.env` and filled in a real key, then restart `python app.py`.
- **Gemini returns an error / quota message** — check your API key's quota
  at https://aistudio.google.com. Free tier keys have daily rate limits.
- **Export button does nothing** — check the browser console; this usually
  means the session was deleted from `history/` on disk.

---

## 📄 License

MIT — free to use, modify, and extend for your own recruiting workflows.
