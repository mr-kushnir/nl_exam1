DEVELOPER Agent: Pick Open tasks (MCP) → Read BDD from KB (API) → TDD → Review

**Input:** None (picks from queue) or specific task ID

## CRITICAL REQUIREMENTS

⚠️ **MANDATORY GIT COMMITS** ⚠️

The DEVELOPER agent MUST commit after EVERY TDD phase:
1. **RED** - Commit failing test BEFORE implementation
2. **GREEN** - Commit working implementation
3. **REFACTOR** - Commit refactored code (if any)

**NO EXCEPTIONS. Each commit must happen IMMEDIATELY after completing the phase.**

---

## Integration

- **Tasks**: YouTrack MCP (native)
- **Knowledge Base**: REST API for BDD scenarios
- **Git**: Bash commands (git add, git commit, git push)

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

### Step 4: Read BDD from KB

```bash
python scripts/youtrack_kb.py bdd ARTICLE-ID
```

### Step 5: TDD Implementation

**For EACH Gherkin scenario:**

#### 5.1 RED Phase - Write Failing Test

```python
# tests/test_feature.py
def test_scenario_name():
    """Scenario: Description from Gherkin"""
    # Arrange
    # Act
    # Assert
    pass
```

**Run test to verify it fails:**
```bash
python -m pytest tests/test_feature.py::test_scenario_name -v
# Must see FAILED
```

**⚠️ MANDATORY COMMIT - RED:**
```bash
git add tests/
git commit -m "$(cat <<'EOF'
test(TASK-ID): red: failing test for scenario_name

- Added test for: [scenario description]
- Test fails as expected (no implementation yet)

Refs TASK-ID
EOF
)"
```

#### 5.2 GREEN Phase - Implement

Write minimal code to make test pass:
```python
# src/module/feature.py
class Feature:
    def method(self):
        # Implementation
        pass
```

**Run test to verify it passes:**
```bash
python -m pytest tests/test_feature.py::test_scenario_name -v
# Must see PASSED
```

**⚠️ MANDATORY COMMIT - GREEN:**
```bash
git add src/ tests/
git commit -m "$(cat <<'EOF'
feat(TASK-ID): green: implement scenario_name

- Implemented: [what was implemented]
- Test now passes

Refs TASK-ID
EOF
)"
```

#### 5.3 REFACTOR Phase (if needed)

Clean up code without changing behavior:
```bash
python -m pytest tests/ -v  # All tests must still pass
```

**⚠️ MANDATORY COMMIT - REFACTOR:**
```bash
git add src/
git commit -m "$(cat <<'EOF'
refactor(TASK-ID): clean up implementation

- [What was refactored]
- All tests still passing

Refs TASK-ID
EOF
)"
```

**Repeat steps 5.1-5.3 for EACH scenario.**

### Step 6: Verify All Tests

```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

**Requirements:**
- All tests MUST pass
- Coverage MUST be >= 70%

### Step 7: Push and Move to Review

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

### Step 8: Next Task

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

- [ ] All Gherkin scenarios have tests
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
📝 Scenarios: 4
🔄 TDD Cycles: 4

📦 Commits:
  - test(TASK-ID): red: failing test for scenario1
  - feat(TASK-ID): green: implement scenario1
  - test(TASK-ID): red: failing test for scenario2
  - feat(TASK-ID): green: implement scenario2
  ... (8 commits total)

✅ Tests: 15 passing
📊 Coverage: 85%

Next task: TASK-ID+1 [Open]
```

Task ID (optional): $ARGUMENTS
