SECURITY Agent: Tested tasks → Comprehensive Security Scan → Ready or back to Open

**Input:** None (picks from queue) or specific task ID

## CRITICAL REQUIREMENTS

⚠️ **THOROUGH SECURITY ANALYSIS** ⚠️

The SECURITY agent MUST perform comprehensive security testing:

1. **SAST** - Static Application Security Testing (bandit)
2. **Dependency Audit** - Check for vulnerable packages (pip-audit, safety)
3. **Secret Detection** - Find hardcoded credentials
4. **OWASP Top 10** - Check for common vulnerabilities
5. **Input Validation** - Verify all user inputs are sanitized
6. **Code Review** - Manual security review of critical paths

**DO NOT approve code with ANY HIGH or CRITICAL vulnerabilities.**

---

## Integration

- **Tasks**: YouTrack API
- **Issues**: GitHub API (for security issues)
- **Tools**: bandit, pip-audit, safety, grep

---

## Workflow

### Step 1: Find Tested Tasks

```bash
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('YOUTRACK_URL').rstrip('/')
token = os.getenv('YOUTRACK_TOKEN')
project = os.getenv('YOUTRACK_PROJECT')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
r = requests.get(f'{url}/api/issues?fields=idReadable,summary&query=project:{project}%20State:Tested', headers=headers)
for t in r.json(): print(f\"{t['idReadable']}: {t['summary']}\")
"
```

### Step 2: SAST Scan with Bandit

```bash
# Run bandit with all severity levels
python -m bandit -r src/ -f json -o /tmp/bandit_report.json 2>&1

# Show results
python -m bandit -r src/ -f txt -ll 2>&1

# Check for critical/high issues
python -c "
import json
with open('/tmp/bandit_report.json') as f:
    report = json.load(f)

high_issues = [r for r in report.get('results', []) if r['issue_severity'] in ['HIGH', 'CRITICAL']]
medium_issues = [r for r in report.get('results', []) if r['issue_severity'] == 'MEDIUM']

print(f'CRITICAL/HIGH: {len(high_issues)}')
print(f'MEDIUM: {len(medium_issues)}')

for issue in high_issues:
    print(f\"  [{issue['issue_severity']}] {issue['issue_text']}\")
    print(f\"    Location: {issue['filename']}:{issue['line_number']}\")
    print(f\"    CWE: {issue.get('issue_cwe', {}).get('id', 'N/A')}\")
"
```

**⚠️ ANY HIGH/CRITICAL → BLOCK**

### Step 3: Dependency Vulnerability Scan

```bash
# Primary: pip-audit
python -m pip_audit --format json 2>&1 | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    vulns = data if isinstance(data, list) else data.get('dependencies', [])
    high = [v for v in vulns if v.get('vulns') and any(x.get('fix_versions') for x in v.get('vulns', []))]
    print(f'Vulnerable packages: {len(high)}')
    for v in vulns:
        for vuln in v.get('vulns', []):
            print(f\"  {v['name']} {v['version']}: {vuln['id']}\")
except: pass
"

# Secondary: safety check
python -m safety check --json 2>&1 || true
```

**Check for:**
- Known CVEs in dependencies
- Packages with available security fixes
- Outdated packages with vulnerabilities

### Step 4: Secret Detection

```bash
echo "=== Checking for hardcoded secrets ==="

# API Keys
echo "API Keys:"
grep -rn "api_key\s*=\s*['\"][^'\"]*['\"]" src/ --include="*.py" 2>/dev/null || echo "  None found"
grep -rn "API_KEY\s*=\s*['\"][^'\"]*['\"]" src/ --include="*.py" 2>/dev/null || echo "  None found"

# Passwords
echo "Passwords:"
grep -rn "password\s*=\s*['\"][^'\"]*['\"]" src/ --include="*.py" 2>/dev/null || echo "  None found"
grep -rn "passwd\s*=\s*['\"][^'\"]*['\"]" src/ --include="*.py" 2>/dev/null || echo "  None found"

# Tokens
echo "Tokens:"
grep -rn "token\s*=\s*['\"][^'\"]*['\"]" src/ --include="*.py" 2>/dev/null | grep -v "os.getenv" || echo "  None found"

# Private Keys
echo "Private Keys:"
grep -rn "BEGIN.*PRIVATE KEY" src/ --include="*.py" 2>/dev/null || echo "  None found"

# AWS Keys
echo "AWS Keys:"
grep -rn "AKIA[0-9A-Z]{16}" src/ --include="*.py" 2>/dev/null || echo "  None found"

# Connection Strings
echo "Connection Strings:"
grep -rn "mongodb://\|postgres://\|mysql://\|redis://" src/ --include="*.py" 2>/dev/null | grep -v "os.getenv" || echo "  None found"
```

**⚠️ ANY hardcoded secret → CRITICAL BLOCK**

### Step 5: OWASP Top 10 Checks

