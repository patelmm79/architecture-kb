# Project Structure

```
architecture-kb/
│
├── 📋 Documentation
│   ├── README.md                    # Main project documentation
│   ├── CLAUDE.md                    # Claude Code guidance & architecture
│   ├── ORCHESTRATOR.md              # Orchestrator service documentation
│   ├── SETUP_MONITORING.md          # Pattern monitoring setup guide
│   ├── SETUP_ORCHESTRATOR.md        # Orchestrator deployment guide
│   └── PROJECT_STRUCTURE.md         # This file
│
├── 🔧 Configuration
│   ├── config/
│   │   └── relationships.json       # Dependency relationship definitions
│   ├── .env.example                 # Environment variables template
│   ├── .gitignore                   # Git ignore patterns
│   └── .dockerignore                # Docker ignore patterns
│
├── 🤖 Pattern Discovery (Core)
│   └── scripts/
│       ├── pattern_analyzer.py      # Main pattern extraction & analysis
│       └── precommit_checker.py     # Local pre-commit validation
│
├── 🎯 Orchestrator Service (NEW)
│   └── orchestrator/
│       ├── __init__.py
│       ├── app.py                   # FastAPI application
│       └── agents/
│           ├── __init__.py
│           ├── consumer_triage.py   # API consumer impact analysis
│           └── template_triage.py   # Template fork sync analysis
│
├── 🚀 Deployment
│   ├── Dockerfile                   # Container image definition
│   ├── deploy-gcp.sh                # GCP Cloud Run deployment script
│   └── requirements.txt             # Python dependencies
│
├── ⚙️ GitHub Actions
│   └── .github/
│       └── workflows/
│           └── main.yml             # Reusable workflow (pattern analysis)
│
└── 📊 Dashboard
    └── pattern_dashboard.html       # Client-side visualization UI
```

## Key Files Explained

### Documentation Files

| File | Purpose |
|------|---------|
| **README.md** | Main entry point, quick start, examples |
| **CLAUDE.md** | Architecture details for Claude Code |
| **ORCHESTRATOR.md** | Complete orchestrator documentation |
| **SETUP_MONITORING.md** | How to add pattern monitoring to repos |
| **SETUP_ORCHESTRATOR.md** | How to deploy and configure orchestrator |

### Configuration Files

| File | Purpose |
|------|---------|
| **config/relationships.json** | Defines consumer and template relationships between repos |
| **.env.example** | Template for local environment variables |
| **requirements.txt** | Python package dependencies |

### Core Python Files

| File | LOC | Purpose |
|------|-----|---------|
| **scripts/pattern_analyzer.py** | ~390 | Extracts patterns, updates KB, notifies orchestrator |
| **scripts/precommit_checker.py** | ~200 | Local pre-commit pattern checking |
| **orchestrator/app.py** | ~400 | FastAPI service, webhook receiver, issue creator |
| **orchestrator/agents/consumer_triage.py** | ~250 | Analyzes API breaking changes |
| **orchestrator/agents/template_triage.py** | ~270 | Analyzes template sync opportunities |

### Deployment Files

| File | Purpose |
|------|---------|
| **Dockerfile** | Container image for orchestrator service |
| **deploy-gcp.sh** | One-command deployment to GCP Cloud Run |
| **.dockerignore** | Files to exclude from Docker build |

## Data Flow Overview

### 1. Pattern Discovery Flow

```
Developer commits to monitored repo
       ↓
GitHub Actions triggered
       ↓
Reusable workflow called from architecture-kb
       ↓
pattern_analyzer.py runs
       ↓
Claude extracts patterns
       ↓
Updates knowledge_base.json
       ↓
Finds similar patterns in other repos
       ↓
Sends Discord/Slack notification
```

### 2. Dependency Orchestration Flow

```
Developer commits to monitored repo
       ↓
GitHub Actions triggered
       ↓
pattern_analyzer.py runs
       ↓
Extracts patterns + notifies orchestrator
       ↓
Orchestrator receives webhook
       ↓
Loads relationships.json
       ↓
Dispatches triage agents:
  - ConsumerTriageAgent (for API consumers)
  - TemplateTriageAgent (for template forks)
       ↓
Agents analyze with Claude
       ↓
Create GitHub issues if action needed
       ↓
Send critical notifications to Discord/Slack
```

## Deployment Architecture

