#!/usr/bin/env python3
"""
YouTrack Knowledge Base API Client
Tasks are handled via MCP, this is ONLY for KB articles
"""

import os
import sys
import json
import requests
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()


class YouTrackKB:
    """YouTrack Knowledge Base API client"""
    
    def __init__(self):
        self.base_url = os.getenv('YOUTRACK_URL', '').rstrip('/')
        self.token = os.getenv('YOUTRACK_TOKEN', '')
        self.project = os.getenv('YOUTRACK_PROJECT', 'NLE')
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        self._project_id = None
    
    def _request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """Make API request"""
        url = f"{self.base_url}/api/{endpoint}"
        try:
            response = requests.request(method, url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json() if response.text else {}
        except requests.exceptions.RequestException as e:
            print(f"YouTrack API Error: {e}", file=sys.stderr)
            return None
    
    def _get_project_id(self) -> str:
        """Get project ID for KB articles"""
        if self._project_id:
            return self._project_id
        
        # Try to get from existing articles
        articles = self.list_articles()
        if articles:
            article = self._request('GET', f"articles/{articles[0]['id']}?fields=project(id)")
            if article and 'project' in article:
                self._project_id = article['project']['id']
                return self._project_id
        
        # Fallback: admin API
        result = self._request('GET', f"admin/projects?fields=id,shortName&query={self.project}")
        if result and len(result) > 0:
            self._project_id = result[0]['id']
            return self._project_id
        
        return self.project

    # ═══════════════════════════════════════════════════════════
    # KB Articles
    # ═══════════════════════════════════════════════════════════
    
    def list_articles(self) -> List[dict]:
        """List all KB articles in project"""
        result = self._request(
            'GET', 
            f"articles?fields=id,idReadable,summary,updated&query=project:{self.project}"
        )
        return result if isinstance(result, list) else []
    
    def get_article(self, article_id: str) -> Optional[dict]:
        """Get article by ID (e.g., NLE-A-5)"""
        return self._request(
            'GET', 
            f"articles/{article_id}?fields=id,idReadable,summary,content,updated"
        )
    
    def create_article(self, title: str, content: str) -> Optional[dict]:
        """Create new KB article"""
        data = {
            "summary": title,
            "content": content,
            "project": {"id": self._get_project_id()}
        }
        return self._request('POST', f"articles?fields=id,idReadable,summary", data)
    
    def update_article(self, article_id: str, title: str = None, content: str = None) -> Optional[dict]:
        """Update existing article"""
        data = {}
        if title:
            data["summary"] = title
        if content:
            data["content"] = content
        return self._request('POST', f"articles/{article_id}?fields=id,idReadable,summary", data)
    
    def find_or_create(self, title: str, content: str) -> Optional[dict]:
        """Find by title or create new"""
        articles = self.list_articles()
        for article in articles:
            if article.get('summary') == title:
                return self.update_article(article['id'], content=content)
        return self.create_article(title, content)
    
    def get_bdd_scenarios(self, article_id: str) -> Optional[str]:
        """Extract Gherkin scenarios from KB article"""
        article = self.get_article(article_id)
        if not article:
            return None
        
        content = article.get('content', '')
        
        # Extract content between ```gherkin and ```
        import re
        match = re.search(r'```gherkin\s*(.*?)\s*```', content, re.DOTALL)
        if match:
            return match.group(1).strip()
        
        return content


# ═══════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("""
YouTrack Knowledge Base Client
(Tasks are handled via MCP, this is ONLY for KB)

Usage:
  python youtrack_kb.py list                    List all articles
  python youtrack_kb.py get <article_id>        Get article content
  python youtrack_kb.py bdd <article_id>        Get BDD/Gherkin from article
  python youtrack_kb.py create <title> <content>
  python youtrack_kb.py update <article_id> <content>
""")
        sys.exit(1)
    
    kb = YouTrackKB()
    cmd = sys.argv[1]
    
    if cmd == "list":
        articles = kb.list_articles()
        print(f"KB Articles ({len(articles)}):")
        for a in articles:
            print(f"  {a.get('idReadable')}: {a.get('summary')}")
    
    elif cmd == "get" and len(sys.argv) > 2:
        article = kb.get_article(sys.argv[2])
        if article:
            print(f"# {article.get('summary')}\n")
            print(article.get('content', ''))
        else:
            print("Article not found", file=sys.stderr)
            sys.exit(1)
    
    elif cmd == "bdd" and len(sys.argv) > 2:
        bdd = kb.get_bdd_scenarios(sys.argv[2])
        if bdd:
            print(bdd)
        else:
            print("No BDD scenarios found", file=sys.stderr)
            sys.exit(1)
    
    elif cmd == "create" and len(sys.argv) > 3:
        result = kb.create_article(sys.argv[2], sys.argv[3])
        if result:
            print(f"Created: {result.get('idReadable')} - {result.get('summary')}")
        else:
            sys.exit(1)
    
    elif cmd == "update" and len(sys.argv) > 3:
        result = kb.update_article(sys.argv[2], content=sys.argv[3])
        if result:
            print(f"Updated: {result.get('idReadable')}")
        else:
            sys.exit(1)
    
    else:
        print("Unknown command", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
