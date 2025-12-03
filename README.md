# Architecture KB: Pattern Discovery + Dependency Orchestrator

> Automated architectural consistency, pattern discovery, and intelligent dependency management across your GitHub repositories

## 🎯 What This Solves

When building multiple projects with AI assistance, you face:
- **Pattern drift**: Similar problems solved differently across repos
- **Code duplication**: Reimplementing the same logic multiple times
- **Lost context**: Forgetting how you solved something last month
- **Technical debt**: Inconsistency compounds over time
- **🆕 Dependency blindness**: Changes in one repo breaking others silently
- **🆕 Manual coordination**: Tedious tracking of interdependent services

This system acts as your **automated institutional memory and dependency coordinator**, watching your commits and:
- ✅ Detecting similar patterns in other repos you can reuse
- ✅ Finding opportunities to extract shared libraries
- ✅ Catching architectural inconsistencies before they spread
- ✅ Identifying potential redundancy in real-time
- ✅ **🆕 Notifying dependent applications when changes require action**
- ✅ **🆕 Using AI agents to triage impact across your architecture**

## 📦 What's Included

### Core Components

1. **Reusable GitHub Workflow** (`.github/workflows/main.yml`)
   - Called from monitored repositories
   - No file copying required - automatically pulls latest code
   - Triggers on push/PR events
   - Uses Claude API for semantic analysis

2. **Pattern Analyzer** (`scripts/pattern_analyzer.py`)
   - Extracts semantic patterns from code changes
   - Compares patterns across repositories
   - Updates central knowledge base automatically
   - Sends smart notifications via Discord/Slack webhooks
   - **🆕 Notifies orchestrator service for dependency triage**

3. **🆕 Orchestrator Service** (`orchestrator/`)
   - FastAPI service deployed on GCP Cloud Run
   - Receives change notifications from pattern analyzer
   - Spawns AI triage agents to assess dependency impact
   - Creates GitHub issues in affected repositories
   - Handles two relationship types:
     - **Consumer relationships**: API changes → dependent apps
     - **Template relationships**: Infrastructure improvements → derived repos

4. **🆕 Triage Agents** (`orchestrator/agents/`)
   - **ConsumerTriageAgent**: Analyzes API breaking changes
   - **TemplateTriageAgent**: Identifies sync opportunities
   - Uses Claude to intelligently assess impact
   - Provides confidence scores and detailed recommendations

5. **Dashboard** (`pattern_dashboard.html`)
   - Visualize your architectural landscape
   - Interactive pattern similarity network graph
   - Track redundancy metrics across repos
   - Browse repository details and history

6. **Pre-commit Hook** (`scripts/precommit_checker.py`) [Optional]
   - Check patterns before commit locally
   - Warn about divergence from other repos
   - Interactive approval workflow

## 🚀 Quick Start

Choose your path:
- **Pattern Discovery Only**: Follow steps 1-4 below
- **🆕 With Dependency Orchestrator**: Follow all steps + see [ORCHESTRATOR.md](ORCHESTRATOR.md)

### 1. Create Knowledge Base Repository

```bash
gh repo create architecture-kb --private
cd architecture-kb
echo "# Architecture Knowledge Base" > README.md
git add . && git commit -m "init" && git push
```

### 2. Set Up Secrets

In **each repository** you want to monitor, add these GitHub secrets:

**Required:**
- `ANTHROPIC_API_KEY` - Get from console.anthropic.com

**Optional:**
- `DISCORD_WEBHOOK_URL` - For notifications
- `KNOWLEDGE_BASE_REPO` - Format: `username/architecture-kb`

### 3. Add to Repository

**No files to copy!** Just create one small workflow file:

```bash
# In your project repo
cd my-project

# Create workflow directory
mkdir -p .github/workflows

# Create the workflow file
cat > .github/workflows/pattern-monitoring.yml << 'EOF'
name: Pattern Monitoring

on:
  push:
    branches: [main, master, develop]
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze-patterns:
    uses: patelmm79/architecture-kb/.github/workflows/main.yml@main
    secrets:
      ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
      DISCORD_WEBHOOK_URL: ${{ secrets.DISCORD_WEBHOOK_URL }}
      KNOWLEDGE_BASE_REPO: ${{ secrets.KNOWLEDGE_BASE_REPO }}
      ORCHESTRATOR_URL: ${{ secrets.ORCHESTRATOR_URL }}  # Optional: for dependency triage
EOF

# Commit
git add .github/workflows/pattern-monitoring.yml
git commit -m "Enable pattern monitoring"
git push
```

**That's it!** The workflow automatically pulls the latest analyzer from this repo.

### 4. Watch It Work

On your next commit, the action will:
1. Call the reusable workflow from architecture-kb
2. Analyze your changes using Claude
3. Extract patterns and update knowledge base
4. Check for similarities across other repos
5. Notify you via Discord/Slack if patterns match

**See [SETUP_MONITORING.md](SETUP_MONITORING.md) for detailed instructions and troubleshooting.**

