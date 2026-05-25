from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import os

import fitz  # PyMuPDF
from groq import Groq
from flask import Flask, jsonify, render_template, request, session

# Initialize Groq client only when an API key is present
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
if GROQ_API_KEY:
    _ai = Groq(api_key=GROQ_API_KEY)
else:
    _ai = None

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "corpus.db"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-secret")
# Limit uploads to a reasonable size (5 MB)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB


@app.errorhandler(Exception)
def handle_error(e):
    app.logger.exception(e)
    return jsonify({"error": str(e)}), 500

# ---------------------------------------------------------------------------
# DB
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                filename    TEXT    NOT NULL,
                filetype    TEXT    NOT NULL,
                content     TEXT    NOT NULL,
                upload_date TEXT    NOT NULL,
                is_active   INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS artifacts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                type         TEXT    NOT NULL,
                content_json TEXT    NOT NULL,
                created_at   TEXT    NOT NULL
            );
            CREATE TABLE IF NOT EXISTS usage (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                workflow      TEXT    NOT NULL,
                input_tokens  INTEGER NOT NULL,
                output_tokens INTEGER NOT NULL,
                created_at    TEXT    NOT NULL
            );
        """)


# ---------------------------------------------------------------------------
# RAG
# ---------------------------------------------------------------------------

def get_active_content() -> str:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT content FROM documents WHERE is_active=1"
        ).fetchall()
    return "\n\n".join(r["content"] for r in rows)


def chunk_text(text: str, size: int = 500) -> list[str]:
    words = text.split()
    return [" ".join(words[i : i + size]) for i in range(0, len(words), size)]


def _top_chunks(chunks: list[str], query: str, n: int, unique: bool) -> list[str]:
    q_words = set(query.lower().split())
    if unique:
        scored = [(len(q_words & set(c.lower().split())), c) for c in chunks]
    else:
        scored = [(sum(1 for w in c.lower().split() if w in q_words), c) for c in chunks]
    scored.sort(key=lambda x: x[0], reverse=True)
    return [c for _, c in scored[:n]]


def retrieve_context(query: str, strategy: str = "keyword") -> str:
    content = get_active_content()
    if not content:
        return ""
    if len(content.split()) <= 500:
        return content
    chunks = chunk_text(content)
    return "\n\n".join(_top_chunks(chunks, query, 3, unique=(strategy == "tf")))


# ---------------------------------------------------------------------------
# Prompt steering
# ---------------------------------------------------------------------------

DEFAULT_SETTINGS: dict[str, str] = {
    "audience": "intermediate",
    "tone": "formal",
    "format": "markdown",
    "creativity": "medium",
}
TEMPERATURE_MAP = {"low": 0.2, "medium": 0.7, "high": 1.0}


def get_settings() -> dict[str, str]:
    s = DEFAULT_SETTINGS.copy()
    s.update(session.get("settings", {}))
    return s


def build_system_prompt(settings: dict[str, str]) -> str:
    return (
        f"You are helping a {settings['audience']} audience. "
        f"Tone: {settings['tone']}. Format: {settings['format']}."
    )


# ---------------------------------------------------------------------------
# Groq
# ---------------------------------------------------------------------------

def call_ai(system: str, user: str, workflow: str, temperature: float = 0.7) -> str:
    if _ai is None:
        raise RuntimeError("GROQ_API_KEY is not configured. Set GROQ_API_KEY in the environment to enable AI calls.")

    resp = _ai.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=temperature,
        max_tokens=2048,
    )
    input_tokens = resp.usage.prompt_tokens or 0
    output_tokens = resp.usage.completion_tokens or 0
    with get_db() as conn:
        conn.execute(
            "INSERT INTO usage (workflow, input_tokens, output_tokens, created_at) "
            "VALUES (?,?,?,?)",
            (workflow, input_tokens, output_tokens, datetime.now(timezone.utc).isoformat()),
        )
    return resp.choices[0].message.content


# ---------------------------------------------------------------------------
# Route implementations
# ---------------------------------------------------------------------------

def ingest_upload():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "No file provided"}), 400
    filename = f.filename
    ext = Path(filename).suffix.lower()
    if ext in (".txt", ".md", ".py", ".js"):
        content = f.read().decode("utf-8", errors="replace")
    elif ext == ".pdf":
        data = f.read()
        doc = fitz.open(stream=data, filetype="pdf")
        content = "\n".join(page.get_text() for page in doc)
    else:
        return jsonify({"error": f"Unsupported file type: {ext}"}), 400
    with get_db() as conn:
        conn.execute(
            "INSERT INTO documents (filename, filetype, content, upload_date, is_active) "
            "VALUES (?,?,?,?,1)",
            (filename, ext.lstrip("."), content, datetime.now(timezone.utc).isoformat()),
        )
    return jsonify({"status": "ok", "filename": filename})


def delete_document(document_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM documents WHERE id=?", (document_id,))
    return jsonify({"status": "ok"})


def toggle_document(document_id: int):
    with get_db() as conn:
        conn.execute(
            "UPDATE documents SET is_active = 1 - is_active WHERE id=?", (document_id,)
        )
        row = conn.execute(
            "SELECT is_active FROM documents WHERE id=?", (document_id,)
        ).fetchone()
    return jsonify({"status": "ok", "is_active": bool(row["is_active"]) if row else False})


def run_chat():
    data = request.get_json(force=True)
    query = (data.get("query") or "").strip()
    if not query:
        return jsonify({"error": "No query"}), 400
    strategy = data.get("strategy", "keyword")
    context = retrieve_context(query, strategy)
    settings = get_settings()
    system = build_system_prompt(settings)
    user_msg = f"Context:\n{context}\n\nQuestion: {query}" if context else query
    answer = call_ai(system, user_msg, "chat", TEMPERATURE_MAP[settings["creativity"]])
    return jsonify({"answer": answer})


def generate_artifact(artifact_type: str):
    data = request.get_json(force=True, silent=True) or {}
    query = (data.get("query") or "summarize the content").strip()
    context = retrieve_context(query)
    settings = get_settings()
    system = build_system_prompt(settings)
    temp = TEMPERATURE_MAP[settings["creativity"]]

    if artifact_type == "flashcards":
        user_msg = (
            "Based on the following content, generate 5-10 flashcards as JSON.\n"
            'Return ONLY a JSON array like: [{"front": "...", "back": "..."}]\n\n'
            f"Content:\n{context}"
        )
    elif artifact_type == "quiz":
        user_msg = (
            "Based on the following content, generate 5 multiple-choice questions as JSON.\n"
            'Return ONLY a JSON array like: [{"question": "...", "options": ["a","b","c","d"], "answer": 0}]\n\n'
            f"Content:\n{context}"
        )
    elif artifact_type == "code-review":
        user_msg = f"Review the following code and provide detailed feedback:\n\n{context}"
    elif artifact_type == "architecture":
        user_msg = (
            "Describe the module structure and data flow of the following code:\n\n"
            f"{context}"
        )
    else:
        return jsonify({"error": f"Unknown type: {artifact_type}"}), 400

    if not context:
        return jsonify({"error": "No active documents to work with"}), 400

    raw = call_ai(system, user_msg, artifact_type, temp)

    if artifact_type in ("flashcards", "quiz"):
        try:
            start, end = raw.find("["), raw.rfind("]") + 1
            parsed = json.loads(raw[start:end])
            content_json = json.dumps(parsed)
        except (ValueError, json.JSONDecodeError):
            content_json = json.dumps({"raw": raw})
    else:
        content_json = json.dumps({"text": raw})

    with get_db() as conn:
        conn.execute(
            "INSERT INTO artifacts (type, content_json, created_at) VALUES (?,?,?)",
            (artifact_type, content_json, datetime.now(timezone.utc).isoformat()),
        )
    return jsonify({"status": "ok", "result": json.loads(content_json)})


def list_artifacts():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM artifacts ORDER BY created_at DESC"
        ).fetchall()
    return jsonify({"artifacts": [dict(r) for r in rows]})


def get_stats():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT workflow, COUNT(*) as requests, "
            "SUM(input_tokens) as input, SUM(output_tokens) as output "
            "FROM usage GROUP BY workflow"
        ).fetchall()
        total = conn.execute(
            "SELECT COUNT(*) as requests, "
            "SUM(input_tokens) as input, SUM(output_tokens) as output FROM usage"
        ).fetchone()
    return jsonify(
        {
            "by_workflow": [dict(r) for r in rows],
            "total_requests": total["requests"] or 0,
            "total_input": total["input"] or 0,
            "total_output": total["output"] or 0,
        }
    )


def save_settings():
    data = request.get_json(force=True)
    allowed = {"audience", "tone", "format", "creativity"}
    session["settings"] = {k: v for k, v in data.items() if k in allowed}
    return jsonify({"status": "ok", "settings": session["settings"]})


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/")
def index():
    return render_template("index.html")


@app.get("/documents")
def documents_list():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, filename, filetype, upload_date, is_active FROM documents ORDER BY id DESC"
        ).fetchall()
    return jsonify({"documents": [dict(r) for r in rows]})


@app.post("/upload")
def upload():
    return ingest_upload()


@app.post("/documents/<int:document_id>/delete")
def document_delete(document_id: int):
    return delete_document(document_id)


@app.post("/documents/<int:document_id>/toggle")
def document_toggle(document_id: int):
    return toggle_document(document_id)


@app.post("/chat")
def chat():
    return run_chat()


@app.post("/generate/<artifact_type>")
def generate(artifact_type: str):
    return generate_artifact(artifact_type)


@app.get("/artifacts")
def artifacts():
    return list_artifacts()


@app.get("/stats")
def stats():
    return get_stats()


@app.post("/settings")
def settings():
    return save_settings()


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(debug=True)