### Pattern Discovery (Serverless)
- Runs in GitHub Actions
- Triggered by commits
- No persistent infrastructure
- Cost: ~$0-3/month

### Orchestrator Service (GCP Cloud Run)
- Deployed as container
- Scales to zero when idle
- Receives webhooks from GitHub Actions
- Cost: ~$1-5/month

## Configuration Points

### 1. Repository Level
Each monitored repo needs:
- `.github/workflows/pattern-monitoring.yml` (15 lines)
- Secrets: `ANTHROPIC_API_KEY`, `ORCHESTRATOR_URL`, etc.

### 2. Orchestrator Level
- `config/relationships.json` - Define all repo relationships
- Environment variables for orchestrator service
- GCP Cloud Run deployment

### 3. Knowledge Base Level
- Separate GitHub repo storing `knowledge_base.json`
- Automatically updated by pattern_analyzer.py

## Use Cases

### Pattern Discovery
- **Scenario**: Building similar features across repos
- **Files**: `scripts/pattern_analyzer.py`, `knowledge_base.json`
- **Outcome**: Notified of similar patterns, reduce duplication

### Consumer Relationships
- **Scenario**: API service changes breaking consumers
- **Files**: `orchestrator/agents/consumer_triage.py`, `config/relationships.json`
- **Outcome**: Auto-created issues in consumer repos

### Template Relationships
- **Scenario**: Infrastructure improvements in template repos
- **Files**: `orchestrator/agents/template_triage.py`, `config/relationships.json`
- **Outcome**: Auto-created issues suggesting backports

## Extension Points

Want to customize the system? Here's where to look:

### Add New Relationship Types
1. Create new agent in `orchestrator/agents/`
2. Add relationship type to `config/relationships.json` schema
3. Update `orchestrator/app.py` to dispatch new agent

### Modify Pattern Detection
1. Edit `scripts/pattern_analyzer.py`
2. Adjust LLM prompt in `extract_patterns_with_llm()`
3. Modify `find_similar_patterns()` scoring

### Change Triage Logic
1. Edit agent files in `orchestrator/agents/`
2. Modify `_llm_analyze_impact()` or `_llm_analyze_sync()`
3. Adjust prompts and confidence thresholds

### Add New Triggers
1. Update `config/relationships.json` with new trigger types
2. Modify `_filter_relevant_changes()` in consumer_triage.py
3. Update trigger detection patterns

## Development Workflow

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ANTHROPIC_API_KEY="..."
export GITHUB_TOKEN="..."

# Run orchestrator locally
uvicorn orchestrator.app:app --reload --port 8080

# Test pattern analyzer
cd scripts
python pattern_analyzer.py
```

### Deploy Changes
```bash
# Pull latest
git pull

# Deploy orchestrator
./deploy-gcp.sh

# Pattern analyzer auto-updates via reusable workflow
# (no deployment needed)
```

## Monitoring

### GitHub Actions
- View workflow runs in Actions tab
- Check pattern_analysis.json artifacts

### Orchestrator Logs
```bash
gcloud logging read "resource.labels.service_name=architecture-kb-orchestrator" --limit 50
```

### Knowledge Base
- Check `knowledge_base.json` in KB repo
- View with `pattern_dashboard.html`

## Security

### Secrets Management
- Never commit `.env` or credentials
- Use GitHub Secrets for workflow variables
- Use GCP Secret Manager for production (optional)

### Access Control
- GitHub token scoped to required repos only
- Orchestrator uses read-only access where possible
- GCP IAM controls who can deploy/modify service

## Scaling Considerations

### Current Capacity
- **Pattern Discovery**: Unlimited (runs per repo)
- **Orchestrator**: ~1000 requests/day comfortable
- **Claude API**: Rate limited by Anthropic tier

### Scale Horizontally
- Add more Cloud Run instances (auto-scales)
- Consider caching for repeated analyses
- Batch notifications for low-priority updates

## Cost Breakdown

| Component | Monthly Cost (Est.) |
|-----------|---------------------|
| GitHub Actions | $0-3 (free tier) |
| GCP Cloud Run | $1-3 |
| Anthropic API | $1-5 |
| GCR Storage | $0.50 |
| **Total** | **$3-12** |

Scales with:
- Number of commits
- Number of monitored repos
- Triage agent invocations

---

**Questions?** Check the documentation files or open an issue.
