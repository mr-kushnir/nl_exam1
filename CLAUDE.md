# 🤖 NLExam - Expense Tracker Bot

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
│   │   └── main.py          # FastAPI + webhook
│   ├── services/
│   │   ├── yagpt_service.py      # Expense parsing
│   │   ├── speech_service.py     # Yandex SpeechKit STT
│   │   └── expense_storage.py    # YDB storage
│   └── db/
│       └── ydb_client.py    # YDB client
├── tests/
│   ├── features/            # BDD .feature files
│   ├── steps/               # Step definitions
│   └── test_*.py            # Unit tests
├── scripts/
│   └── youtrack_kb.py       # KB API client
├── Dockerfile
├── requirements.txt
├── CLAUDE.md               # This file
└── README.md               # User documentation
```

---

## Services

### YaGPT Service (`src/services/yagpt_service.py`)

Парсинг расходов из естественного языка:

```python
# Parse expense
result = yagpt.parse_expense("кофе 300")
# -> ParsedExpense(item="кофе", amount=300, category="Еда")

# Detect intent
intent = yagpt.detect_intent("расходы")
# -> Intent(type="report_monthly")
```

**Intents:**
- `add_expense` - добавить расход
- `report_monthly` - отчёт за месяц
- `item_total` - сумма по позиции
- `top_expenses` - топ категорий

### Speech Service (`src/services/speech_service.py`)

Распознавание голоса через Yandex SpeechKit:

```python
service = SpeechService()
result = service.transcribe(audio_bytes)
# -> TranscriptionResult(text="кофе триста", success=True)
```

**Note:** Использует IAM токен, полученный из OAuth токена.

### Expense Storage (`src/services/expense_storage.py`)

Хранение расходов в YDB или in-memory:

```python
storage = ExpenseStorage(use_memory=False)  # YDB
storage = ExpenseStorage(use_memory=True)   # In-memory (tests)

storage.save_expense(expense)
expenses = storage.get_monthly_expenses(user_id)
totals = storage.get_category_totals(user_id)
```

---

## Development

### Local Setup

```bash
# Clone
git clone https://github.com/mr-kushnir/nl_exam1.git
cd nl_exam1

# Venv
python -m venv venv
source venv/bin/activate  # or: venv\Scripts\activate

# Install
pip install -r requirements.txt

# Run locally (polling mode)
python -m src.bot.main
```

### Running Tests

```bash
# All tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=src --cov-report=term-missing

# Only BDD
python -m pytest tests/steps/ -v
```

### Deployment

```bash
# Build
docker build -t cr.yandex/$YC_REGISTRY_ID/nlexam-bot:latest .

# Push
docker push cr.yandex/$YC_REGISTRY_ID/nlexam-bot:latest

# Deploy
yc serverless container revision deploy \
    --container-id $YC_CONTAINER_ID \
    --image cr.yandex/$YC_REGISTRY_ID/nlexam-bot:latest \
    ...
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
```

---

## Multi-Agent System

### Commands

| Command | Description |
|---------|-------------|
| `/run EPIC-ID` | Full pipeline (BUSINESS → DEVELOPER → TESTER → SECURITY → DEPLOYER) |
| `/agent:business` | Create KB articles + subtasks |
| `/agent:developer` | Implement tasks with TDD |
| `/agent:tester` | Run tests, verify coverage |
| `/agent:security` | Security scan (bandit, pip-audit) |
| `/agent:deployer` | Build & deploy to production |

### Task States

| State | Agent | Action |
|-------|-------|--------|
| To do | DEVELOPER | Pick and implement |
| In Progress | DEVELOPER | Working on it |
| Done | - | Completed |

---

## Current Status

### Epic NLE-13: Expense Tracker Bot v2.0 - ✅ COMPLETE

| Task | Status | Description |
|------|--------|-------------|
| NLE-14 | ✅ Done | Fix BDD step definitions |
| NLE-15 | ✅ Done | Integration tests |
| NLE-16 | ✅ Done | Production deployment |
| NLE-17 | ✅ Done | Voice recognition fix |

### Test Results

```
57 passed, 1 warning
Coverage: 71% (core services)
```

### Production

- **Container:** ACTIVE
- **Health:** `{"status":"healthy"}`
- **Webhook:** Configured
- **Voice:** Yandex SpeechKit (IAM token auth)

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

### 2026-01-14: Security Scan #2 (SECURITY Agent)

**Comprehensive Re-scan Results:**

| Check | Status | Details |
|-------|--------|---------|
| SAST (Bandit) | ⚠️ | 0 HIGH, 3 MEDIUM (false positives), 3 LOW |
| Dependencies | ⚠️ | 2 CVEs found |
| Hardcoded Secrets | ✅ | None found |
| OWASP Top 10 | ⚠️ | 1 issue found |
| Input Validation | ✅ | Partial (YDB has validation) |

**Vulnerabilities Found:**

| Issue | Severity | Location | GitHub Issue |
|-------|----------|----------|--------------|
| SQL Injection in insert() | MEDIUM | src/db/ydb_client.py:150-171 | #3 |
| Vulnerable pip 25.2 | MEDIUM | CVE-2025-8869 | #4 |
| Vulnerable urllib3 2.6.2 | MEDIUM | CVE-2026-21441 | #4 |

**Bandit False Positives (verified safe):**
- Lines 123, 126, 147: Table is validated via `_validate_table_name()`, values use parameterized queries

**Action Required:**
1. Fix `insert()` method - add table/column validation (GitHub #3)
2. Update vulnerable dependencies (GitHub #4)

**Status:** ⚠️ BLOCKED - Fix issues before production deployment

---

### 2026-01-14: Voice Recognition Fix

- Replaced ElevenLabs with Yandex SpeechKit
- Fixed IAM token authentication (OAuth → IAM conversion)
- Deployed to production

### 2026-01-14: Production Deployment

- Added webhook mode (FastAPI)
- Deployed to Yandex Serverless Containers
- Configured Telegram webhook
- All 57 tests passing

### 2026-01-14: BDD Implementation

- Fixed all BDD step definitions
- Synced .feature files with implementation
- 21 BDD scenarios passing

### 2026-01-14: Initial Implementation

- YaGPT Service (expense parsing)
- Expense Storage (YDB)
- Telegram Bot Handlers
- Unit tests (23 tests)
