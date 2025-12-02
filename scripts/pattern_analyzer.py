#!/usr/bin/env python3
"""
Pattern Discovery Agent - Main Analysis Script
Extracts patterns from commits and checks for cross-repo similarities
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import anthropic
import requests
from github import Github
import git

class PatternAnalyzer:
    def __init__(self):
        self.anthropic_client = anthropic.Anthropic(
            api_key=os.environ['ANTHROPIC_API_KEY']
        )
        self.github_token = os.environ['GITHUB_TOKEN']
        self.github_client = Github(self.github_token)
        self.webhook_url = os.environ.get('WEBHOOK_URL')
        self.kb_repo_name = os.environ.get('KNOWLEDGE_BASE_REPO')
        self.repo = git.Repo('.')

        # Get current repository info
        self.current_repo = os.environ.get('GITHUB_REPOSITORY')
        self.current_sha = os.environ.get('GITHUB_SHA', self.repo.head.commit.hexsha)

    def get_recent_changes(self) -> Dict:
        """Extract recent commit changes"""
        try:
            # Get the diff for the latest commit
            commit = self.repo.commit(self.current_sha)
            parent = commit.parents[0] if commit.parents else None

            if parent:
                diff = parent.diff(commit, create_patch=True)
            else:
                # First commit - get all files
                diff = commit.diff(git.NULL_TREE, create_patch=True)

            changes = {
                'commit_sha': self.current_sha,
                'commit_message': commit.message,
                'author': str(commit.author),
                'timestamp': commit.committed_datetime.isoformat(),
                'files_changed': []
            }

            for item in diff:
                file_info = {
                    'path': item.a_path or item.b_path,
                    'change_type': item.change_type,
                    'diff': item.diff.decode('utf-8', errors='ignore') if item.diff else ''
                }

                # Only include meaningful files
                if self._is_meaningful_file(file_info['path']):
                    changes['files_changed'].append(file_info)

            return changes
        except Exception as e:
            print(f"Error getting changes: {e}")
            return {'error': str(e)}

    def _is_meaningful_file(self, filepath: str) -> bool:
        """Filter out noise files"""
        ignore_patterns = [
            r'\.lock$', r'package-lock\.json$', r'yarn\.lock$',
            r'\.min\.js$', r'\.map$', r'__pycache__',
            r'\.pyc$', r'\.git/', r'node_modules/', r'\.DS_Store'
        ]
        return not any(re.search(pattern, filepath) for pattern in ignore_patterns)

    def extract_patterns_with_llm(self, changes: Dict) -> Dict:
        """Use Claude to extract semantic patterns from code changes"""

        # Prepare a concise summary of changes for the LLM
        files_summary = []
        for file in changes['files_changed'][:10]:  # Limit to avoid token overflow
            files_summary.append({
                'path': file['path'],
                'change_type': file['change_type'],
                'diff': file['diff'][:2000]  # Truncate large diffs
            })

        prompt = f"""Analyze this code commit and extract architectural patterns and decisions.

Repository: {self.current_repo}
Commit: {changes['commit_message']}

Files changed:
{json.dumps(files_summary, indent=2)}

Please identify:
1. **Core Patterns**: What architectural patterns are being used or introduced? (e.g., "error handling with custom exceptions", "API client with retry logic", "authentication middleware")

2. **Technical Decisions**: What technical choices were made? (e.g., "using requests library for HTTP", "storing config in environment variables")

3. **Reusable Components**: What parts of this code might be useful across multiple projects? Be specific about the abstraction.

4. **Dependencies**: What external libraries or services does this rely on?

5. **Problem Domain**: What business/technical problem does this solve in one sentence?

