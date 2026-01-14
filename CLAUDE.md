# NLExam - Expense Tracker Bot

## Project Overview

Telegram-бот для учёта расходов с поддержкой естественного языка и голосовых сообщений.

**Production URL:** https://bba7ha844a2gpf5pou9e.containers.yandexcloud.net/
**Telegram Bot:** @nlexambot

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT                              │
│                                                              │
│   User Message ─────▶ FastAPI Webhook                       │
│                           │                                  │
│                    ┌──────┴──────┐                          │
│                    │             │                           │
│              Text Message   Voice Message                    │
│                    │             │                           │
│                    ▼             ▼                           │
│              YaGPT Service  SpeechKit STT                   │
│              (parse intent)  (transcribe)                   │
│                    │             │                           │
│                    └──────┬──────┘                          │
│                           │                                  │
│                    Expense Storage                           │
│                    (YDB / Memory)                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Component | Technology |
|-----------|------------|
| Bot Framework | python-telegram-bot 22.x |
| Web Server | FastAPI + uvicorn |
| NLP | YaGPT (expense parsing) |
| Voice | Yandex SpeechKit STT |
| Database | Yandex YDB |
| Storage | Yandex S3 |
| Hosting | Yandex Serverless Containers |

---

## Project Structure

```
nlexam/
├── src/
│   ├── bot/
│   │   ├── handlers.py      # Command & message handlers
│   │   ├── keyboards.py     # Inline/Reply keyboards
│   │   └── main.py          # FastAPI + webhook
│   ├── services/
│   │   ├── yagpt_service.py      # Expense parsing (YaGPT)
│   │   ├── speech_service.py     # Yandex SpeechKit STT
│   │   └── expense_storage.py    # YDB storage
│   └── db/
│       └── ydb_client.py    # YDB client (parameterized queries)
├── tests/
│   ├── features/            # 12 BDD .feature files
│   ├── steps/               # 12 step definitions
│   └── test_*.py            # Unit tests
├── scripts/
│   └── youtrack_kb.py       # KB API client
├── Dockerfile
├── requirements.txt
├── CLAUDE.md               # This file
└── README.md               # User documentation
```

---

## Features

### Implemented

| Feature | KB Article | Status |
|---------|------------|--------|
| Expense Parsing | NLE-A-8 | ✅ Done |
| Voice Recognition | NLE-A-9 | ✅ Done |
| Data Storage | NLE-A-10 | ✅ Done |
| Telegram Bot | NLE-A-11 | ✅ Done |
| BDD Sync | NLE-A-12 | ✅ Done |
| Integration Tests | NLE-A-13 | ✅ Done |
| Production Deploy | NLE-A-14 | ✅ Done |
| Confirmation Flow | NLE-A-15 | ✅ Done |
| Time Reports | NLE-A-17 | ✅ Done |
| Budget Management | NLE-A-18 | ✅ Done |
| Expense Management | NLE-A-19 | ✅ Done |
| Analytics | NLE-A-20 | ✅ Done |

---

## Test Results

```
═══════════════════════════════════════════════════════════
Test Summary (2026-01-14)
═══════════════════════════════════════════════════════════

Total Tests: 122 passing
Coverage: ~50%

BDD Features: 12
Step Definitions: 12

Unit Tests:
├── test_yagpt_service.py      - 7 tests
├── test_expense_storage.py    - 6 tests
├── test_telegram_bot.py       - 6 tests
├── test_speech_service.py     - 5 tests
├── test_ydb_client.py         - 7 tests
├── test_time_reports.py       - 7 tests
├── test_budget.py             - 5 tests
├── test_confirmation_flow.py  - 5 tests
├── test_expense_management.py - 5 tests
├── test_analytics.py          - 4 tests
└── test_keyboards.py          - 5 tests

BDD Steps:
├── test_expense_parsing.py    - 5 scenarios
├── test_expense_storage.py    - 4 scenarios
├── test_telegram_bot.py       - 4 scenarios
├── test_voice_recognition.py  - 3 scenarios
├── test_confirmation_flow.py  - 4 scenarios
├── test_time_reports.py       - 5 scenarios
├── test_budget_management.py  - 4 scenarios
├── test_expense_management.py - 5 scenarios
├── test_analytics.py          - 4 scenarios
├── test_bdd_sync.py           - 3 scenarios
├── test_integration.py        - 3 scenarios
└── test_deployment.py         - 2 scenarios
═══════════════════════════════════════════════════════════
```

