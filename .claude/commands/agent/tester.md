TESTER Agent: Review tasks (MCP) → Run tests → Tested or back to Open

**Input:** None (picks from queue) or specific task ID

## Integration

- **Tasks**: YouTrack MCP (native)
- **Issues**: GitHub MCP (native)

---

## Workflow

### Step 1: Find Review Tasks via MCP

```
Find YouTrack issues in project POD with state Review
```

### Step 2: Pick Task

Read task details:
```
Read YouTrack issue POD-2
```

### Step 3: Run Tests

```bash
python -m pytest tests/ -v --cov=src --cov-report=term-missing
```

Calculate coverage:
```bash
python -m pytest tests/ --cov=src --cov-report=json -q
```

### Step 4: Evaluate Results

**If tests PASS and coverage >= 70%:**

```
Update YouTrack issue POD-2 state to "Tested"
Add comment to POD-2:

✅ **TESTER Approved**

| Metric | Value |
|--------|-------|
| Tests | 15 passing |
| Coverage | 85% |

Ready for SECURITY
```

**If tests FAIL or coverage < 70%:**

Create GitHub issue:
```
Create GitHub issue:
  Title: [TESTER] Test failures in POD-2
  Body: |
    ## Failed Tests
    - test_parse_recent_articles
    - test_cache_fallback
    
    ## Coverage
    45% (required: 70%)
    
    Refs POD-2
  Labels: bug, testing
```

Return to developer:
```
Update YouTrack issue POD-2 state to "Open"
Add comment to POD-2:

❌ **TESTER Returned**

**Reason:** Tests failing / coverage below 70%

**GitHub Issue:** #5

Please fix and resubmit.
```

### Step 5: Next Task

Repeat for next Review task.

---

## Decision Matrix

| Tests | Coverage | Action |
|-------|----------|--------|
| ✅ Pass | >= 70% | → Tested |
| ✅ Pass | < 70% | → Open + GitHub Issue |
| ❌ Fail | any | → Open + GitHub Issue |

---

## Output Format

```
═══════════════════════════════════════════════════════════
TESTER Results
═══════════════════════════════════════════════════════════

POD-2: ✅ → Tested (85% coverage)
POD-3: ❌ → Open (3 tests failing) GitHub #5
POD-4: ❌ → Open (45% coverage) GitHub #6

Processed: 3
Approved: 1
Returned: 2
```

Task ID (optional): $ARGUMENTS
