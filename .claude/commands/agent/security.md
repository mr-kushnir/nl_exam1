SECURITY Agent: Tested tasks (MCP) → Scan → Ready or back to Open

**Input:** None (picks from queue) or specific task ID

## Integration

- **Tasks**: YouTrack MCP (native)
- **Issues**: GitHub MCP (native)

---

## Workflow

### Step 1: Find Tested Tasks via MCP

```
Find YouTrack issues in project POD with state Tested
```

### Step 2: Run Security Scans

```bash
# SAST with bandit
bandit -r src/ -f json -o bandit_report.json -ll

# Dependency audit
pip-audit --format json > audit_report.json 2>/dev/null || safety check --json > safety_report.json

# Check for hardcoded secrets
grep -rn "password\s*=\s*['\"]" src/ || true
grep -rn "api_key\s*=\s*['\"]" src/ || true
grep -rn "secret\s*=\s*['\"]" src/ || true
```

### Step 3: Evaluate Results

**Blocking issues (CRITICAL/HIGH):**
- SQL Injection
- Command Injection
- Hardcoded credentials
- Known CVEs (high severity)
- Weak crypto (MD5 for security)

**Non-blocking (MEDIUM/LOW):**
- Info disclosure
- Code style issues
- Low severity CVEs

### Step 4: Decision

**If NO critical/high issues:**

```
Update YouTrack issue POD-2 state to "Ready"
Add comment to POD-2:

✅ **SECURITY Approved**

| Check | Status |
|-------|--------|
| SAST (bandit) | ✅ No critical |
| Dependencies | ✅ No high CVEs |
| Secrets | ✅ None found |

Ready for DEPLOYER
```

**If critical/high issues found:**

Create GitHub issue:
```
Create GitHub issue:
  Title: [SECURITY] SQL Injection in POD-2
  Body: |
    ## Vulnerability
    SQL Injection (CWE-89)
    
    ## Severity
    HIGH
    
    ## Location
    src/db/ydb_client.py:118
    
    ## Details
    User input concatenated directly into SQL query
    
    ## Fix
    Use parameterized queries
    
    Refs POD-2
  Labels: security, high-priority
```

Return to developer:
```
Update YouTrack issue POD-2 state to "Open"
Add comment to POD-2:

❌ **SECURITY Blocked**

**Vulnerability:** SQL Injection (HIGH)
**Location:** src/db/ydb_client.py:118
**GitHub Issue:** #7

Must fix before deployment.
```

### Step 5: Next Task

Repeat for next Tested task.

---

## Blocking Conditions

| Issue | Severity | Action |
|-------|----------|--------|
| SQL Injection | CRITICAL | Block |
| Command Injection | CRITICAL | Block |
| Hardcoded secrets | CRITICAL | Block |
| RCE | CRITICAL | Block |
| XSS | HIGH | Block |
| Path Traversal | HIGH | Block |
| High CVE | HIGH | Block |
| Info disclosure | MEDIUM | Warn, pass |
| Low CVE | LOW | Pass |

---

## Output Format

```
═══════════════════════════════════════════════════════════
SECURITY Results
═══════════════════════════════════════════════════════════

POD-2: ✅ → Ready
POD-3: ❌ → Open (SQL Injection) GitHub #7
POD-4: ✅ → Ready (1 low, passed)

Processed: 3
Approved: 2
Blocked: 1
```

Task ID (optional): $ARGUMENTS
