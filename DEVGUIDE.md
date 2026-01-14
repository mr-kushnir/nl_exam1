# Development Guide - Zero Manual Code

## Philosophy: Autonomous Agent-Driven Development

> **Ни строчки кода руками.** Весь код пишется агентами через пайплайн.

Этот проект демонстрирует полностью автоматизированную разработку, где:
- Человек формулирует требования в виде Epic
- Агенты декомпозируют, реализуют, тестируют и деплоят
- Целостность обеспечивается через YouTrack KB и задачи

---

## Multi-Agent Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        AUTONOMOUS PIPELINE                               │
│                                                                          │
│   Human         BUSINESS        DEVELOPER       TESTER                  │
│     │              │               │              │                      │
│     │  Epic        │  BDD → KB     │  TDD         │  Tests               │
│     ▼              ▼               ▼              ▼                      │
│  ┌──────┐     ┌─────────┐     ┌─────────┐    ┌─────────┐                │
│  │NLE-1 │────▶│ KB Arts │────▶│  Code   │───▶│ Verify  │                │
│  │Epic  │     │ + Tasks │     │ + Tests │    │ Coverage│                │
│  └──────┘     └─────────┘     └─────────┘    └─────────┘                │
│                    │               │              │                      │
│                    ▼               ▼              ▼                      │
│               SECURITY        DEPLOYER                                   │
│                    │               │                                     │
│                    ▼               ▼                                     │
│              ┌─────────┐     ┌─────────┐                                │
│              │  Scan   │────▶│ Deploy  │────▶ Production                │
│              │ Bandit  │     │ Docker  │                                │
│              └─────────┘     └─────────┘                                │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Agent Responsibilities

### BUSINESS Agent (`/agent:business`)

**Input:** Epic ID (e.g., NLE-1)

**Actions:**
1. Анализирует Epic и декомпозирует на фичи
2. Создаёт BDD сценарии в Knowledge Base (Gherkin)
3. Создаёт подзадачи в YouTrack с ссылками на KB

**Output:**
- KB Articles: `NLE-A-8`, `NLE-A-9`, ...
- Tasks: `NLE-14`, `NLE-15`, ... (state: Open)

```
Epic NLE-1 → KB Articles + Tasks
```

### DEVELOPER Agent (`/agent:developer`)

**Input:** None (picks Open tasks) or specific task ID

**Actions:**
1. Читает BDD из KB через API
2. Реализует по TDD: RED → GREEN → REFACTOR
3. Коммитит с правильными сообщениями
4. Переводит задачу в Review

**Output:**
- Code in `src/`
- Tests in `tests/`
- Commits with `Refs TASK-ID`

```bash
# Read BDD from KB
python scripts/youtrack_kb.py bdd NLE-A-8
```

### TESTER Agent (`/agent:tester`)

**Input:** None (picks Review tasks) or specific task ID

**Actions:**
1. Запускает все тесты
2. Проверяет coverage >= 70%
3. При успехе → Tested, при провале → Open + GitHub Issue

**Output:**
- Test results
- Coverage report
- GitHub Issues (если есть проблемы)

### SECURITY Agent (`/agent:security`)

**Input:** None (picks Tested tasks) or specific task ID

**Actions:**
1. SAST scan (bandit)
2. Dependency audit (pip-audit)
3. Secrets scan
4. При успехе → Ready, при провале → Open + GitHub Issue

**Blocking conditions:**
- SQL Injection (CRITICAL)
- Command Injection (CRITICAL)
- Hardcoded secrets (CRITICAL)
- High CVE in dependencies (HIGH)

### DEPLOYER Agent (`/agent:deployer`)

**Input:** None (deploys all Ready) or specific task ID

**Actions:**
1. Build Docker image
2. Push to Yandex Container Registry
3. Deploy to Serverless Container
4. Health check
5. Mark tasks as Done

**Output:**
- Container revision
- Production URL
- Health status

---

## Knowledge Base Integration

### YouTrack KB API

```bash
# List all articles
python scripts/youtrack_kb.py list

# Get article content
python scripts/youtrack_kb.py get NLE-A-8

# Extract BDD scenarios
python scripts/youtrack_kb.py bdd NLE-A-8

# Create new article
python scripts/youtrack_kb.py create "Title" "Content"
```

### BDD Article Structure

```markdown
# BDD: Feature Name

## Epic Reference
NLE-1

## Gherkin Scenarios

```gherkin
Feature: Expense Parsing

  Scenario: Parse simple expense
    Given user message "кофе 300"
    When YaGPT processes message
    Then extract item "кофе", amount 300, category "Еда"
```

## Acceptance Criteria
- [ ] All scenarios pass
- [ ] Coverage >= 70%
```

---

## Task Flow

