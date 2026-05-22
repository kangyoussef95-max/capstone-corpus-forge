# Capstone Project: Corpus Forge

RAG-powered document intelligence app — upload files, chat with them, generate flashcards, quizzes, code reviews, and architecture reports using Groq (free, no billing required).

## Setup

**1. Clone and create a virtual environment**
```bash
python -m venv .venv
.venv\Scripts\activate      # Windows
source .venv/bin/activate   # Mac/Linux
```

**2. Install dependencies**
```bash
pip install -r requirements
```

**3. Add your API key**
```bash
copy .env.example .env      # Windows
cp .env.example .env        # Mac/Linux
```
Open `.env` and replace `your-groq-api-key-here` with your free key from [groq.com](https://groq.com) → sign up with Google → API Keys → Create API key. No billing required.

**4. Run**
```bash
python app.py
```

Open [http://localhost:5000](http://localhost:5000) in your browser.

## Features

- Upload `.txt`, `.md`, `.pdf`, `.py`, `.js` files
- Toggle which documents are active for context
- Chat with your documents using RAG retrieval
- Two retrieval strategies: keyword overlap vs TF uniqueness (Challenge A)
- Generate flashcards, quizzes, code reviews, architecture reports
- Prompt steering: audience, tone, format, creativity
- Request count and token usage tracking
