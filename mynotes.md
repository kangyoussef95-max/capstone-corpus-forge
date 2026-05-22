# My Notes — Corpus Forge

## General idea

Single Flask app, everything in app.py. One HTML page that does everything.
Use Claude API (anthropic package), model claude-sonnet-4-6.
Store everything in a SQLite database so it persists between runs.
Plain HTML + a bit of JS, no frontend framework.

---

## File upload / ingestion

User picks a file, server extracts plain text from it:
- .txt and .md → read directly
- .pdf → use PyMuPDF (fitz) to extract text page by page
- .py and .js → read as plain text

Save filename, filetype, extracted text, and upload date to the database.

---

## Corpus management

One documents table: id, filename, filetype, content, upload_date, is_active.
UI shows the list. Each row has a delete button and a checkbox to mark it active.
Only active documents get sent to Claude.

---

## Retrieval

For RAG, just concatenate all active document content and send it as context.
If it gets too long, split into 500-word chunks and pick the top 3 chunks that
contain the most query keywords (simple word overlap, no embeddings needed).

For Challenge A: also implement a second strategy where instead of keyword overlap,
rank chunks by how many unique query words they contain (TF style). Compare both,
write up which works better in REPORT.md. No external libraries needed for either.

---

## AI workflows

All call Claude with: system prompt (from prompt steering) + context + user request.

### Chat
User asks a question → retrieve context → call Claude → return the answer.

### Flashcards
Tell Claude to return JSON like: [{"front": "...", "back": "..."}]
Parse it, save to db, show with a flip effect on the page.

### Quiz
Tell Claude to return JSON like: [{"question": "...", "options": ["a","b","c","d"], "answer": 0}]
Parse it, save to db, show with a submit button and score.

### Code review
Only when .py or .js files are active. Send the code to Claude, ask for a review.
Returns markdown. Save to db.

### Architecture report
Same as code review but ask for module structure and data flow instead. Save to db.

---

## Prompt steering

User can set these before any generation:
- audience: beginner / intermediate / expert
- tone: formal / casual / technical
- format: bullet points / prose / markdown
- creativity: low / medium / high → temperature 0.2 / 0.7 / 1.0

Inject into the system prompt: "You are helping a {audience} audience. Tone: {tone}. Format: {format}."
Save to Flask session so user doesn't have to reset each time.

---

## Persistence

SQLite file corpus.db. Tables:
- documents: id, filename, filetype, content, upload_date, is_active
- artifacts: id, type (flashcards/quiz/code_review/architecture), content_json, created_at
- usage: id, workflow, input_tokens, output_tokens, created_at

Create tables on startup if they don't exist.

---

## Cost tracking

After every Claude call, log to usage table using response.usage.input_tokens and output_tokens.
Show totals on a simple stats section of the page.

---

## Routes

GET  /                        → main page
POST /upload                  → upload + ingest file
POST /documents/<id>/delete   → delete document
POST /documents/<id>/toggle   → toggle is_active
POST /chat                    → chat Q&A
POST /generate/<type>         → type = flashcards | quiz | code-review | architecture
GET  /artifacts               → return all saved artifacts as JSON
GET  /stats                   → return token usage totals
POST /settings                → save prompt steering to session

---

## Layer 2 choices

Challenge A (retrieval): keyword overlap vs keyword uniqueness ranking — simple, no extra deps.
Challenge B (prompt engineering): iterate on flashcard/quiz prompts, log each version in JOURNAL.md.

---

## Tech stack

- Python + Flask
- anthropic
- PyMuPDF (fitz)
- SQLite (stdlib)
- Plain HTML/CSS/JS