```
┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐
│  Open   │───▶│In Progr.│───▶│ Review  │───▶│ Tested  │───▶│  Ready  │
└─────────┘    └─────────┘    └─────────┘    └─────────┘    └─────────┘
     │              │              │              │              │
     │   DEVELOPER  │   DEVELOPER  │    TESTER   │   SECURITY  │
     │    picks     │   completes  │   verifies  │    scans    │
     │              │              │              │              │
     └──────────────┴──────────────┴──────────────┴──────────────┘
                                                          │
                                                          ▼
                                                    ┌─────────┐
                                                    │  Done   │
                                                    └─────────┘
                                                          │
                                                     DEPLOYER
                                                     deploys
```

### State Transitions

| From | To | Agent | Condition |
|------|----|-------|-----------|
| Open | In Progress | DEVELOPER | Task picked |
| In Progress | Review | DEVELOPER | Code complete |
| Review | Tested | TESTER | Tests pass, coverage OK |
| Review | Open | TESTER | Tests fail |
| Tested | Ready | SECURITY | No vulnerabilities |
| Tested | Open | SECURITY | Security issues found |
| Ready | Done | DEPLOYER | Deployed successfully |

---

## Commit Convention

All commits are made by agents with structured messages:

```
<type>(<task-id>): <phase>: <description>

Refs <task-id>
Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

### TDD Phases

| Phase | Type | Example |
|-------|------|---------|
| RED | test | `test(NLE-14): red: failing test for parser` |
| GREEN | feat | `feat(NLE-14): green: implement parser` |
| REFACTOR | refactor | `refactor(NLE-14): extract helper function` |

### Other Types

| Type | Usage |
|------|-------|
| fix | Bug fixes |
| docs | Documentation |
| chore | Maintenance |
| security | Security fixes |

---

## GitHub Issues Integration

Agents create GitHub Issues for:
- Test failures (TESTER)
- Security vulnerabilities (SECURITY)
- Bugs found during development

Issue format:
```markdown
## [TYPE] Description

### Severity
CRITICAL / HIGH / MEDIUM / LOW

### Location
`src/file.py:123`

### Details
Description of the issue

### Fix
Suggested remediation

Refs TASK-ID
```

---

## Running the Pipeline

### Full Pipeline

```bash
# Process entire Epic
/run NLE-1
```

This runs: BUSINESS → DEVELOPER → TESTER → SECURITY → DEPLOYER

### Individual Agents

```bash
# Create BDD + tasks from Epic
/agent:business NLE-1

# Implement all Open tasks
/agent:developer

# Implement specific task
/agent:developer NLE-14

# Test all Review tasks
/agent:tester

# Security scan all Tested tasks
/agent:security

# Deploy all Ready tasks
/agent:deployer
```

---

## Context Preservation

### How Context is Maintained

1. **YouTrack Tasks** - contain task description + KB reference
2. **KB Articles** - contain BDD scenarios (source of truth)
3. **Git Commits** - reference task IDs (`Refs NLE-14`)
4. **GitHub Issues** - link to YouTrack tasks

### Reading Context

```bash
# Get task with KB reference
Read YouTrack issue NLE-14

# Get BDD from KB
python scripts/youtrack_kb.py bdd NLE-A-8

# See commits for task
git log --grep="NLE-14"
```

---

## Best Practices

### DO

- Always reference KB article in task description
- Use TDD: write test first, then implement
- Commit after each TDD phase (RED/GREEN/REFACTOR)
- Run full test suite before moving to Review
- Create GitHub Issues for any problems found

### DON'T

- Write code manually (use agents)
- Skip TDD phases
- Deploy without security scan
- Ignore test failures
- Commit without task reference

---

## Example Workflow

```
1. Human creates Epic NLE-1: "Telegram Expense Bot"

2. /agent:business NLE-1
   → Creates NLE-A-8 (BDD: Expense Parsing)
   → Creates NLE-14 (task, refs NLE-A-8)

3. /agent:developer NLE-14
   → Reads BDD from NLE-A-8
   → TDD: RED commit → GREEN commit → REFACTOR commit
   → Moves NLE-14 to Review

4. /agent:tester NLE-14
   → Runs tests (171 passing)
   → Coverage 85%
   → Moves NLE-14 to Tested

5. /agent:security NLE-14
   → Bandit scan: OK
   → pip-audit: OK
   → Moves NLE-14 to Ready

6. /agent:deployer
   → Build Docker image
   → Push to registry
   → Deploy to production
   → Moves NLE-14 to Done
```

---

## Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Test Coverage | >= 70% | ~50% |
| Security Issues | 0 critical/high | 0 |
| Deploy Success Rate | 100% | 100% |
| BDD Scenarios | All passing | 46/46 |
| Unit Tests | All passing | 171/171 |

---

## Related Documentation

- [README.md](README.md) - User documentation
- [CLAUDE.md](CLAUDE.md) - Technical documentation & development log
