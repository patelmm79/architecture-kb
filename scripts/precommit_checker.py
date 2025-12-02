#!/usr/bin/env python3
"""
Pre-commit Pattern Checker
Runs locally before commit to warn about pattern divergence
"""

import os
import sys
import json
import subprocess
from pathlib import Path
import anthropic
import requests

class PreCommitChecker:
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.kb_url = os.environ.get('KNOWLEDGE_BASE_URL')
        
        if not self.api_key:
            print("⚠️  ANTHROPIC_API_KEY not set - skipping pattern check")
            sys.exit(0)  # Don't block commit
    
    def get_staged_changes(self):
        """Get the diff of staged changes"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached'],
                capture_output=True,
                text=True,
                check=True
            )
            return result.stdout
        except subprocess.CalledProcessError:
            return ""
    
    def get_current_repo(self):
        """Get current repository name from git remote"""
        try:
            result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                capture_output=True,
                text=True,
                check=True
            )
            # Parse owner/repo from URL
            url = result.stdout.strip()
            if 'github.com' in url:
                parts = url.split('github.com')[-1].strip('/:').replace('.git', '')
                return parts
        except:
            pass
        return "unknown/repo"
    
    def fetch_knowledge_base(self):
        """Fetch knowledge base from GitHub"""
        if not self.kb_url:
            return None
        
        try:
            response = requests.get(self.kb_url, timeout=5)
            response.raise_for_status()
            return response.json()
        except:
            return None
    
    def quick_pattern_check(self, diff_content: str, kb: dict) -> list:
        """Quick Claude check for pattern similarities"""
        if not diff_content.strip():
            return []
        
        current_repo = self.get_current_repo()
        
        # Build a summary of patterns from other repos
        other_repos_summary = []
        for repo_name, repo_data in kb.get('repositories', {}).items():
            if repo_name == current_repo:
                continue
            patterns = repo_data.get('patterns', {})
            if patterns:
                other_repos_summary.append(f"{repo_name}: {', '.join(patterns.get('patterns', [])[:3])}")
        
        if not other_repos_summary:
            return []
        
        prompt = f"""You are reviewing staged code changes before commit. Check if these changes are similar to existing patterns in other repositories.

Staged changes:
```
{diff_content[:3000]}
```

Known patterns in other repositories:
{chr(10).join(other_repos_summary[:5])}

Respond ONLY with valid JSON:
{{
  "has_similarities": true/false,
  "warnings": [
    {{
      "message": "brief warning about potential redundancy or divergence",
      "similar_repo": "repo name",
      "suggestion": "what to consider"
    }}
  ]
}}

If no significant similarities, return {{"has_similarities": false, "warnings": []}}"""

        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            content = content.strip().replace('```json', '').replace('```', '').strip()
            result = json.loads(content)
            
            return result.get('warnings', [])
            
        except Exception as e:
            print(f"⚠️  Pattern check error: {e}")
            return []
    
    def run(self):
        """Main pre-commit check"""
        print("🔍 Checking patterns...")
        
        # Get staged changes
        diff = self.get_staged_changes()
        if not diff.strip():
            print("✓ No changes staged")
            return 0
        
        # Try to fetch KB
        kb = self.fetch_knowledge_base()
        if not kb or not kb.get('repositories'):
            print("✓ No knowledge base available (first repo?)")
            return 0
        
        # Check for similarities
        warnings = self.quick_pattern_check(diff, kb)
        
        if warnings:
            print("\n⚠️  Pattern Analysis Warnings:\n")
            for i, warning in enumerate(warnings, 1):
                print(f"{i}. {warning['message']}")
                print(f"   Similar to: {warning['similar_repo']}")
                print(f"   💡 {warning['suggestion']}\n")
            
            # Ask user if they want to continue
            response = input("Continue with commit? [y/N] ").lower()
            if response != 'y':
                print("Commit aborted. Review the warnings and try again.")
                return 1
        else:
            print("✓ No pattern conflicts detected")
        
        return 0


if __name__ == '__main__':
    checker = PreCommitChecker()
    sys.exit(checker.run())