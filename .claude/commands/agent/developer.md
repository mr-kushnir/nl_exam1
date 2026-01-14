DEVELOPER Agent: Pick Open tasks (MCP) → Read BDD from KB (API) → TDD → Review

**Input:** None (picks from queue) or specific task ID

## Integration

- **Tasks**: YouTrack MCP (native)
- **Knowledge Base**: REST API for BDD scenarios
- **Git**: GitHub MCP (native)

---

## Workflow

### Step 1: Find Open Tasks via MCP

```
Find YouTrack issues in project POD with state Open
```

### Step 2: Pick Task and Start

```
Update YouTrack issue POD-2 state to "In Progress"
Add comment to POD-2: 🔧 DEVELOPER Agent started
```

### Step 3: Read Task Description via MCP

```
Read YouTrack issue POD-2 with full description
```

Find KB article reference in description:
```
## 📚 BDD Specification
**Knowledge Base Article:** POD-A-5
```

### Step 4: Read BDD from KB (via API)

```bash
python scripts/youtrack_kb.py bdd POD-A-5
```

Output:
```gherkin
Feature: News Collection from TechCrunch AI

  Scenario: Successfully parse recent articles
    Given the TechCrunch website is accessible
    When I request articles from the last 24 hours
    Then I should receive between 5 and 7 articles
    ...
```

### Step 5: TDD Implementation

**For EACH scenario:**

#### RED - Write Failing Test
```python
# tests/unit/news/test_parser.py

def test_parse_recent_articles():
    """Scenario: Successfully parse recent articles"""
    parser = TechCrunchParser()
    articles = parser.parse_recent(hours=24)
    
    assert 5 <= len(articles) <= 7
    for article in articles:
        assert article.title
        assert article.url
```

Commit via MCP:
```
Commit with message: test(POD-2): red: failing test for parse_recent_articles

Refs POD-2
```

#### GREEN - Implement
```python
# src/news/parser.py

class TechCrunchParser:
    def parse_recent(self, hours=24):
        # Implementation
        ...
```

Commit:
```
Commit with message: feat(POD-2): green: implement parse_recent

Refs POD-2
```

#### REFACTOR
```
Commit with message: refactor(POD-2): extract HTTP client

Refs POD-2
```

**Repeat for each scenario.**

### Step 6: Verify Tests

```bash
python -m pytest tests/ -v --cov=src
```

### Step 7: Push and Move to Review

```
Push to origin main
```

```
Update YouTrack issue POD-2 state to "Review"
Add comment to POD-2:

✅ **DEVELOPER Complete**

## Implementation
- Scenarios implemented: 4
- TDD cycles: 4
- Commits: 12

## Tests
All passing, coverage 85%

Ready for TESTER
```

### Step 8: Next Task

Repeat for next Open task.

---

## Commit Convention

```
<type>(POD-X): <phase>: <description>

Refs POD-X
```

| Phase | Type | Example |
|-------|------|---------|
| RED | test | `test(POD-2): red: failing test for cache` |
| GREEN | feat | `feat(POD-2): green: implement cache` |
| REFACTOR | refactor | `refactor(POD-2): extract cache class` |

---

## Output Format

```
═══════════════════════════════════════════════════════════
DEVELOPER: POD-2 → Review
═══════════════════════════════════════════════════════════

📚 BDD Source: POD-A-5
📝 Scenarios: 4
🔄 TDD Cycles: 4
📦 Commits: 12
✅ Tests: 15 passing
📊 Coverage: 85%

Next task: POD-3 [Open]
```

Task ID (optional): $ARGUMENTS
