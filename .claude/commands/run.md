Full autonomous pipeline: BUSINESS → DEVELOPER → TESTER → SECURITY → DEPLOYER

**Input:** Epic ID (e.g., NLE-1)

## Pipeline Overview

```
Epic ──▶ BUSINESS ──▶ Creates subtasks (Open)
                          │
                          ▼
         DEVELOPER ◀── Picks Open tasks
              │
              ▼
         TDD Implementation
              │
              ▼
         [Review] ──▶ TESTER
                         │
                    ┌────┴────┐
                    │         │
                  PASS      FAIL
                    │         │
                    ▼         ▼
               [Tested]    [Open] + GitHub Issue
                    │         │
                    ▼         └──▶ DEVELOPER fixes
               SECURITY
                    │
              ┌─────┴─────┐
              │           │
            PASS        FAIL
              │           │
              ▼           ▼
           [Ready]     [Open] + GitHub Issue
              │           │
              ▼           └──▶ DEVELOPER fixes
           DEPLOYER
              │
              ▼
           [Done] + Production
```

## Execution Steps

### Phase 1: BUSINESS Agent
```
Execute: /agent:business $ARGUMENTS

Creates:
- BDD articles in KB
- Subtasks in Open state
```

### Phase 2: DEVELOPER Agent Loop
```
While tasks in Open state:
  Execute: /agent:developer
  
  For each task:
  - Pick task → In Progress
  - TDD implementation
  - Commit with task reference
  - Set → Review
```

### Phase 3: TESTER Agent Loop
```
While tasks in Review state:
  Execute: /agent:tester
  
  For each task:
  - Run tests
  - Check coverage
  - If PASS: → Tested
  - If FAIL: → Open + GitHub Issue
```

### Phase 4: SECURITY Agent Loop
```
While tasks in Tested state:
  Execute: /agent:security
  
  For each task:
  - Run SAST
  - Check dependencies
  - If PASS: → Ready
  - If FAIL: → Open + GitHub Issue
```

### Phase 5: DEPLOYER Agent
```
When tasks in Ready state:
  Execute: /agent:deployer
  
  - Setup infrastructure (if first deploy)
  - Deploy to Yandex Cloud
  - Configure domain (YANDEX_DOMAIN)
  - Health check
  - → Done
```

### Phase 6: Cleanup
```
If all subtasks Done:
  - Mark Epic as Done
  - Final report
```

## Loop Logic

The pipeline loops until all tasks reach Done:

```
1. DEVELOPER works on Open tasks
2. TESTER reviews, may return to Open
3. DEVELOPER fixes returned tasks
4. TESTER re-reviews
5. SECURITY scans, may return to Open
6. DEVELOPER fixes security issues
7. Repeat until Ready
8. DEPLOYER deploys Ready tasks
```

## Output Format

```
═══════════════════════════════════════════════════════════
PIPELINE COMPLETE: $ARGUMENTS
═══════════════════════════════════════════════════════════

📋 BUSINESS:
  - KB Articles: 3
  - Subtasks: 5

💻 DEVELOPER:
  - Tasks implemented: 5
  - Commits: 15
  - Iterations: 2 (1 return from TESTER)

🧪 TESTER:
  - Approved: 5
  - Returned: 1 (fixed)
  - Coverage: 85%

🔒 SECURITY:
  - Approved: 5
  - Returned: 0
  - Issues: 0 critical

🚀 DEPLOYER:
  - URL: https://xxx.containers.yandexcloud.net
  - Domain: https://podcast.rapidapp.ru
  - Tasks Done: 5

✅ Epic $ARGUMENTS: DONE
```

Epic ID: $ARGUMENTS