#### A01: Broken Access Control
```bash
echo "=== A01: Access Control ==="
# Check for missing auth decorators
grep -rn "def \w\+(" src/ --include="*.py" | head -20
# Look for @auth_required, @login_required patterns
grep -rn "@auth\|@login\|@permission" src/ --include="*.py" || echo "No auth decorators found (may be OK for public APIs)"
```

#### A02: Cryptographic Failures
```bash
echo "=== A02: Cryptographic Failures ==="
# Check for weak hashing
grep -rn "md5\|sha1" src/ --include="*.py" 2>/dev/null && echo "WARNING: Weak hash found" || echo "No weak hashes"
# Check for hardcoded encryption keys
grep -rn "AES\|DES\|RSA" src/ --include="*.py" 2>/dev/null || echo "No encryption found"
```

#### A03: Injection
```bash
echo "=== A03: Injection ==="
# SQL Injection
grep -rn "execute.*%" src/ --include="*.py" 2>/dev/null && echo "WARNING: Possible SQL injection" || echo "No SQL injection patterns"
grep -rn "f\".*SELECT\|f\".*INSERT\|f\".*UPDATE\|f\".*DELETE" src/ --include="*.py" 2>/dev/null && echo "WARNING: SQL string formatting" || true

# Command Injection
grep -rn "os.system\|subprocess.call\|subprocess.run\|os.popen" src/ --include="*.py" 2>/dev/null | grep -v "shell=False" && echo "WARNING: Possible command injection" || echo "No command injection patterns"

# XSS (for web apps)
grep -rn "innerHTML\|document.write\|eval(" src/ --include="*.py" 2>/dev/null && echo "WARNING: Possible XSS" || echo "No XSS patterns"
```

#### A04: Insecure Design
```bash
echo "=== A04: Insecure Design ==="
# Check for rate limiting
grep -rn "rate_limit\|throttle\|RateLimiter" src/ --include="*.py" 2>/dev/null || echo "WARNING: No rate limiting found"
```

#### A05: Security Misconfiguration
```bash
echo "=== A05: Security Misconfiguration ==="
# Debug mode
grep -rn "DEBUG\s*=\s*True\|debug=True" src/ --include="*.py" 2>/dev/null && echo "WARNING: Debug mode enabled" || echo "No debug mode"
# CORS
grep -rn "CORS\|Access-Control-Allow-Origin: \*" src/ --include="*.py" 2>/dev/null && echo "WARNING: Check CORS config" || true
```

#### A06: Vulnerable Components
```bash
echo "=== A06: Vulnerable Components ==="
# Already covered by pip-audit
python -m pip_audit 2>&1 | head -10
```

#### A07: Authentication Failures
```bash
echo "=== A07: Authentication ==="
# Weak password validation
grep -rn "len(password)" src/ --include="*.py" 2>/dev/null || echo "No password length check (may be OK)"
# Session handling
grep -rn "session\|Session\|JWT\|token" src/ --include="*.py" 2>/dev/null | head -5 || echo "No session handling found"
```

#### A08: Data Integrity Failures
```bash
echo "=== A08: Data Integrity ==="
# Pickle/deserialize
grep -rn "pickle.load\|yaml.load\|eval(" src/ --include="*.py" 2>/dev/null && echo "WARNING: Unsafe deserialization" || echo "No unsafe deserialization"
```

#### A09: Logging Failures
```bash
echo "=== A09: Logging ==="
# Check for logging
grep -rn "import logging\|from logging" src/ --include="*.py" 2>/dev/null || echo "WARNING: No logging module used"
# Check for sensitive data in logs
grep -rn "logger.*password\|log.*password\|print.*password" src/ --include="*.py" 2>/dev/null && echo "WARNING: Possible password logging" || echo "No password logging"
```

#### A10: SSRF
```bash
echo "=== A10: SSRF ==="
# Check for URL handling
grep -rn "requests.get\|requests.post\|urllib\|httpx" src/ --include="*.py" 2>/dev/null | head -5 || echo "No HTTP requests"
# Look for user-controlled URLs
grep -rn "requests\.\w\+(.*user\|requests\.\w\+(.*input" src/ --include="*.py" 2>/dev/null && echo "WARNING: Check for SSRF" || true
```

### Step 6: Input Validation Review

```bash
echo "=== Input Validation ==="

# Check for input sanitization
grep -rn "sanitize\|escape\|validate\|clean" src/ --include="*.py" 2>/dev/null || echo "WARNING: No input sanitization functions found"

# Check for type hints (helps with validation)
grep -rn "def .*:.*->" src/ --include="*.py" 2>/dev/null | wc -l | xargs echo "Functions with type hints:"

# Check for Pydantic validation
grep -rn "BaseModel\|validator\|Field" src/ --include="*.py" 2>/dev/null | head -5 || echo "No Pydantic validation"
```

### Step 7: Generate Security Report