Respond ONLY with valid JSON in this exact format:
{{
  "patterns": ["pattern1", "pattern2"],
  "decisions": ["decision1", "decision2"],
  "reusable_components": [
    {{"name": "component_name", "description": "what it does", "files": ["file1.py"]}}
  ],
  "dependencies": ["dep1", "dep2"],
  "problem_domain": "brief description",
  "keywords": ["keyword1", "keyword2"]
}}"""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract JSON from response
            content = response.content[0].text
            # Remove markdown code blocks if present
            content = re.sub(r'```json\n?|\n?```', '', content).strip()

            pattern_data = json.loads(content)
            pattern_data['analyzed_at'] = datetime.now().isoformat()
            pattern_data['commit_sha'] = self.current_sha

            return pattern_data

        except Exception as e:
            print(f"Error in LLM analysis: {e}")
            return {
                'error': str(e),
                'patterns': [],
                'decisions': [],
                'reusable_components': [],
                'dependencies': [],
                'problem_domain': 'unknown',
                'keywords': []
            }

    def load_knowledge_base(self) -> Dict:
        """Load existing pattern knowledge base from GitHub repo"""
        if not self.kb_repo_name:
            return {'repositories': {}}

        try:
            kb_repo = self.github_client.get_repo(self.kb_repo_name)

            # Try to get the knowledge base file
            try:
                content_file = kb_repo.get_contents("knowledge_base.json")
                kb_data = json.loads(content_file.decoded_content.decode())
                return kb_data
            except:
                # KB doesn't exist yet
                return {'repositories': {}, 'created_at': datetime.now().isoformat()}

        except Exception as e:
            print(f"Error loading KB: {e}")
            return {'repositories': {}}

    def update_knowledge_base(self, pattern_data: Dict):
        """Update the central knowledge base with new patterns"""
        if not self.kb_repo_name:
            print("No knowledge base repo configured, skipping update")
            return

        try:
            kb = self.load_knowledge_base()

            # Initialize repo entry if doesn't exist
            if self.current_repo not in kb['repositories']:
                kb['repositories'][self.current_repo] = {
                    'patterns': [],
                    'history': []
                }

            # Add new pattern entry
            entry = {
                'timestamp': datetime.now().isoformat(),
                'commit_sha': self.current_sha,
                'patterns': pattern_data
            }

            kb['repositories'][self.current_repo]['history'].append(entry)
            kb['repositories'][self.current_repo]['patterns'] = pattern_data  # Latest
            kb['last_updated'] = datetime.now().isoformat()

            # Update in GitHub
            kb_repo = self.github_client.get_repo(self.kb_repo_name)
            kb_json = json.dumps(kb, indent=2)

            try:
                # Try to update existing file
                content_file = kb_repo.get_contents("knowledge_base.json")
                kb_repo.update_file(
                    "knowledge_base.json",
                    f"Update KB: {self.current_repo} @ {self.current_sha[:7]}",
                    kb_json,
                    content_file.sha,
                    branch="main"
                )
            except:
                # Create new file
                kb_repo.create_file(
                    "knowledge_base.json",
                    f"Initialize KB with {self.current_repo}",
                    kb_json,
                    branch="main"
                )

            print("Knowledge base updated successfully")

        except Exception as e:
            print(f"Error updating KB: {e}")

    def find_similar_patterns(self, current_patterns: Dict, kb: Dict) -> List[Dict]:
        """Find similar patterns in other repositories"""
        similarities = []

        current_keywords = set(current_patterns.get('keywords', []))
        current_patterns_list = current_patterns.get('patterns', [])

        for repo_name, repo_data in kb.get('repositories', {}).items():
            if repo_name == self.current_repo:
                continue  # Skip self

            repo_patterns = repo_data.get('patterns', {})
            repo_keywords = set(repo_patterns.get('keywords', []))
            repo_patterns_list = repo_patterns.get('patterns', [])

            # Simple similarity scoring
            keyword_overlap = len(current_keywords & repo_keywords)
            pattern_overlap = len(set(current_patterns_list) & set(repo_patterns_list))

            if keyword_overlap > 0 or pattern_overlap > 0:
                similarities.append({
                    'repository': repo_name,
                    'keyword_overlap': keyword_overlap,
                    'pattern_overlap': pattern_overlap,
                    'matching_patterns': list(set(current_patterns_list) & set(repo_patterns_list)),
                    'matching_keywords': list(current_keywords & repo_keywords),
                    'repo_patterns': repo_patterns
                })

        # Sort by relevance
        similarities.sort(key=lambda x: x['keyword_overlap'] + x['pattern_overlap'], reverse=True)

        return similarities[:5]  # Top 5 most similar

    def notify(self, message: str, similarities: List[Dict]):
        """Send notification via webhook"""
        if not self.webhook_url:
            print("No webhook URL configured")
            print(message)
            return

        # Format message for Discord/Slack
        notification = {
            "content": message,
            "embeds": []
        }

        # Add similarity embeds
        for sim in similarities[:3]:  # Top 3
            embed = {
                "title": f"Similar to: {sim['repository']}",
                "description": f"**Overlap**: {sim['keyword_overlap']} keywords, {sim['pattern_overlap']} patterns",
                "fields": []
            }

            if sim['matching_patterns']:
                embed['fields'].append({
                    "name": "Matching Patterns",
                    "value": "\n".join(f"• {p}" for p in sim['matching_patterns'][:5]),
                    "inline": False
                })

            notification['embeds'].append(embed)

        try:
            response = requests.post(self.webhook_url, json=notification)
            response.raise_for_status()
            print("Notification sent successfully")
        except Exception as e:
            print(f"Error sending notification: {e}")

    def run(self):
        """Main execution flow"""
        print(f"Analyzing patterns for {self.current_repo}...")

        # Step 1: Get changes
        changes = self.get_recent_changes()
        if 'error' in changes:
            print(f"Could not analyze changes: {changes['error']}")
            return

        if not changes['files_changed']:
            print("No meaningful file changes detected")
            return

        print(f"Found {len(changes['files_changed'])} changed files")

        # Step 2: Extract patterns with LLM
        print("Extracting patterns with Claude...")
        patterns = self.extract_patterns_with_llm(changes)

        # Save locally
        with open('pattern_analysis.json', 'w') as f:
            json.dump({
                'changes': changes,
                'patterns': patterns
            }, f, indent=2)

        # Step 3: Update knowledge base
        print("Updating knowledge base...")
        self.update_knowledge_base(patterns)

        # Step 4: Find similarities
        print("Checking for similar patterns in other repos...")
        kb = self.load_knowledge_base()
        similarities = self.find_similar_patterns(patterns, kb)

        # Step 5: Notify
        if similarities:
            message = f"🔍 **Pattern Analysis: {self.current_repo}**\n\n"
            message += f"Found {len(similarities)} similar repositories!\n\n"
            message += f"**This commit introduces:**\n"
            for pattern in patterns.get('patterns', [])[:3]:
                message += f"• {pattern}\n"

            self.notify(message, similarities)
        else:
            print("No similar patterns found in other repositories")

        print("\n✅ Analysis complete!")
        print(f"Patterns extracted: {len(patterns.get('patterns', []))}")
        print(f"Similar repos found: {len(similarities)}")


if __name__ == '__main__':
    analyzer = PatternAnalyzer()
    analyzer.run()