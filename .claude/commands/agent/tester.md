TESTER Agent: Review tasks → Comprehensive Testing → Tested or back to Open

**Input:** None (picks from queue) or specific task ID

## CRITICAL REQUIREMENTS

⚠️ **THOROUGH TESTING + SYNC VERIFICATION** ⚠️

The TESTER agent works with **THREE systems simultaneously**:

| System | Verification |
|--------|--------------|
| **YouTrack Tasks** | Task state, comments |
| **YouTrack KB** | BDD source of truth |
| **Local Files** | .feature files, step definitions, coverage |

### Checks:
1. **KB ↔ Local sync** - .feature files MUST match KB content
2. **BDD tests** - All scenarios pass with pytest-bdd
3. **Coverage** - Minimum 70%, target 80%+
4. **TDD commits** - RED/GREEN commits exist in git log
5. **Edge cases** - Boundary conditions tested
6. **Code quality** - No TODOs, proper error handling

**DO NOT approve if KB and local files differ!**

---

## Integration

- **Tasks**: YouTrack API (update states, comments)
- **Knowledge Base**: REST API - verify BDD sync
- **Local Files**: tests/features/*.feature, tests/steps/*.py
- **Issues**: GitHub API (create issues for failures)
- **Git**: Bash commands (verify commits)

---

## Workflow

### Step 1: Find Review Tasks

```bash
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('YOUTRACK_URL').rstrip('/')
token = os.getenv('YOUTRACK_TOKEN')
project = os.getenv('YOUTRACK_PROJECT')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
r = requests.get(f'{url}/api/issues?fields=idReadable,summary&query=project:{project}%20State:Review', headers=headers)
for t in r.json(): print(f\"{t['idReadable']}: {t['summary']}\")
"
```

### Step 2: Verify Git Commits

**Check that DEVELOPER made proper TDD commits:**
```bash
git log --oneline -20

# Look for pattern:
# - test(TASK-ID): red: ...
# - feat(TASK-ID): green: ...
```

**⚠️ If NO TDD commits found → REJECT immediately**

### Step 3: Verify KB ↔ Local Sync

**⚠️ CRITICAL - KB and local .feature files MUST be identical:**

```bash
# For each feature in the task, verify sync:
echo "=== Verifying KB ↔ Local Sync ==="

# Get KB article ID from task description
# Read BDD from KB
python scripts/youtrack_kb.py bdd ARTICLE-ID > /tmp/kb_bdd.txt

# Compare with local .feature file
echo "Comparing KB with local:"
diff /tmp/kb_bdd.txt tests/features/feature_name.feature

if [ $? -ne 0 ]; then
    echo "❌ ERROR: KB and local .feature files differ!"
    echo "KB is source of truth - local must be updated"
    exit 1
else
    echo "✅ KB and local are in sync"
fi
```

**⚠️ If KB and local differ → REJECT immediately (sync issue)**

### Step 4: Run Unit Tests

```bash
python -m pytest tests/ -v --tb=short 2>&1
```

**All tests MUST pass. Any failure → REJECT**

### Step 5: Check Coverage

```bash
python -m pytest tests/ --cov=src --cov-report=term-missing --cov-report=html --cov-fail-under=70
```

**Coverage requirements:**
- Minimum: 70% (MUST have)
- Target: 80% (should have)
- Excellent: 90%+ (nice to have)

**⚠️ Coverage < 70% → REJECT**

### Step 6: Verify BDD Compliance

**5.1 Check .feature files exist:**
```bash
echo "=== Feature Files ==="
ls -la tests/features/*.feature 2>/dev/null || echo "ERROR: No .feature files found!"
```

**5.2 Check step definitions exist:**
```bash
echo "=== Step Definitions ==="
ls -la tests/steps/test_*.py 2>/dev/null || echo "ERROR: No step definitions found!"
```

**5.3 Run BDD tests:**
```bash
echo "=== BDD Test Results ==="
python -m pytest tests/steps/ -v --tb=short 2>&1
```

**5.4 Compare with KB scenarios:**
```bash
python scripts/youtrack_kb.py bdd ARTICLE-ID
```

**For EACH Gherkin scenario in .feature file, verify:**
- [ ] Corresponding step definitions exist
- [ ] Steps are not stubs (have actual assertions)
- [ ] Test covers Given/When/Then flow

**⚠️ No .feature files or step definitions → REJECT immediately**

### Step 7: Test Edge Cases

**Run additional edge case tests:**
```bash
# Test with empty inputs
python -m pytest tests/ -v -k "empty or none or null" 2>&1 || true

# Test with invalid inputs
python -m pytest tests/ -v -k "invalid or error or fail" 2>&1 || true
```

**Check for missing edge case tests:**
- Empty/null inputs
- Boundary values (0, -1, MAX_INT)
- Invalid formats
- Network errors
- Timeouts

### Step 8: Code Review Checklist

**Review the implementation code for:**

```bash
# Check for TODO/FIXME comments
grep -rn "TODO\|FIXME\|HACK\|XXX" src/ || echo "No TODOs found"

# Check for print statements (should use logging)
grep -rn "print(" src/ --include="*.py" | grep -v "test" || echo "No prints found"

# Check for hardcoded values
grep -rn "localhost\|127.0.0.1\|password\|secret" src/ || echo "No hardcoded values"

# Check for proper error handling
grep -rn "except:" src/ --include="*.py" || echo "No bare excepts"
```

**Code quality issues to flag:**
- [ ] Bare `except:` clauses
- [ ] Missing docstrings on public methods
- [ ] Hardcoded configuration values
- [ ] Print statements instead of logging
- [ ] TODO/FIXME comments not addressed

### Step 9: Integration Test (if applicable)

**Test component interactions:**
```bash
# Run integration tests if they exist
python -m pytest tests/integration/ -v 2>&1 || echo "No integration tests"

# Or test manually
python -c "
from src.services.yagpt_service import YaGPTService
from src.services.expense_storage import ExpenseStorage, Expense

yagpt = YaGPTService()
storage = ExpenseStorage(use_memory=True)

# Test flow: parse -> save -> retrieve
parsed = yagpt.parse_expense('кофе 300')
assert parsed is not None
expense = Expense(user_id=1, item=parsed.item, amount=parsed.amount, category=parsed.category)
storage.save_expense(expense)
expenses = storage.get_expenses(1)
assert len(expenses) == 1
print('Integration test PASSED')
"
```

### Step 10: Decision

#### APPROVE (→ Tested)

If ALL conditions met:
- [ ] All unit tests pass
- [ ] Coverage >= 70%
- [ ] TDD commits exist
- [ ] BDD scenarios covered
- [ ] No critical code issues

```bash
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('YOUTRACK_URL').rstrip('/')
token = os.getenv('YOUTRACK_TOKEN')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
data = {'customFields': [{'name': 'State', '\$type': 'StateIssueCustomField', 'value': {'name': 'Tested'}}]}
requests.post(f'{url}/api/issues/TASK-ID?fields=id', headers=headers, json=data)
comment = '''TESTER Approved

## Test Results
| Metric | Value | Status |
|--------|-------|--------|
| Unit Tests | XX passing | ✅ |
| Coverage | XX% | ✅ |
| BDD Compliance | X/X scenarios | ✅ |
| Code Quality | No issues | ✅ |

## Verified
- [x] TDD commits present
- [x] All scenarios tested
- [x] Edge cases covered
- [x] Error handling verified

Ready for SECURITY'''
requests.post(f'{url}/api/issues/TASK-ID/comments', headers=headers, json={'text': comment})
"
```

#### REJECT (→ Open + GitHub Issue)

If ANY condition fails:

**Create GitHub Issue:**
```bash
# Using gh CLI or API
gh issue create --title "[TESTER] Issues in TASK-ID" --body "## Testing Failed

### Issues Found
- [ ] Issue 1: Description
- [ ] Issue 2: Description

### Test Results
- Tests: X passing, Y failing
- Coverage: XX% (required: 70%)

### Required Actions
1. Fix failing tests
2. Add missing edge case tests
3. Increase coverage

Refs TASK-ID" --label "bug,testing"
```

**Return to Open:**
```bash
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('YOUTRACK_URL').rstrip('/')
token = os.getenv('YOUTRACK_TOKEN')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
data = {'customFields': [{'name': 'State', '\$type': 'StateIssueCustomField', 'value': {'name': 'Open'}}]}
requests.post(f'{url}/api/issues/TASK-ID?fields=id', headers=headers, json=data)
comment = '''TESTER Rejected

## Issues Found
1. [Issue description]
2. [Issue description]

## GitHub Issue
#XX

## Required Actions
- Fix the issues listed above
- Resubmit for review'''
requests.post(f'{url}/api/issues/TASK-ID/comments', headers=headers, json={'text': comment})
"
```

### Step 11: Next Task

Repeat for next Review task.

---

## Decision Matrix

| Tests | Coverage | TDD Commits | BDD | Action |
|-------|----------|-------------|-----|--------|
| ✅ Pass | >= 70% | ✅ Yes | ✅ Yes | → Tested |
| ✅ Pass | >= 70% | ❌ No | any | → Open (no TDD) |
| ✅ Pass | < 70% | any | any | → Open (low coverage) |
| ❌ Fail | any | any | any | → Open (tests fail) |

---

## Rejection Reasons

| Reason | Required Action |
|--------|-----------------|
| Tests failing | Fix the failing tests |
| Coverage < 70% | Add more tests |
| No TDD commits | Redo with proper TDD |
| Missing BDD scenarios | Add tests for all scenarios |
| No error handling tests | Add error case tests |
| Bare except clauses | Use specific exceptions |
| Hardcoded values | Move to config/env |

---

## Output Format

```
═══════════════════════════════════════════════════════════
TESTER Results
═══════════════════════════════════════════════════════════

TASK-ID: ✅ → Tested
  Tests: 15 passing
  Coverage: 85%
  BDD: 5/5 scenarios
  Commits: 10 TDD commits verified

TASK-ID+1: ❌ → Open (GitHub #12)
  Issue: Coverage 45% < 70%
  Missing: Edge case tests

Processed: 2
Approved: 1
Returned: 1
```

Task ID (optional): $ARGUMENTS
