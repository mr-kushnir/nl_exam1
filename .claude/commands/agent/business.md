BUSINESS Agent: Analyze Epic → Create BDD → Create Subtasks → Initialize Documentation

**Input:** Epic ID (e.g., NLE-1)

## CRITICAL REQUIREMENTS

⚠️ **MANDATORY ACTIONS** ⚠️

The BUSINESS agent MUST:
1. **Analyze Epic** - Understand requirements and break into features
2. **Create BDD Articles** - Gherkin scenarios for each feature
3. **Create Subtasks** - YouTrack tasks linked to Epic
4. **Initialize README.md** - Project description and setup instructions
5. **Initialize CLAUDE.md** - AI workflow documentation
6. **Commit Documentation** - Git commit with initial docs

**NO moving forward without documentation initialization.**

---

## Integration

- **Tasks**: YouTrack API
- **Knowledge Base**: REST API (`scripts/youtrack_kb.py`)
- **Git**: Bash commands

---

## Workflow

### Step 1: Initialize Git Repository

```bash
# Ensure git is initialized
git status || git init

# Check for existing README
if [ ! -f README.md ]; then
    echo "README.md needs to be created"
fi
```

### Step 2: Read Epic

```bash
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('YOUTRACK_URL').rstrip('/')
token = os.getenv('YOUTRACK_TOKEN')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json'}
r = requests.get(f'{url}/api/issues/EPIC-ID?fields=id,idReadable,summary,description', headers=headers)
issue = r.json()
print(f\"Summary: {issue.get('summary')}\")
print(f\"Description:\\n{issue.get('description', '')}\")
"
```

### Step 3: Analyze and Break Down

Break down Epic into features:
- Feature 1: [Name] - [Description]
- Feature 2: [Name] - [Description]
- Feature 3: [Name] - [Description]

### Step 4: Create BDD Structure

**⚠️ MANDATORY - Create tests directory structure:**

```bash
# Create BDD directories
mkdir -p tests/features tests/steps

# Create conftest.py for pytest-bdd
cat > tests/conftest.py << 'EOF'
"""Pytest configuration for BDD tests."""
import pytest


@pytest.fixture
def app_context():
    """Application context fixture."""
    return {}
EOF

# Create __init__.py files
touch tests/__init__.py tests/features/__init__.py tests/steps/__init__.py
```

### Step 5: Create BDD Articles in KB and Feature Files

For EACH feature:

**5.1 Create KB Article:**

```bash
python scripts/youtrack_kb.py create "BDD: Feature Name" "# BDD: Feature Name

## Epic Reference
EPIC-ID

## Gherkin Scenarios

\`\`\`gherkin
Feature: Feature Name
  Description of the feature

  Scenario: Scenario 1
    Given precondition
    When action
    Then expected result

  Scenario: Scenario 2
    Given precondition
    When action
    Then expected result
\`\`\`

## Acceptance Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
"
```

Note the article ID returned (e.g., NLE-A-5).

**5.2 Create .feature file:**

```bash
cat > tests/features/feature_name.feature << 'EOF'
Feature: Feature Name
  Description of the feature

  Scenario: Scenario 1
    Given precondition
    When action
    Then expected result

  Scenario: Scenario 2
    Given precondition
    When action
    Then expected result
EOF
```

**5.3 Create step definitions stub:**

```bash
cat > tests/steps/test_feature_name.py << 'EOF'
"""Step definitions for Feature Name."""
import pytest
from pytest_bdd import scenarios, given, when, then

# Load scenarios from .feature file
scenarios('../features/feature_name.feature')


@given('precondition')
def given_precondition():
    """Set up precondition."""
    # TODO: Implement in DEVELOPER phase
    pass


@when('action')
def when_action():
    """Perform action."""
    # TODO: Implement in DEVELOPER phase
    pass


@then('expected result')
def then_expected_result():
    """Verify expected result."""
    # TODO: Implement in DEVELOPER phase
    pass
EOF
```

Repeat 5.1-5.3 for each feature.

### Step 6: Create Subtasks

For EACH feature:

```bash
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('YOUTRACK_URL').rstrip('/')
token = os.getenv('YOUTRACK_TOKEN')
project = os.getenv('YOUTRACK_PROJECT')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}

# Get project ID
r = requests.get(f'{url}/api/admin/projects?fields=id,shortName', headers=headers)
project_id = next(p['id'] for p in r.json() if p['shortName'] == project)

data = {
    'project': {'id': project_id},
    'summary': 'Implement feature name',
    'description': '''## Overview
Feature description

## BDD Specification
**Knowledge Base Article:** ARTICLE-ID

\`\`\`bash
python scripts/youtrack_kb.py bdd ARTICLE-ID
\`\`\`

## Definition of Done
- [ ] All Gherkin scenarios pass as tests
- [ ] Coverage >= 70%
- [ ] No security vulnerabilities
'''
}
r = requests.post(f'{url}/api/issues?fields=id,idReadable,summary', headers=headers, json=data)
task = r.json()
print(f\"Created: {task.get('idReadable')} - {task.get('summary')}\")

# Link as subtask
if task.get('id'):
    link_data = {'issues': [{'id': 'EPIC-INTERNAL-ID'}], 'linkType': {'name': 'Subtask'}}
    requests.post(f\"{url}/api/issues/{task['id']}/links\", headers=headers, json=link_data)
"
```

### Step 6: Create/Update README.md

**⚠️ MANDATORY - Create project documentation:**

```bash
cat > README.md << 'EOF'
# Project Name

Brief description of what this project does.

## Features

- Feature 1: Description
- Feature 2: Description
- Feature 3: Description

## Requirements

- Python 3.11+
- Docker
- Yandex Cloud CLI (`yc`)

## Environment Variables

Create `.env` file:

```bash
cp .env.example .env
```

Required variables:
- `BOT_TOKEN` - Telegram bot token
- `YC_TOKEN` - Yandex Cloud OAuth token
- `YC_FOLDER_ID` - Yandex Cloud folder ID
- `YDB_ENDPOINT` - YDB endpoint
- `YDB_DATABASE` - YDB database path

## Installation

```bash
# Clone repository
git clone <repo-url>
cd <project>

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Running Locally

```bash
# Run bot
python -m src.bot.main

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

## Deployment

Deployment is handled by the DEPLOYER agent. See `CLAUDE.md` for AI-assisted workflow.

Manual deployment:
```bash
# Build Docker image
docker build -t app:latest .

# Push to Yandex Container Registry
docker tag app:latest cr.yandex/$YC_REGISTRY_ID/app:latest
docker push cr.yandex/$YC_REGISTRY_ID/app:latest

# Deploy to Serverless Container
yc serverless container revision deploy --container-name app --image cr.yandex/$YC_REGISTRY_ID/app:latest
```

## Project Structure

```
.
├── src/
│   ├── bot/           # Telegram bot handlers
│   ├── services/      # Business logic services
│   └── db/            # Database clients
├── tests/             # Test files
├── scripts/           # Utility scripts
├── .claude/           # AI agent commands
├── CLAUDE.md          # AI workflow documentation
└── README.md          # This file
```

## License

MIT
EOF
```

### Step 7: Create/Update CLAUDE.md

**⚠️ MANDATORY - Create AI workflow documentation:**