```bash
echo "
═══════════════════════════════════════════════════════════
SECURITY SCAN REPORT
═══════════════════════════════════════════════════════════
"

# Summary
python -c "
import json
import os

# Bandit results
try:
    with open('/tmp/bandit_report.json') as f:
        bandit = json.load(f)
    results = bandit.get('results', [])
    critical = len([r for r in results if r['issue_severity'] == 'CRITICAL'])
    high = len([r for r in results if r['issue_severity'] == 'HIGH'])
    medium = len([r for r in results if r['issue_severity'] == 'MEDIUM'])
    low = len([r for r in results if r['issue_severity'] == 'LOW'])
    print(f'SAST (Bandit):')
    print(f'  CRITICAL: {critical}')
    print(f'  HIGH: {high}')
    print(f'  MEDIUM: {medium}')
    print(f'  LOW: {low}')

    # Block if critical or high
    if critical > 0 or high > 0:
        print('  STATUS: ❌ BLOCKED')
    else:
        print('  STATUS: ✅ PASSED')
except Exception as e:
    print(f'Error reading bandit report: {e}')
"
```

### Step 8: Decision

#### APPROVE (→ Ready)

If ALL conditions met:
- [ ] No CRITICAL/HIGH bandit issues
- [ ] No HIGH severity CVEs in dependencies
- [ ] No hardcoded secrets
- [ ] No SQL/Command injection patterns
- [ ] Input validation present

```bash
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('YOUTRACK_URL').rstrip('/')
token = os.getenv('YOUTRACK_TOKEN')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}
data = {'customFields': [{'name': 'State', '\$type': 'StateIssueCustomField', 'value': {'name': 'Ready'}}]}
requests.post(f'{url}/api/issues/TASK-ID?fields=id', headers=headers, json=data)
comment = '''SECURITY Approved

## Security Scan Results

| Check | Status | Details |
|-------|--------|---------|
| SAST (Bandit) | ✅ | 0 high, X medium, Y low |
| Dependencies | ✅ | No high CVEs |
| Secrets | ✅ | None found |
| OWASP Top 10 | ✅ | No critical issues |
| Input Validation | ✅ | Pydantic used |

## Verified
- [x] No SQL injection
- [x] No command injection
- [x] No hardcoded credentials
- [x] No weak cryptography
- [x] Proper error handling

Ready for DEPLOYER'''
requests.post(f'{url}/api/issues/TASK-ID/comments', headers=headers, json={'text': comment})
"
```

#### BLOCK (→ Open + GitHub Issue)

If ANY critical issue found:

**Create Security Issue:**
```bash
gh issue create --title "[SECURITY] Vulnerability in TASK-ID" --body "## Security Vulnerability Found

### Severity: HIGH/CRITICAL

### Vulnerability Type
[e.g., SQL Injection, Hardcoded Secret, etc.]

### Location
\`src/file.py:123\`

### Description
[Detailed description of the vulnerability]

### CWE Reference
CWE-XXX: [Name]

### Remediation
1. [Step to fix]
2. [Step to fix]

### References
- [Link to OWASP]
- [Link to CWE]

Refs TASK-ID" --label "security,critical"
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
comment = '''SECURITY BLOCKED

## Critical Vulnerability Found

**Type:** [Vulnerability Type]
**Severity:** CRITICAL/HIGH
**Location:** src/file.py:123

## Required Actions
1. [Specific fix required]
2. [Specific fix required]

## GitHub Issue
#XX

**This MUST be fixed before deployment.**'''
requests.post(f'{url}/api/issues/TASK-ID/comments', headers=headers, json={'text': comment})
"
```

### Step 9: Next Task

Repeat for next Tested task.

---

## Blocking Conditions

| Vulnerability | Severity | Action |
|--------------|----------|--------|
| SQL Injection | CRITICAL | BLOCK |
| Command Injection | CRITICAL | BLOCK |
| Hardcoded Secrets | CRITICAL | BLOCK |
| RCE (Remote Code Exec) | CRITICAL | BLOCK |
| Path Traversal | HIGH | BLOCK |
| XSS (if web) | HIGH | BLOCK |
| High CVE in deps | HIGH | BLOCK |
| Unsafe Deserialization | HIGH | BLOCK |
| SSRF | HIGH | BLOCK |
| Weak Crypto (MD5/SHA1 for security) | MEDIUM | WARN |
| Missing Rate Limiting | MEDIUM | WARN |
| Debug Mode Enabled | MEDIUM | WARN |
| Info Disclosure | LOW | PASS |

---

## Output Format

```
═══════════════════════════════════════════════════════════
SECURITY Results
═══════════════════════════════════════════════════════════

TASK-ID: ✅ → Ready
  SAST: 0 high, 2 medium, 5 low
  Dependencies: 0 high CVEs
  Secrets: None found
  OWASP: Passed

TASK-ID+1: ❌ → Open (GitHub #15)
  BLOCKED: SQL Injection (CWE-89)
  Location: src/db/queries.py:45

Processed: 2
Approved: 1
Blocked: 1
```

Task ID (optional): $ARGUMENTS
