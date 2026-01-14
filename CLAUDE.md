# 🤖 MULTI-AGENT TASK-DRIVEN SYSTEM v3.2

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         INTEGRATIONS                                     │
│                                                                          │
│   YouTrack Tasks ──────▶ MCP (native Claude Code)                       │
│   YouTrack KB ─────────▶ REST API (scripts/youtrack_kb.py)              │
│   GitHub ──────────────▶ MCP (native Claude Code)                       │
│   Yandex Cloud ────────▶ yc CLI + scripts                               │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Why this split?

- **Tasks via MCP**: Claude Code has native YouTrack MCP — use it for issues
- **KB via API**: MCP doesn't support Knowledge Base — use REST API

---

## Project Lifecycle

```
1. INFRA INIT (once)
   └──▶ /infra:init
        ├── Service Account
        ├── Container Registry
        ├── YDB Database
        ├── S3 Bucket
        ├── Wildcard Certificate (*.domain.ru)
        └── API Gateway with subdomain

2. DEVELOPMENT (per Epic)
   └──▶ /run EPIC-ID
        ├── BUSINESS: Epic → KB articles + subtasks
        ├── DEVELOPER: Tasks [Open] → TDD → [Review]
        ├── TESTER: Tasks [Review] → test → [Tested/Open]
        ├── SECURITY: Tasks [Tested] → scan → [Ready/Open]
        └── DEPLOYER: Tasks [Ready] → deploy → [Done]
```

---

## Working with YouTrack

### Tasks (via MCP)

Use Claude Code's native YouTrack integration:

```
# Read task
"Read YouTrack issue NLE-1"

# Create subtask
"Create YouTrack issue in NLE project:
 Summary: Implement news parser
 Description: See KB article NLE-A-5
 Parent: NLE-1"

# Update state
"Update YouTrack issue NLE-2 state to Review"

# Add comment
"Add comment to NLE-2: Implementation complete"

# Search
"Find YouTrack issues in NLE with state Open"
```

### Knowledge Base (via API)

MCP doesn't support KB, use script:

```bash
# List articles
python scripts/youtrack_kb.py list

# Get article content
python scripts/youtrack_kb.py get NLE-A-5

# Get only BDD/Gherkin scenarios
python scripts/youtrack_kb.py bdd NLE-A-5

# Create article
python scripts/youtrack_kb.py create "BDD: News Collection" "# Content..."

# Update article
python scripts/youtrack_kb.py update NLE-A-5 "# Updated content..."
```

---

## Working with GitHub

Use Claude Code's native GitHub MCP:

```
# Create issue
"Create GitHub issue:
 Title: Test failures in NLE-2
 Body: Coverage below 70%
 Labels: bug, testing"

# Close issue
"Close GitHub issue #5 with comment: Fixed in commit abc123"

# Commit
"Commit changes with message: feat(NLE-2): implement news parser"

# Push
"Push to origin main"
```

---

## Task States & Agent Mapping

| State | Agent | MCP Command |
|-------|-------|-------------|
| Open | DEVELOPER picks | `Find issues state: Open` |
| In Progress | DEVELOPER working | `Update issue state: In Progress` |
| Review | TESTER picks | `Find issues state: Review` |
| Tested | SECURITY picks | `Find issues state: Tested` |
| Ready | DEPLOYER picks | `Find issues state: Ready` |
| Done | Completed | `Update issue state: Done` |

---

## Agent Commands

| Command | Description |
|---------|-------------|
| `/infra:init` | Create infrastructure (once) |
| `/run EPIC-ID` | Full pipeline |
| `/agent:business EPIC-ID` | Create KB articles + subtasks |
| `/agent:developer` | Implement Open tasks |
| `/agent:tester` | Test Review tasks |
| `/agent:security` | Scan Tested tasks |
| `/agent:deployer` | Deploy Ready tasks |

---

## Environment Variables

```bash
# YouTrack (for KB API)
YOUTRACK_URL=https://xxx.youtrack.cloud
YOUTRACK_TOKEN=perm:xxx
YOUTRACK_PROJECT=NLE

# GitHub (MCP uses GITHUB_TOKEN from environment)
GITHUB_TOKEN=ghp_xxx

# Yandex Cloud
YC_TOKEN=y0_xxx
YC_FOLDER_ID=b1gxxx
YC_REGISTRY_ID=crpxxx          # Set by infra:init
YC_SERVICE_ACCOUNT_ID=xxx       # Set by infra:init
YC_CERT_ID=xxx                  # Set by infra:init

# Database (set by infra:init)
YDB_ENDPOINT=grpcs://...
YDB_DATABASE=/ru-central1/...
S3_BUCKET=xxx-files
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx

# Domain
YANDEX_DOMAIN=podcast.rapidapp.ru
```

---

## Commit Convention

```
<type>(<task-id>): <description>

Refs <task-id>
```

Types: `feat`, `fix`, `test`, `refactor`, `docs`, `chore`

Example:
```
feat(NLE-2): implement news parser

- Add TechCrunch scraper
- Parse articles from last 24h
- Cache in YDB

Refs NLE-2
```

---

## Project Status

### Current Epic: NLE-13 - Expense Tracker Bot v2.0

| Component | Status | Details |
|-----------|--------|---------|
| Infrastructure | ✅ Done | Registry, YDB, S3, Container, API Gateway |
| Agent System | ✅ Done | BUSINESS, DEVELOPER, TESTER, SECURITY, DEPLOYER |
| YaGPT Service | ✅ Done | Expense parsing, intent detection |
| ElevenLabs Service | ✅ Done | Voice transcription |
| Expense Storage | ✅ Done | YDB integration |
| Telegram Bot | ✅ Done | Handlers implemented |
| Unit Tests | ✅ 23 passing | 100% pass rate |
| BDD Tests | ⚠️ 7/13 passing | Step definitions need sync |
| Production Deploy | ❌ Pending | Next step |

### Completed Epics

| Epic | Description | Status |
|------|-------------|--------|
| NLE-1 | Initial Setup | ✅ Done |

### KB Articles

| Article | Feature |
|---------|---------|
| NLE-A-8 | BDD: YaGPT Service |
| NLE-A-9 | BDD: ElevenLabs Voice |
| NLE-A-10 | BDD: Data Storage |
| NLE-A-11 | BDD: Telegram Bot |

---

## Development Log

### 2026-01-14: Agent System Update

**Changes:**
- Updated all agents for parallel work with KB, local files, and tasks
- Added mandatory CLAUDE.md documentation logging
- Added KB ↔ Local sync verification
- Enforced immediate git push after every commit

**Commits:**
- `4645ba4` feat: add CLAUDE.md documentation logging to all agents
- `4f33ed0` feat: update agents for parallel work with KB, local files, and tasks
- `c022309` feat: add BDD test structure with feature files and step definitions

### 2026-01-14: Initial Implementation (NLE-1)

**Implemented:**
- YaGPT Service (expense parsing, intent detection)
- ElevenLabs Service (voice transcription)
- Expense Storage (YDB client)
- Telegram Bot Handlers

**Test Results:**
- Unit Tests: 23 passing
- Coverage: ~85%
