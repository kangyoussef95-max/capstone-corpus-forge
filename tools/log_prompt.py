#!/usr/bin/env python3
"""Simple prompt/journal logger for local activation.

Usage:
  python tools/log_prompt.py --prompt "your prompt text" [--user name]

This script appends a prompt entry to `prompts_history.md` and a journal-style
entry to `JOURNAL.md` using UTF-8 and basic validation safeguards.
"""
import argparse
import datetime
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
JOURNAL = ROOT / "JOURNAL.md"
PROMPTS = ROOT / "prompts_history.md"


def validate(text: str) -> None:
    # Reject obvious corruption patterns: single letters separated by spaces
    if re.search(r"\b(?:[A-Za-z])(?:\s+[A-Za-z]){2,}\b", text):
        raise ValueError("Input looks like single-letter tokens separated by spaces")
    if "* *" in text or " - " in text:
        raise ValueError("Input contains suspicious spacing patterns")


def append_prompts(prompt: str, ts: str) -> None:
    with PROMPTS.open("a", encoding="utf-8") as f:
        f.write(f"### {ts}\n- **Prompt**: {prompt}\n\n")


def append_journal(prompt: str, ts: str, user: str) -> None:
    entry = (
        "### **New Interaction**\n"
        f"- **Agent Version**: local-logger\n"
        f"- **Date**: {ts}\n"
        f"- **User**: {user}\n"
        f"- **Prompt**: {prompt}\n"
        "- **CoPilot Mode**: Ask\n"
        "- **CoPilot Model**: local\n"
        "- **Socratic Mode**: OFF\n"
        "- **Changes Made**: no changes\n"
        "- **Context and Reasons for Changes**: Activated local logging script for prompts and journal.\n\n"
    )
    with JOURNAL.open("a", encoding="utf-8") as f:
        f.write(entry)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--prompt", "-p", required=True, help="Prompt text to log")
    p.add_argument("--user", "-u", default="$USER", help="User identity to record")
    args = p.parse_args()

    prompt = args.prompt.strip()
    user = args.user
    ts = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")

    validate(prompt)
    append_prompts(prompt, ts)
    append_journal(prompt, ts, user)

    # Print last few lines of JOURNAL.md for verification
    with JOURNAL.open("r", encoding="utf-8") as f:
        lines = f.read().splitlines()
    print("--- Last journal lines ---")
    for ln in lines[-12:]:
        print(ln)


if __name__ == "__main__":
    main()
