# Project Report — Corpus Forge
**Capstone: Generative AI for Software Engineering — EPITA 2026**

---

## Team Members

| Name | EPITA Email | GitHub |
|---|---|---|
| Youssef Kang | youssef.kang@epita.fr | kangyoussef95-max |
| Quang Phuc Hoang | quang-phuc.hoang@epita.fr | GaudiumX |

---

## 1. Initial Architecture

### Assumptions Made at the Start

- A single-user, local web application was sufficient — no multi-tenancy or authentication required.
- A relational database was the right persistence layer for documents, artifacts, and usage logs.
- Simple word-overlap retrieval could serve as the RAG foundation without needing vector embeddings or a vector database.
- A single-page app with no build steps (no React, no bundler) would keep setup simple and the deliverable self-contained.

### Initial Design

The application was designed as a Flask monolith with three layers:

**Backend (`app.py`)** — a single Python file handling all HTTP routes, business logic, database access, PDF parsing, retrieval, and AI calls. This was intentional: it keeps the entire system readable in one place and avoids import complexity for a short project.

**Database (`corpus.db`)** — SQLite with three tables:
- `documents` — stores ingested file content, filename, type, upload date, and an `is_active` flag for corpus management.
- `artifacts` — persists generated outputs (flashcards, quizzes, code reviews, architecture reports) as JSON blobs.
- `usage` — logs every AI call with workflow name, input tokens, output tokens, and timestamp for cost observability.

**Frontend (`templates/index.html`)** — a single HTML file with inline CSS and vanilla JavaScript. No external libraries, no CDN dependencies, no build step. The browser communicates with the backend via a JSON REST API.

### Technology Choices

| Component | Technology | Why |
|---|---|---|
| Web framework | Flask | Lightweight, familiar Python framework; routes map directly to features |
| Database | SQLite | Zero-configuration, file-based, sufficient for a local single-user app |
| LLM API | Groq (llama-3.3-70b-versatile) | Free tier, no billing required, fast inference |
| PDF parsing | PyMuPDF (fitz) | Reliable text extraction, handles multi-page PDFs |
| Frontend | Vanilla JS + inline CSS | No build tooling needed; keeps the deliverable self-contained |

---

## 2. Engineering Decisions

### Decision 1: LLM Provider Selection — Claude → Gemini → Groq

**Alternatives considered:** Anthropic Claude API, Google Gemini API, OpenAI GPT-4o-mini, Groq (llama-3.3-70b).

**What happened:** The first provider evaluated was the Anthropic Claude API. It was ruled out immediately because it requires billing information to activate even on the free tier — there is no way to use it without entering a credit card. The next candidate was Google Gemini (gemini-1.5-flash), which has a genuinely free tier with no billing required. A working prototype was built on top of Gemini. However, within the first real testing session, the free-tier quota (`RESOURCE_EXHAUSTED`) was hit and all AI endpoints began returning 500 errors. OpenAI similarly requires billing setup. Groq was then evaluated: it offers a free tier for llama-3.3-70b-versatile with no credit card required, and its API is OpenAI-compatible.

**Why Groq:** No billing, no quota issues within the project's usage volume, and a 70B-parameter model that is capable enough for all four artifact types.

**Trade-off:** Groq imposes rate limits, and the llama model occasionally has weaker instruction-following than GPT-4-class models, particularly for structured JSON outputs (flashcards, quiz). Mitigation: the `generate_artifact` function extracts JSON by searching for `[` and `]` boundaries and falls back gracefully if parsing fails.

---

### Decision 2: Word-Overlap RAG Over Semantic Embeddings

**Alternatives considered:** Semantic embedding search (e.g., sentence-transformers + FAISS or ChromaDB), BM25, pure keyword scan.

**Why word-overlap:** Embedding-based retrieval requires a vector database and an embedding model, adding significant setup complexity and either a second API call or a local model download. For a capstone prototype that must run locally with minimal dependencies, word-overlap retrieval is transparent, deterministic, and requires no additional infrastructure.