---

## Environment Variables

```bash
# Telegram
BOT_TOKEN=xxx

# Yandex Cloud
YC_TOKEN=y0_xxx                    # OAuth token
YC_FOLDER_ID=b1gxxx
YC_REGISTRY_ID=crpxxx
YC_CONTAINER_ID=bbaxxx
YC_SERVICE_ACCOUNT_ID=ajexxx

# YDB
YDB_ENDPOINT=grpcs://ydb.serverless.yandexcloud.net:2135
YDB_DATABASE=/ru-central1/xxx/xxx

# S3
S3_BUCKET=nlexam-files
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx

# YouTrack (for KB API)
YOUTRACK_URL=https://xxx.youtrack.cloud
YOUTRACK_TOKEN=perm:xxx
YOUTRACK_PROJECT=NLE

# GitHub
GITHUB_TOKEN=ghp_xxx
GITHUB_REPO=mr-kushnir/nl_exam1
```

---

## Multi-Agent System

### Commands

| Command | Description |
|---------|-------------|
| `/run EPIC-ID` | Full pipeline |
| `/agent:business` | Create KB articles + subtasks |
| `/agent:developer` | Implement tasks with TDD |
| `/agent:tester` | Run tests, verify coverage |
| `/agent:security` | Security scan (bandit, pip-audit) |
| `/agent:deployer` | Build & deploy to production |

### Task States

| State | Agent | Action |
|-------|-------|--------|
| To do | DEVELOPER | Pick and implement |
| In Progress | DEVELOPER | Working |
| Done | - | Completed |

---

## Security

### Last Scan Results

| Check | Status |
|-------|--------|
| SAST (Bandit) | ✅ No HIGH/CRITICAL |
| Dependencies | ✅ Checked |
| Hardcoded Secrets | ✅ None found |
| SQL Injection | ✅ Fixed (parameterized queries) |

### Fixed Issues

| Issue | Fix | Commit |
|-------|-----|--------|
| SQL Injection in select() | Parameterized queries | dd718ce |
| SQL Injection in delete() | Parameterized queries | dd718ce |

---

## Commit Convention

```
<type>(<task-id>): <description>

Refs <task-id>
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

Types: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`

---

## Development Log

### 2026-01-14: BDD Features Complete

**Added:**
- 6 new feature files (voice, confirmation, time, budget, management, analytics)
- 6 new step definition files
- Total: 122 tests passing

**Features:**
- `voice_recognition.feature` - Yandex SpeechKit integration
- `confirmation_flow.feature` - Expense confirmation with buttons
- `time_reports.feature` - /today, /week commands
- `budget_management.feature` - /budget command
- `expense_management.feature` - /undo, /export, /find
- `analytics.feature` - ASCII charts, statistics

### 2026-01-14: Security Fix

**Fixed:**
- SQL injection in `select()` and `delete()` methods
- Added `_validate_table_name()` for table name validation
- Added `_build_select_query()` and `_build_delete_query()` with parameterized queries
- GitHub issues #1, #2 closed

### 2026-01-14: Initial Implementation

**Implemented:**
- YaGPT Service (expense parsing)
- Speech Service (Yandex SpeechKit)
- Expense Storage (YDB)
- Telegram Bot Handlers
- Production deployment

---

## Quick Reference

### Run Tests
```bash
python -m pytest tests/ -v
```

### Run Security Scan
```bash
python -m bandit -r src/ -ll
pip-audit
```

### Deploy
```bash
docker build -t nlexam-bot .
docker push cr.yandex/$YC_REGISTRY_ID/nlexam-bot:latest
```

### KB Operations
```bash
python scripts/youtrack_kb.py list
python scripts/youtrack_kb.py get NLE-A-8
python scripts/youtrack_kb.py bdd NLE-A-8
```
