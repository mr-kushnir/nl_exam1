#!/usr/bin/env python3
"""
GitHub API Client for issue management
"""

import os
import sys
import json
import subprocess
import requests
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

class GitHubClient:
    """GitHub API client for issues and PRs"""
    
    def __init__(self):
        self.token = os.getenv('GITHUB_TOKEN', '')
        self.repo = os.getenv('GITHUB_REPO', '')  # owner/repo
        self.api_url = 'https://api.github.com'
        self.headers = {
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def _request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """Make API request"""
        url = f"{self.api_url}/repos/{self.repo}/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.RequestException as e:
            print(f"GitHub API Error: {e}", file=sys.stderr)
            return None

    # ═══════════════════════════════════════════════════════════
    # ISSUES
    # ═══════════════════════════════════════════════════════════
    
    def create_issue(self, title: str, body: str, labels: List[str] = None) -> Optional[dict]:
        """Create new issue"""
        data = {
            "title": title,
            "body": body
        }
        if labels:
            data["labels"] = labels
        return self._request('POST', 'issues', data)
    
    def get_issues(self, state: str = 'open', labels: str = None) -> List[dict]:
        """Get issues by state and labels"""
        endpoint = f"issues?state={state}"
        if labels:
            endpoint += f"&labels={labels}"
        result = self._request('GET', endpoint)
        return result if isinstance(result, list) else []
    
    def close_issue(self, issue_number: int, comment: str = None) -> Optional[dict]:
        """Close issue with optional comment"""
        if comment:
            self.add_comment(issue_number, comment)
        return self._request('PATCH', f'issues/{issue_number}', {"state": "closed"})
    
    def add_comment(self, issue_number: int, body: str) -> Optional[dict]:
        """Add comment to issue"""
        return self._request('POST', f'issues/{issue_number}/comments', {"body": body})
    
    def create_test_failure_issue(self, task_id: str, failures: List[str], coverage: float) -> Optional[dict]:
        """Create issue for test failures"""
        body = f"""## Test Failures for {task_id}

### Failed Tests
{"".join(f"- {f}" for f in failures)}

### Coverage
{coverage:.1f}%

---
*Created by TESTER Agent*
Refs {task_id}
"""
        return self.create_issue(
            f"[TESTER] Test failures in {task_id}",
            body,
            ["bug", "testing", "auto-created"]
        )
    
    def create_security_issue(self, task_id: str, vuln_type: str, severity: str, location: str, details: str) -> Optional[dict]:
        """Create issue for security vulnerability"""
        body = f"""## Security Vulnerability: {vuln_type}

**Severity:** {severity}
**Location:** {location}
**Task:** {task_id}

### Details
{details}

### Recommendation
Fix the vulnerability before deployment.

---
*Created by SECURITY Agent*
Refs {task_id}
"""
        labels = ["security", "auto-created"]
        if severity.lower() in ["critical", "high"]:
            labels.append("high-priority")
        
        return self.create_issue(
            f"[SECURITY] {severity}: {vuln_type} in {task_id}",
            body,
            labels
        )

    # ═══════════════════════════════════════════════════════════
    # GIT OPERATIONS
    # ═══════════════════════════════════════════════════════════
    
    @staticmethod
    def git_commit(message: str, task_id: str = None) -> bool:
        """Create git commit with task reference"""
        full_message = message
        if task_id:
            full_message += f"\n\nRefs {task_id}"
        
        try:
            subprocess.run(['git', 'add', '-A'], check=True)
            subprocess.run(['git', 'commit', '-m', full_message], check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def git_push() -> bool:
        """Push to remote"""
        try:
            subprocess.run(['git', 'push'], check=True)
            return True
        except subprocess.CalledProcessError:
            return False
    
    @staticmethod
    def conventional_commit(type: str, scope: str, message: str, task_id: str = None) -> bool:
        """Create conventional commit"""
        commit_msg = f"{type}({scope}): {message}"
        return GitHubClient.git_commit(commit_msg, task_id)


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def print_usage():
    print("""
GitHub Client - Issue and Git Management

Usage:
  python github_client.py issue create <title> <body> [labels]
  python github_client.py issue list [state] [labels]
  python github_client.py issue close <number> [comment]
  python github_client.py issue comment <number> <body>
  
  python github_client.py test-failure <task_id> <failures_json> <coverage>
  python github_client.py security-issue <task_id> <type> <severity> <location> <details>
  
  python github_client.py commit <type> <scope> <message> [task_id]
  python github_client.py push
""")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)
    
    cmd = sys.argv[1]
    gh = GitHubClient()
    
    if cmd == "issue":
        action = sys.argv[2] if len(sys.argv) > 2 else ""
        
        if action == "create" and len(sys.argv) > 4:
            labels = sys.argv[5].split(',') if len(sys.argv) > 5 else None
            result = gh.create_issue(sys.argv[3], sys.argv[4], labels)
            if result:
                print(f"Created: {result.get('html_url')}")
        
        elif action == "list":
            state = sys.argv[3] if len(sys.argv) > 3 else 'open'
            labels = sys.argv[4] if len(sys.argv) > 4 else None
            issues = gh.get_issues(state, labels)
            for i in issues:
                print(f"#{i['number']}: {i['title']}")
        
        elif action == "close" and len(sys.argv) > 3:
            comment = sys.argv[4] if len(sys.argv) > 4 else None
            gh.close_issue(int(sys.argv[3]), comment)
            print("Closed")
        
        elif action == "comment" and len(sys.argv) > 4:
            gh.add_comment(int(sys.argv[3]), sys.argv[4])
            print("Comment added")
    
    elif cmd == "test-failure" and len(sys.argv) > 4:
        failures = json.loads(sys.argv[3])
        coverage = float(sys.argv[4])
        result = gh.create_test_failure_issue(sys.argv[2], failures, coverage)
        if result:
            print(f"Created: {result.get('html_url')}")
    
    elif cmd == "security-issue" and len(sys.argv) > 6:
        result = gh.create_security_issue(
            sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6]
        )
        if result:
            print(f"Created: {result.get('html_url')}")
    
    elif cmd == "commit" and len(sys.argv) > 4:
        task_id = sys.argv[5] if len(sys.argv) > 5 else None
        result = gh.conventional_commit(sys.argv[2], sys.argv[3], sys.argv[4], task_id)
        print("OK" if result else "FAILED")
    
    elif cmd == "push":
        result = gh.git_push()
        print("OK" if result else "FAILED")
    
    else:
        print_usage()
