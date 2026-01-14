DEVELOPER Agent: Pick Open tasks → Read BDD (KB + Local) → TDD → Review

**Input:** None (picks from queue) or specific task ID

## CRITICAL REQUIREMENTS

⚠️ **MANDATORY PARALLEL WORK** ⚠️

The DEVELOPER agent works with **THREE systems simultaneously**:

| System | Purpose | Tool |
|--------|---------|------|
| **YouTrack Tasks** | Track progress | API |
| **YouTrack KB** | BDD source of truth | API (`scripts/youtrack_kb.py`) |
| **Local Files** | Implement & run tests | File system + pytest-bdd |

### TDD Workflow:
1. **Read BDD from KB** - Source of truth for scenarios
2. **Verify local .feature** - Must match KB content
3. **Implement step definitions** - Fill in the stubs
4. **RED** - Run tests, verify they fail → commit + push
5. **GREEN** - Implement service → commit + push
6. **REFACTOR** - Clean up → commit + push

**Rule: `git commit` → `git push` — always together, small iterations.**

---

## Integration

- **Tasks**: YouTrack API (update states, comments)
- **Knowledge Base**: REST API - BDD source of truth
- **Local Files**: tests/features/*.feature, tests/steps/*.py, src/
- **Git**: Bash commands (commit + push immediately)

---

## Workflow

### Step 1: Initialize Git (if needed)

```bash
# Check if git repo exists
git status || git init

# Configure if needed
git config user.email "bot@example.com" || true
git config user.name "Developer Bot" || true
```

### Step 2: Find Open Tasks

```bash
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('YOUTRACK_URL').rstrip('/')
token = os.getenv('YOUTRACK_TOKEN')
project = os.getenv('YOUTRACK_PROJECT')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
r = requests.get(f'{url}/api/issues?fields=idReadable,summary&query=project:{project}%20State:Open', headers=headers)
for t in r.json(): print(f\"{t['idReadable']}: {t['summary']}\")
"
```

### Step 3: Pick Task and Update State

```bash
# Update task to In Progress via API
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('YOUTRACK_URL').rstrip('/')
token = os.getenv('YOUTRACK_TOKEN')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
data = {'customFields': [{'name': 'State', '\$type': 'StateIssueCustomField', 'value': {'name': 'In Progress'}}]}
requests.post(f'{url}/api/issues/TASK-ID?fields=id', headers=headers, json=data)
requests.post(f'{url}/api/issues/TASK-ID/comments', headers=headers, json={'text': 'DEVELOPER Agent started'})
"
```

### Step 4: Read BDD from KB and Verify Sync with Local

```bash
# Ensure pytest-bdd is installed
pip install pytest-bdd --quiet
```

**4.1 Read BDD from KB (source of truth):**
```bash
python scripts/youtrack_kb.py bdd ARTICLE-ID
```

**4.2 Verify local .feature file exists:**
```bash
cat tests/features/feature_name.feature
```

**4.3 Compare KB and local - MUST be identical:**
```bash
# Get KB content
python scripts/youtrack_kb.py bdd ARTICLE-ID > /tmp/kb_bdd.txt

# Compare with local
diff /tmp/kb_bdd.txt tests/features/feature_name.feature || echo "WARNING: KB and local differ!"
```

**⚠️ If KB and local differ:**
- KB is source of truth
- Update local .feature to match KB
- Commit + push the sync

**4.4 Verify step definitions stub exists:**
```bash
ls tests/steps/test_*.py
```

### Step 5: TDD Implementation with BDD

**For EACH Gherkin scenario in .feature file:**

#### 5.1 RED Phase - Implement Step Definitions

Update the stub step definitions created by BUSINESS agent:

```python
# tests/steps/test_feature_name.py
"""Step definitions for Feature Name."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Load scenarios from .feature file
scenarios('../features/feature_name.feature')


@given('precondition')
def given_precondition():
    """Set up precondition."""
    # Actual implementation
    return {"context": "value"}


@when('action')
def when_action(given_precondition):
    """Perform action."""
    result = some_service.do_action(given_precondition)
    return result


@then('expected result')
def then_expected_result(when_action):
    """Verify expected result."""
    assert when_action is not None
    # Add assertions
```

**Run test to verify it fails (no implementation yet):**
```bash
python -m pytest tests/steps/test_feature_name.py -v
# Must see FAILED
```

**⚠️ MANDATORY COMMIT + PUSH - RED:**
```bash
git add tests/
git commit -m "$(cat <<'EOF'
test(TASK-ID): red: step definitions for scenario_name

- Implemented step definitions for: [scenario description]
- Test fails as expected (no service implementation yet)

Refs TASK-ID
EOF
)"
git push origin main
```

#### 5.2 GREEN Phase - Implement Service

Write minimal code to make test pass:
```python
# src/services/feature_service.py
class FeatureService:
    def do_action(self, context):
        """Implementation to satisfy BDD scenario."""
        # Minimal implementation
        return result
```

**Run test to verify it passes:**
```bash
python -m pytest tests/steps/test_feature_name.py -v
# Must see PASSED
```

**⚠️ MANDATORY COMMIT + PUSH - GREEN:**
```bash
git add src/ tests/
git commit -m "$(cat <<'EOF'
feat(TASK-ID): green: implement scenario_name

- Implemented: [what was implemented]
- BDD scenario now passes

Refs TASK-ID
EOF
)"
git push origin main
```

#### 5.3 REFACTOR Phase (if needed)

Clean up code without changing behavior:
```bash
python -m pytest tests/ -v  # All tests must still pass
```

**⚠️ MANDATORY COMMIT + PUSH - REFACTOR:**
```bash
git add src/
git commit -m "$(cat <<'EOF'
refactor(TASK-ID): clean up implementation

- [What was refactored]
- All tests still passing

Refs TASK-ID
EOF
)"
git push origin main
```

**Repeat steps 5.1-5.3 for EACH scenario in .feature file.**

### Step 6: Verify All Tests

```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

**Requirements:**
- All tests MUST pass
- Coverage MUST be >= 70%

### Step 7: Update CLAUDE.md (Development Log)

**⚠️ Document AI-assisted development progress:**

```bash
# Append development log entry to CLAUDE.md
cat >> CLAUDE.md << 'EOF'

---

## Development Log: TASK-ID

**Date:** $(date +%Y-%m-%d)
**Agent:** DEVELOPER

### Implementation Summary
- **Feature:** feature_name
- **KB Article:** ARTICLE-ID
- **Scenarios:** X implemented

### TDD Commits
| Phase | Commit | Description |
|-------|--------|-------------|
| RED | abc123 | test(TASK-ID): failing test for scenario |
| GREEN | def456 | feat(TASK-ID): implement scenario |
| REFACTOR | ghi789 | refactor(TASK-ID): cleanup |

### Files Changed
- tests/steps/test_feature_name.py
- src/services/feature_service.py

### Test Results
- BDD Scenarios: X passing
- Coverage: XX%

EOF

git add CLAUDE.md
git commit -m "docs(TASK-ID): update development log"
git push origin main
```

### Step 8: Move to Review

```bash
git push origin main
```

Update task state:
```bash
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('YOUTRACK_URL').rstrip('/')
token = os.getenv('YOUTRACK_TOKEN')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
data = {'customFields': [{'name': 'State', '\$type': 'StateIssueCustomField', 'value': {'name': 'Review'}}]}
requests.post(f'{url}/api/issues/TASK-ID?fields=id', headers=headers, json=data)
comment = '''DEVELOPER Complete

Commits:
- test(TASK-ID): red: failing test for X
- feat(TASK-ID): green: implement X
- refactor(TASK-ID): cleanup

Tests: X passing
Coverage: XX%

Ready for TESTER'''
requests.post(f'{url}/api/issues/TASK-ID/comments', headers=headers, json={'text': comment})
"
```

### Step 9: Next Task

Repeat for next Open task.

---

## Commit Convention

```
<type>(TASK-ID): <phase>: <description>

- Detail 1
- Detail 2

Refs TASK-ID
```

| Phase | Type | Prefix | Example |
|-------|------|--------|---------|
| RED | test | red: | `test(NLE-5): red: failing test for parse_expense` |
| GREEN | feat | green: | `feat(NLE-5): green: implement parse_expense` |
| REFACTOR | refactor | | `refactor(NLE-5): extract helper method` |
| FIX | fix | | `fix(NLE-5): handle edge case` |

---

## Verification Checklist

Before moving to Review:

- [ ] All .feature files have corresponding step definitions
- [ ] All step definitions implemented (not stubs)
- [ ] All BDD scenarios pass (`pytest tests/steps/ -v`)
- [ ] All tests pass
- [ ] Coverage >= 70%
- [ ] At least 2 commits per scenario (RED + GREEN)
- [ ] All commits pushed to remote
- [ ] Task state updated to Review

---

## Output Format

```
═══════════════════════════════════════════════════════════
DEVELOPER: TASK-ID → Review
═══════════════════════════════════════════════════════════

📚 BDD Source: ARTICLE-ID
📄 Feature file: tests/features/feature_name.feature
📝 Scenarios: 4
🔄 TDD Cycles: 4

📁 Files:
  - tests/features/feature_name.feature
  - tests/steps/test_feature_name.py
  - src/services/feature_service.py

📦 Commits:
  - test(TASK-ID): red: step definitions for scenario1
  - feat(TASK-ID): green: implement scenario1
  - test(TASK-ID): red: step definitions for scenario2
  - feat(TASK-ID): green: implement scenario2
  ... (8 commits total)

✅ BDD Tests: 4 scenarios passing
✅ Unit Tests: 15 passing
📊 Coverage: 85%

Next task: TASK-ID+1 [Open]
```

Task ID (optional): $ARGUMENTS
