# Copyright Guard V0.1

A runnable PySide6 desktop MVP for authors to discover and manage suspected unauthorized web copies and prepare reporting tasks.

## Included
- Overview / Search / Works & Materials / Reports / Settings
- SQLite persistence
- Exactly 8 selectable search sources: Bing, Baidu, Sogou, 360, Quark, UC, QQ, DuckDuckGo
- MockSearchProvider, so V0.1 runs without API keys
- Search progress simulation and result deduplication
- Manual URL addition
- Result statuses: Potential / Confirmed / Ignored / Reported
- Works and reporting metadata
- Report task center
- Central QSS theme
- SearchProvider and ReportingAdapter interfaces
- AGENTS.md for Codex

## Run
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python main.py
```

The database is created automatically at `data/copyright_guard.db`.

## V0.1 limitations
The eight engine choices are UI/discovery-source placeholders backed by MockSearchProvider. V0.1 does not call live search APIs, make legal determinations, bypass CAPTCHA/login/access controls, crawl websites aggressively, or automatically submit complaints.