```bash
cat > CLAUDE.md << 'EOF'
# AI-Assisted Development Workflow

This project uses a multi-agent system for automated development.

## Agent Pipeline

```
BUSINESS → DEVELOPER → TESTER → SECURITY → DEPLOYER
```

### 1. BUSINESS Agent (`/agent:business EPIC-ID`)

- Analyzes Epic requirements
- Creates BDD articles in Knowledge Base
- Creates subtasks in YouTrack
- Initializes documentation (README.md, CLAUDE.md)

### 2. DEVELOPER Agent (`/agent:developer`)

- Picks Open tasks from YouTrack
- Reads BDD scenarios from KB
- Implements using TDD (Red-Green-Refactor)
- **MUST commit after each TDD phase**
- Moves tasks to Review

### 3. TESTER Agent (`/agent:tester`)

- Picks Review tasks
- Runs comprehensive tests
- Verifies TDD commits exist
- Checks coverage >= 70%
- Moves to Tested or returns to Open

### 4. SECURITY Agent (`/agent:security`)

- Picks Tested tasks
- Runs SAST (Bandit)
- Checks dependencies (pip-audit)
- Scans for hardcoded secrets
- OWASP Top 10 checks
- Moves to Ready or returns to Open

### 5. DEPLOYER Agent (`/agent:deployer`)

- Picks Ready tasks
- Builds Docker image
- Deploys to Yandex Cloud
- Updates documentation
- Moves to Done

## Commands

| Command | Description |
|---------|-------------|
| `/run EPIC-ID` | Full pipeline |
| `/agent:business EPIC-ID` | Business analysis |
| `/agent:developer` | TDD implementation |
| `/agent:tester` | Testing |
| `/agent:security` | Security scan |
| `/agent:deployer` | Deployment |
| `/infra:init` | Initialize infrastructure |

## Task States

```
Open → In Progress → Review → Tested → Ready → Done
```

## Commit Convention

```
<type>(<task-id>): <phase>: <description>

Refs <task-id>
```

Types: `test`, `feat`, `fix`, `refactor`, `docs`, `chore`

Phases (TDD): `red`, `green`

## Integration Points

- **YouTrack**: Task management (API + MCP)
- **GitHub**: Code repository, issues
- **Yandex Cloud**: Deployment (Container, YDB, S3)
EOF
```

### Step 8: Commit Documentation

**⚠️ MANDATORY COMMIT:**

```bash
git add README.md CLAUDE.md
git commit -m "$(cat <<'EOF'
docs(EPIC-ID): initialize project documentation

- Created README.md with setup and usage instructions
- Created CLAUDE.md with AI workflow documentation
- Project structure documented
- Deployment instructions added

Refs EPIC-ID
EOF
)"
```

### Step 9: Report to Epic

```bash
python -c "
import os, requests
from dotenv import load_dotenv
load_dotenv()
url = os.getenv('YOUTRACK_URL').rstrip('/')
token = os.getenv('YOUTRACK_TOKEN')
headers = {'Authorization': f'Bearer {token}', 'Accept': 'application/json', 'Content-Type': 'application/json'}

comment = '''## BUSINESS Agent Complete

### KB Articles Created
| Article | Feature |
|---------|---------|
| ARTICLE-1 | BDD: Feature 1 |
| ARTICLE-2 | BDD: Feature 2 |

### Subtasks Created
| Task | Summary | KB Ref | State |
|------|---------|--------|-------|
| TASK-1 | Implement Feature 1 | ARTICLE-1 | Open |
| TASK-2 | Implement Feature 2 | ARTICLE-2 | Open |

### Documentation
- [x] README.md created
- [x] CLAUDE.md created
- [x] Documentation committed

Ready for DEVELOPER agent'''

requests.post(f'{url}/api/issues/EPIC-ID/comments', headers=headers, json={'text': comment})
"
```

---

## Verification Checklist

Before completing:

- [ ] Epic analyzed and understood
- [ ] BDD articles created for all features
- [ ] Subtasks created and linked to Epic
- [ ] README.md created with setup instructions
- [ ] CLAUDE.md created with AI workflow
- [ ] Documentation committed to git
- [ ] Report added to Epic

---

## Output Format

```
═══════════════════════════════════════════════════════════
✅ BUSINESS Agent Complete: EPIC-ID
═══════════════════════════════════════════════════════════

📚 KB Articles:
  ARTICLE-1: BDD: Feature 1
  ARTICLE-2: BDD: Feature 2

📋 Subtasks:
  TASK-1: Implement Feature 1 [Open]
  TASK-2: Implement Feature 2 [Open]

📝 Documentation:
  README.md: Created ✅
  CLAUDE.md: Created ✅
  Commit: docs(EPIC-ID): initialize project documentation

Next: /agent:developer
```

Epic ID: $ARGUMENTS