## 📊 Example Workflows

### Pattern Discovery: Cross-Repo Reuse

#### Day 1: First Repository
```bash
# You build a web scraper with retry logic
git commit -m "Add scraper with exponential backoff"
git push
```
**System:** ✅ Patterns recorded: "Retry logic with exponential backoff", "Rate limiting"

#### Day 7: Second Repository
```bash
# You build an API client
git commit -m "Add API client"
git push
```
**System:** 🔔 "Found similar pattern in **web-scraper**: 'Retry logic with exponential backoff'. Consider extracting to shared library?"

### 🆕 Dependency Orchestration: Automated Triage

#### Use Case 1: API Consumer
```bash
# You update vllm-container-ngc health check
cd vllm-container-ngc
git commit -m "Change health check from /health to /v1/health"
git push
```

**System Flow:**
1. Pattern analyzer extracts changes
2. Notifies orchestrator service
3. ConsumerTriageAgent analyzes impact on `resume-customizer`
4. **Creates issue in resume-customizer**:
   ```
   ⚠️ Dependency Update Required: vllm-container-ngc
   Urgency: HIGH | Confidence: 90%

   The health check endpoint changed. You need to update:
   - src/llm_client.py line 45
   - config/llm_config.yaml
   ```

#### Use Case 2: Template Fork
```bash
# You optimize GPU memory in vllm-container-ngc
cd vllm-container-ngc
git commit -m "Improve GPU memory allocation in docker-compose"
git push
```

**System Flow:**
1. Pattern analyzer extracts infrastructure improvements
2. Notifies orchestrator service
3. TemplateTriageAgent analyzes `vllm-container-coder`
4. **Creates issue in vllm-container-coder**:
   ```
   📋 Template Update Available: vllm-container-ngc
   Urgency: MEDIUM | Confidence: 85%

   GPU memory optimization added. Consider backporting:
   - docker-compose.yml lines 23-28
   - Improves memory efficiency by 15%
   ```

### Day 14: Review Patterns
Open your knowledge base dashboard to see patterns across all repos:
1. Download `knowledge_base.json` from your architecture-kb repo
2. Open `pattern_dashboard.html` in your browser
3. Load the knowledge base file
4. Explore:
   - Retry logic used in 2 repos: web-scraper, api-client
   - Environment-based configuration in 3 repos
   - Visual similarity network showing connections
   - **🆕 Dependency relationships and recent triage results**

## 🎨 Dashboard Usage

1. Open `pattern_dashboard.html` in your browser
2. Load your `knowledge_base.json` (from your KB repo)
3. Explore:
   - Repository statistics
   - Pattern similarity network
   - Detailed pattern breakdowns
   - Cross-repo relationships

## 🔧 Configuration

### Adjust Sensitivity

In `pattern_analyzer.py`, modify the `find_similar_patterns()` method:

```python
# Current: Alert on any keyword overlap
if keyword_overlap > 0 or pattern_overlap > 0:

# More selective: Require 2+ overlaps
if keyword_overlap > 1 or pattern_overlap > 1:
```

### Customize Notifications

Edit the `notify()` method to change format:

```python
# Add more detail
notification['embeds'][0]['fields'].append({
    "name": "Reusable Components",
    "value": "\n".join(components),
    "inline": False
})
```

### Filter Files

Add to `_is_meaningful_file()`:

```python
ignore_patterns = [
    r'\.lock$', 
    r'test_.*\.py$',  # Ignore test files
    r'.*_generated\..*',  # Ignore generated code
]
```

## 📈 Understanding the Knowledge Base

Your `knowledge_base.json` structure:

```json
{
  "repositories": {
    "username/repo-name": {
      "patterns": {
        "patterns": ["Pattern A", "Pattern B"],
        "decisions": ["Tech decision 1"],
        "reusable_components": [
          {
            "name": "RetryClient",
            "description": "HTTP client with retry logic",
            "files": ["src/client.py"]
          }
        ],
        "dependencies": ["requests", "tenacity"],
        "problem_domain": "Web scraping with resilience",
        "keywords": ["http", "retry", "scraping"]
      },
      "history": [
        {
          "timestamp": "2024-12-01T10:00:00",
          "commit_sha": "abc123",
          "patterns": {...}
        }
      ]
    }
  },
  "last_updated": "2024-12-01T12:00:00"
}
```

## 🎯 Advanced Usage

### Pre-commit Checking

Install the pre-commit hook:

```bash
# Make executable
chmod +x pre_commit_check.py

# Add to git hooks
cp pre_commit_check.py .git/hooks/pre-commit

# Set environment
export ANTHROPIC_API_KEY="your-key"
export KNOWLEDGE_BASE_URL="https://raw.githubusercontent.com/user/kb/main/knowledge_base.json"
```

