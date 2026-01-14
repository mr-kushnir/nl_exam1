BUSINESS Agent: Analyze Epic → Create BDD in KB (API) → Create Subtasks (MCP)

**Input:** Epic ID (e.g., POD-1)

## Integration

- **Tasks**: YouTrack MCP (native)
- **Knowledge Base**: REST API (`scripts/youtrack_kb.py`)

---

## Workflow

### Step 1: Read Epic via MCP

```
Read YouTrack issue $ARGUMENTS with full description
```

Parse the Epic to understand features and requirements.

### Step 2: Analyze with Ultrathink

Break down Epic into features:
- Feature 1: News Collection
- Feature 2: Script Generation
- Feature 3: TTS Service
- etc.

### Step 3: Create BDD Articles in KB (via API)

For EACH feature, create KB article:

```bash
python scripts/youtrack_kb.py create "BDD: News Collection" "# BDD: News Collection

## Epic Reference
$ARGUMENTS

## Gherkin Scenarios

\`\`\`gherkin
Feature: News Collection from TechCrunch AI

  Scenario: Successfully parse recent articles
    Given the TechCrunch website is accessible
    When I request articles from the last 24 hours
    Then I should receive between 5 and 7 articles
    And each article should have title, description, url, date

  Scenario: Handle website unavailable
    Given the TechCrunch website returns error 503
    When I attempt to parse articles
    Then I should return cached articles from previous run

  Scenario: Duplicate detection
    Given article with id 'abc' exists in cache
    When I parse and find same article
    Then I should skip the duplicate
\`\`\`

## Acceptance Criteria
- [ ] Parse articles from last 24h
- [ ] Handle errors with cache fallback
- [ ] Detect duplicates
"
```

Note the article ID returned (e.g., POD-A-5).

### Step 4: Create Subtasks via MCP

For EACH feature:

```
Create YouTrack issue in project POD:
  Summary: Implement news parser
  Description: |
    ## Overview
    Implement news collection service.
    
    ## 📚 BDD Specification
    **Knowledge Base Article:** POD-A-5
    
    Read BDD scenarios: python scripts/youtrack_kb.py bdd POD-A-5
    
    ## Definition of Done
    - [ ] All Gherkin scenarios pass as tests
    - [ ] Coverage >= 70%
    - [ ] No security vulnerabilities
  
  Link as subtask of: $ARGUMENTS
```

### Step 5: Report via MCP

```
Add comment to YouTrack issue $ARGUMENTS:

📋 **BUSINESS Agent Complete**

## KB Articles Created
| Article | Feature |
|---------|---------|
| POD-A-5 | BDD: News Collection |
| POD-A-6 | BDD: Script Generation |
| POD-A-7 | BDD: TTS Service |

## Subtasks Created
| Task | Summary | KB Ref | State |
|------|---------|--------|-------|
| POD-2 | Implement news parser | POD-A-5 | Open |
| POD-3 | Implement script generator | POD-A-6 | Open |
| POD-4 | Implement TTS service | POD-A-7 | Open |

✅ Ready for DEVELOPER agent
```

---

## Output Format

```
═══════════════════════════════════════════════════════════
✅ BUSINESS Agent Complete: $ARGUMENTS
═══════════════════════════════════════════════════════════

📚 KB Articles (via API):
  POD-A-5: BDD: News Collection
  POD-A-6: BDD: Script Generation
  POD-A-7: BDD: TTS Service

📋 Subtasks (via MCP):
  POD-2: Implement news parser [Open]
  POD-3: Implement script generator [Open]
  POD-4: Implement TTS service [Open]

Next: /agent:developer
```

Epic ID: $ARGUMENTS