**Trade-off:** Word-overlap has no semantic understanding. A query about "machine learning" will not match a chunk that says "neural networks" without lexical overlap. This limits retrieval quality for paraphrase-heavy documents but is adequate for technical documents where terminology is consistent.

---

### Decision 3: Two Retrieval Strategies as Layer 2 Challenge A

The platform implements two selectable retrieval strategies, exposed to the user via radio buttons in the chat UI.

**Keyword frequency (default):** Scores each chunk by counting every chunk word that appears in the query, including repetitions. A chunk that repeats a query term five times scores five points for that term. This favors chunks with high topical density.

**TF uniqueness:** Scores each chunk by counting how many *distinct* query words appear at least once in the chunk (set intersection). This favors chunks that cover the broadest range of query terms, regardless of repetition frequency.

**Trade-off observed in testing:** Keyword frequency performs better for single-concept queries ("explain Flask routes") because dense repetition of relevant terms pushes a highly focused chunk to the top. TF uniqueness performs better for multi-term exploratory queries ("database schema artifacts persistence") because it rewards chunks that mention all queried terms even if none are repeated heavily.

The implementation in [app.py:92-99](app.py#L92) (`_top_chunks`) is compact and easy to extend with additional strategies (e.g., BM25) without changing the retrieval interface.

---

### Decision 4: Single-File Frontend, No Framework

**Alternatives considered:** React SPA, HTMX, Jinja2 templates per page.

**Why vanilla JS:** The project has one page and roughly six UI components (upload, document list, settings, chat, generate, artifacts). A framework adds build complexity with no functional benefit at this scale. The JavaScript in `index.html` is ~280 lines including a minimal markdown renderer, toast notifications, flashcard flip logic, and quiz state — all self-contained.

**Trade-off:** The file is long (~760 lines total) and would be harder to maintain at scale. Acceptable for a capstone prototype.

---

### Decision 5: Prompt Steering via Session

User settings (audience, tone, format, creativity) are stored server-side in Flask's session (cookie-backed) rather than in the database. This means settings persist for a browser session but reset on server restart.

**Why session over DB:** Settings are UI preferences, not corpus data. Storing them in a cookie avoids a fourth database table and per-user identity tracking. For a single-user local app this is the right scope.

**Trade-off:** Settings do not survive a server restart. If cross-session persistence of settings were required, they would need a `settings` table in the database.

---

## 3. Division of Work

| Area | Primary | Notes |
|---|---|---|
| Flask backend, routing, DB schema | Youssef | Core `app.py` structure, all route implementations |
| RAG retrieval pipeline | Youssef | `chunk_text`, `_top_chunks`, both scoring strategies |
| AI integration (Groq) | Youssef | `call_ai`, provider evaluation and switch |
| Frontend HTML/CSS/JS | Youssef | `templates/index.html`, all UI components |
| Prompt drafting (artifacts) | Youssef | Initial flashcard, quiz, code-review, architecture prompts |
| Prompt iteration (v1→v3) | Quang Phuc | Iterated prompts for reliable JSON output; added parser fallback |
| Manual testing | Quang Phuc | Tested all four artifact types across multiple sample corpora |
| Security review | Quang Phuc | May 26 session — found and fixed SECRET_KEY, upload limit, XSS, inverted flag |
| Documentation | Quang Phuc | REPORT.md decisions/failures sections, README, repo hygiene |

---

## 4. AI Collaboration

### Tools Used

| Tool | Purpose |
|---|---|
| GitHub Copilot (GPT-5 mini) | Primary code generation, Edit and Agent modes throughout development |

### How AI Was Used

**Scaffolding:** Copilot generated the initial Flask stub with TODO placeholders for all routes. This gave a working skeleton that could be filled in function by function without starting from a blank file.

**Implementation:** Copilot was used in Edit mode to implement each route function. The chat, flashcard, quiz, code-review, and architecture generation functions were all generated with Copilot assistance based on descriptive prompts.

**Bug diagnosis:** When the Gemini API failed with quota errors, Copilot was asked to diagnose the 500 responses. It correctly identified the `RESOURCE_EXHAUSTED` error and suggested switching providers, ultimately leading to the Groq migration.

**Security hardening:** Copilot was used to audit the codebase for vulnerabilities (May 26). It identified: hardcoded `SECRET_KEY`, missing `MAX_CONTENT_LENGTH`, potential XSS in document filename rendering, and the non-standard `requirements` filename. All four were fixed in the same session.

**Copilot instructions configuration:** A Socratic teaching mode was configured in `.github/copilot-instructions.md` as requested by the course. In this mode Copilot responds with guiding questions rather than direct code — useful for learning, but toggled off during rapid prototyping phases with "Just give me the answer."

### How AI Influenced Design

- The single-file architecture was partly a Copilot suggestion: it generated everything in `app.py` without proposing a module split, which turned out to be a reasonable choice for the project scope.
- The word-overlap retrieval strategy was chosen partly because Copilot could implement it in ~10 lines without external dependencies. Embedding-based retrieval would have required more scaffolding.
- Prompt templates for artifact generation (flashcard JSON schema, quiz JSON schema) were refined iteratively based on observed model outputs. The JSON extraction fallback (`raw.find("[")`) was added after Copilot's initial prompt caused the model to wrap the JSON in explanation text.

### Evaluating AI Suggestions

- Generated code was always read and understood before committing. Copilot occasionally suggested patterns that worked but were non-idiomatic (e.g., using `open()` with default encoding instead of explicit UTF-8).
- The security audit caught issues that Copilot had introduced itself (hardcoded secret key in the initial scaffold).
- AI-generated SQL was verified to use parameterized queries (no string formatting) to prevent SQL injection. All DB calls in `app.py` use `?` placeholders correctly.

---

## 5. Failures and Iterations

### Failure 1: Claude API Required Billing — Ruled Out

**What happened:** The first LLM provider evaluated was Anthropic's Claude API. After reading the documentation, it became clear that activating any tier requires entering billing information, even for free-tier usage. This was a hard blocker given the requirement to avoid credit card setup.

**Redesign:** Moved to Google Gemini, which at the time appeared to offer a no-billing free tier.

---

### Failure 2: Google Gemini API Quota Exhaustion

**What happened:** The prototype built on Gemini worked initially. Within the first real testing session (May 22), the free-tier quota (`RESOURCE_EXHAUSTED`) was hit. All four AI endpoints returned 500 errors.

**What was surprising:** The Gemini free tier is more restrictive than expected for a development workload. Even light testing of four artifact types exhausted it quickly.

**Redesign:** Switched to Groq. The change required replacing the `google-generativeai` import with the `groq` package and updating `call_ai()` to use the Groq chat completions API. The interface (`call_ai(system, user, workflow, temperature)`) was preserved so all callers remained unchanged.

---

### Failure 3: Hardcoded Secret Key and Missing Upload Limit

**What happened:** The initial scaffold had `SECRET_KEY = "dev-only-secret"` hardcoded in `app.py`. There was also no `MAX_CONTENT_LENGTH`, meaning a user could upload arbitrarily large files and exhaust server memory.

**Detection:** Code review (May 26).

**Fix:** Moved to `os.environ.get("SECRET_KEY", "dev-only-secret")` with a note that production must set this. Added `MAX_CONTENT_LENGTH = 5 * 1024 * 1024` (5 MB cap).

---

### Failure 4: XSS Risk in Document Filename Display

**What happened:** The document list in `index.html` rendered filenames with `.innerHTML` and string interpolation. A filename like `<script>alert(1)</script>.txt` would execute in the browser.

**Detection:** Code review (May 26).

**Fix:** Added `escAttr()` and applied `escHtml()` consistently to all user-controlled strings before inserting into the DOM. The `escHtml()` function was already present in the codebase but was not applied to filenames.

---

### Failure 5: Non-Standard Requirements File

**What happened:** The dependency file was named `requirements` (no extension), which `pip install -r` accepts but which breaks most IDE tooling and CI/CD conventions.

**Fix:** Added a standard `requirements.txt` file. The README was updated to reference it.

---

### What Required Redesign

The only architectural redesign was the AI provider selection process (Claude → Gemini → Groq). Everything else was a localized bug fix. The core RAG pipeline, database schema, and frontend architecture remained stable from the initial prototype through the final version.

---

## 6. "When AI Was Wrong or Incomplete"

### Case 1: Initial Scaffold Used Wrong Gemini Model

The first Copilot-generated `call_ai` function referenced `gemini-pro`, a deprecated model. API calls failed with a model-not-found error until the model string was corrected to `gemini-1.5-flash`. Lesson: always verify generated API call signatures against current provider documentation rather than trusting AI-generated model names.

### Case 2: JSON Extraction Fragility

Copilot's initial flashcard and quiz prompts were phrased as: "Return JSON like: [...]". The model frequently wrapped the JSON in a sentence like "Here are the flashcards: [...]". The generated parsing code called `json.loads(raw)` directly, causing `json.JSONDecodeError` on every real response.

**Fix:** The prompt was hardened to "Return ONLY a JSON array" and the parsing was made robust by searching for `[` and `]` boundaries, then falling back to `{"raw": raw}` if parsing still fails.

### Case 3: Inverted Retrieval Strategy Logic

The initial `_top_chunks` function had the `unique` flag logic inverted: the TF uniqueness path was executing for the keyword strategy and vice versa. The bug was silent — both strategies returned plausible results, just not the intended ones. Detected only by manually comparing outputs between the two strategies with known test documents. Lesson: AI-generated scoring and ranking logic needs explicit test cases with expected outputs, not just eyeball review.

---

## 7. Lessons Learned

### Technical Growth

- **RAG without vectors is viable for constrained use cases.** Word-overlap retrieval is fast, transparent, and requires no additional infrastructure. For technical documents with consistent vocabulary it produces acceptable results. For general-purpose semantic search over large, paraphrase-heavy corpora, embeddings would be necessary.
- **Free-tier API selection matters and should be evaluated before building.** Spending 30 minutes evaluating each provider's actual billing requirements before writing code would have avoided two provider switches. The evaluation criteria should be explicit: does it require a credit card? What are the rate limits? What models are available?
- **Single-file Flask apps are practical for small projects.** Keeping everything in `app.py` made it easy for both team members to read the full system. The cost is that the file becomes long (~380 lines) and would need refactoring at scale.

### Workflow Improvements

- **Using Copilot in Edit mode with specific function-level prompts** produced better results than asking it to generate entire files at once. Smaller scopes meant easier review and fewer surprises.
- **Keeping a JOURNAL.md and prompt history** made it easy to reconstruct what was tried, in what order, and why. This is genuinely useful when two people need to understand each other's changes without real-time communication.
- **Toggling Socratic mode** was a practical design. When learning a new concept, the guided-questioning mode is valuable. When on a deadline implementing a known pattern, it slows things down unnecessarily. The explicit toggle was the right approach.

### Strengths and Limitations of AI-Assisted Development

**Strengths:**
- Scaffolding and boilerplate generation is fast and mostly correct. The Flask route structure, SQLite schema, and HTML/CSS skeleton were all generated in minutes.
- Debugging known error patterns (quota errors, JSON parsing failures) is well-handled because these are common, well-documented problems with known solutions in the training data.
- Security auditing surfaced issues that were easy to miss during rapid development.

**Limitations:**
- AI tools do not catch silent logic errors. The inverted retrieval strategy bug passed all AI-assisted review because the code was syntactically correct and produced plausible output. Only manual testing caught it.
- Prompt engineering for structured JSON output required iteration that AI tools could not automate — each test round exposed a new edge case in model output format.
- AI cannot substitute for understanding the domain. The decision to use word-overlap instead of embeddings required understanding what embeddings actually do and why they require a vector database. That understanding had to come from reading documentation and course material, not from AI-generated output.