Now on every commit:
```bash
git commit -m "Add feature"

# Output:
🔍 Checking patterns...
⚠️  Pattern Analysis Warnings:

1. Your new error handling resembles pattern in web-scraper
   Similar to: username/web-scraper
   💡 Consider using the same approach for consistency

Continue with commit? [y/N]
```

### Integration with CI/CD

Add to your `Jenkinsfile` or `.gitlab-ci.yml`:

```yaml
pattern-check:
  stage: validate
  script:
    # Call the reusable workflow or run analyzer directly
    - python scripts/pattern_analyzer.py
  artifacts:
    paths:
      - pattern_analysis.json
```

### Weekly Reports

Set up a cron job to generate reports:

```bash
# crontab -e
0 9 * * 1 cd ~/architecture-kb && python generate_weekly_report.py
```

## 🆕 Dependency Orchestrator

The orchestrator service coordinates AI triage agents to assess impact of changes across dependent repositories.

### Key Features
- **Consumer Relationships**: Detects API breaking changes
- **Template Relationships**: Identifies infrastructure sync opportunities
- **AI Triage Agents**: Use Claude to analyze impact intelligently
- **Automated Issues**: Creates GitHub issues with detailed recommendations
- **Confidence Scoring**: Provides 0-100% confidence for each assessment
- **Urgency Levels**: Critical, High, Medium, Low

### Setup
1. **Deploy orchestrator to GCP Cloud Run**:
   ```bash
   export GCP_PROJECT_ID="your-project"
   export ANTHROPIC_API_KEY="sk-ant-xxx"
   export GITHUB_TOKEN="ghp_xxx"
   ./deploy-gcp.sh
   ```

2. **Configure relationships** in `config/relationships.json`:
   ```json
   {
     "relationships": {
       "yourname/service-provider": {
         "consumers": [{
           "repo": "yourname/consumer-app",
           "change_triggers": ["api_contract", "authentication"]
         }]
       }
     }
   }
   ```

3. **Add ORCHESTRATOR_URL secret** to monitored repos

**See [ORCHESTRATOR.md](ORCHESTRATOR.md) for complete documentation.**

## 🔮 Roadmap

### ✅ Phase 1: Pattern Discovery & Orchestration (Complete)
- [x] Pattern extraction with Claude
- [x] Cross-repo similarity detection
- [x] Knowledge base management
- [x] Dependency orchestration service
- [x] Consumer & template triage agents
- [x] Automated issue creation

### Phase 2: Enhanced Intelligence (Next)
- [ ] Add vector embeddings for better pattern matching
- [ ] Implement confidence score improvements
- [ ] Pattern recommendation engine
- [ ] Weekly digest notifications
- [ ] Auto-create PRs (not just issues)

### Phase 3: Scale & Observability (Future)
- [ ] Orchestrator web dashboard
- [ ] Historical trend analysis
- [ ] Custom notification templates
- [ ] Bidirectional template sync detection
- [ ] Learning from user feedback

## 🐛 Troubleshooting

### Action fails immediately
**Check:** Secrets are set correctly (case-sensitive)

### No notifications
**Check:** Webhook URL is valid, test with curl:
```bash
curl -X POST $DISCORD_WEBHOOK_URL -H "Content-Type: application/json" -d '{"content": "test"}'
```

### Knowledge base not updating
**Check:** 
- `KNOWLEDGE_BASE_REPO` format is `username/repo`
- GitHub token has `repo` scope
- KB repo exists and is accessible

### Too many false positives
**Adjust:** Increase thresholds in `find_similar_patterns()`

### Not enough detection
**Adjust:** 
- Increase context in LLM prompts
- Add more keywords to extraction
- Lower similarity thresholds

## 💰 Cost Estimation

Typical monthly costs for active development:

- **GitHub Actions**: Free (public repos), ~$2-5 (private)
- **Claude API**: 
  - Per analysis: $0.01-0.05
  - 50 commits/month: $0.50-2.50
- **Storage**: Free (JSON in GitHub)

**Total: $3-10/month** for 5-10 active repositories

## 🤝 Contributing

This is your personal system, but you can extend it:

1. Fork patterns for specific languages/frameworks
2. Add domain-specific pattern extractors
3. Build custom notification formatters
4. Share your `knowledge_base.json` structure

## 📚 Related Resources

- [Claude Prompt Engineering](https://docs.anthropic.com/claude/docs)
- [GitHub Actions Documentation](https://docs.github.com/actions)
- [Architectural Decision Records](https://adr.github.io/)

## 🎓 Learning More

This system implements several concepts:

- **Knowledge Graphs**: Connecting repos by patterns
- **Semantic Analysis**: Understanding code intent, not just text
- **Proactive Monitoring**: Catching issues before they spread
- **Institutional Memory**: Codifying decisions automatically

## 📝 License

Use this however you want. It's your code and your architecture.

---

**Remember:** This system is a tool to help you maintain consistency as you scale. It's not about restricting creativity—it's about making informed decisions and avoiding accidental inconsistency.

Start small, iterate, and let it grow with your needs. 🚀