## Activating prompt & journal logging

This repository includes a simple local logger to append prompts to `prompts_history.md`
and journal entries to `JOURNAL.md`.

Files:
- `tools/log_prompt.py` — Python script to append entries safely.
- `tools/log_prompt.ps1` — PowerShell wrapper for Windows.

Usage examples:

PowerShell:

```powershell
.
tools\log_prompt.ps1 -Prompt "My test prompt" -User "your_name"
```

Python:

```bash
python tools/log_prompt.py --prompt "My test prompt" --user your_name
```

The script uses UTF-8 encoding and performs basic validation to avoid obvious corruption patterns.
