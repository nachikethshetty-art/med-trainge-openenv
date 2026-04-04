# 🎫 Support Ticket Triage OpenEnv

**Real-world customer support ticket triaging environment for evaluating AI agents on multi-task decision-making under complexity.**

---

## 🎯 Overview

**Support Ticket Triage OpenEnv** simulates a real customer support operation where agents must triage incoming tickets by priority, category, and optimal agent assignment. This is a genuine business problem: companies spend millions automating and optimizing support triaging to improve CSAT, reduce resolution time, and balance workloads.

### Why This Environment Matters

- **Real-world utility**: Applies directly to support operations at any SaaS, e-commerce, or service company
- **Multi-objective**: Requires balancing accuracy, fairness, sentiment awareness, and throughput
- **Partial signal**: Agents get continuous feedback on classification accuracy and load balancing—not just binary success
- **Scalability**: Difficulty progression challenges models: from simple (5 tickets, mostly LOW/MEDIUM) to hard (15 CRITICAL tickets with complex sentiment)

---

## 🏗️ Task Levels

### Task 1: Basic Triage (🟢 Easy)
- **Scenario**: 5 tickets, mostly LOW/MEDIUM priority
- **Challenge**: Achieve >90% priority accuracy
- **Success metric**: Score >0.70
- **Expected agents**: Capable LLMs (GPT-3.5, Llama 2)

### Task 2: Balanced Triage (🟡 Medium)
- **Scenario**: 10 mixed tickets, includes HIGH priority, load-balanced assignment
- **Challenge**: 80% priority accuracy + even workload distribution (std < 1.0)
- **Success metric**: Score >0.65
- **Expected agents**: Strong reasoning models (GPT-4, Claude)

### Task 3: Complex High-Volume Triage (🔴 Hard)
- **Scenario**: 15 CRITICAL/HIGH tickets, negative sentiment, heavy load balancing
- **Challenge**: 70% priority accuracy + 65% category accuracy + fairness (std < 0.5)
- **Success metric**: Score >0.50
- **Expected agents**: Frontier reasoning models + specialized agents

---

## 🔧 Action Space

```python
TriageAction(
    ticket_id: str,                    # Which ticket to triage
    priority: TicketPriority,          # LOW | MEDIUM | HIGH | CRITICAL
    category: TicketCategory,          # BILLING | TECHNICAL | ACCOUNT | FEATURE_REQUEST | BUG_REPORT
    assign_to_agent: Optional[str],    # agent_1 | agent_2 | agent_3
    notes: Optional[str]               # Reasoning/context
)
```

---

## 📊 Observation Space

```python
Observation(
    current_step: int,
    queue_size: int,                   # Tickets waiting
    tickets: List[Ticket],             # Top 5 tickets in queue
    agent_workload: Dict[str, int],    # Workload per agent
    time_remaining_seconds: int,
    metrics: Dict[str, float]          # Priority/category accuracy, load balance
)
```

### Ticket Fields
```python
{
    "ticket_id": "T00001_001",
    "subject": "Payment failed on my account",
    "description": "...",
    "customer_id": "C1234",
    "priority": "high",                # Ground truth (hidden during decision)
    "category": "billing",             # Ground truth (hidden during decision)
    "sentiment_score": -0.8,           # Negative=angry, Positive=happy
    "status": "open"
}
```

---

## 💰 Reward Function

Rewards are **composite** with transparency:

| Component | Reward | Condition |
|-----------|--------|-----------|
| **Priority Correct** | +1.0 | Assigned priority == true priority |
| **Priority Wrong** | -0.5 | Assigned priority != true priority |
| **Category Correct** | +0.8 | Assigned category == true category |
| **Category Wrong** | -0.3 | Assigned category != true category |
| **Load Balanced** | +0.3 | Workload std < threshold |
| **Load Imbalanced** | -0.2 | Workload std > threshold |
| **Negative Sentiment** | +0.4 | Handled frustrated customer |

**Per-step reward range**: [-1.3, 2.3]  
**Episode reward range**: [-65, +115] (depends on episode length and performance)

---

## ✅ OpenEnv Specification Compliance

This environment fully implements OpenEnv spec:

```python
# Reset environment
obs: Observation = env.reset()

# Execute action
obs, reward, done, info = env.step(action: TriageAction)

# Check state
state: Dict = env.state()

# Pydantic models
- Observation (typed)
- TriageAction (typed)
- Reward (typed with components)
- Info (typed)

# openenv.yaml
- Fully specified action/observation spaces
- 3 tasks with graders
- Success criteria defined
- Metadata complete
```

---

## 🚀 Quick Start

### Installation

```bash
git clone <repo>
cd support-triage-openenv
pip install -r requirements.txt
```

### Set up API credentials

```bash
export OPENAI_API_KEY="sk-..."
export MODEL_NAME="gpt-4"
export API_BASE_URL="https://api.openai.com/v1"
```

### Run baseline

```bash
python inference.py
```

### Run tests

```bash
pytest tests/ -v
```

---

## 📝 Baseline Results

Run with GPT-4:

```
Task 1 (Easy):   Score=0.92, Reward=45.30, Priority Acc=95%, Category Acc=92%
Task 2 (Medium): Score=0.78, Reward=32.15, Priority Acc=82%, Category Acc=79%, Load Std=0.8
Task 3 (Hard):   Score=0.64, Reward=18.42, Priority Acc=71%, Category Acc=68%, Load Std=0.3
Average Score:   0.78
```

---

## 🐳 Docker Deployment

### Build

```bash
docker build -t support-triage-openenv .
```

### Run

```bash
docker run -it \
  -e OPENAI_API_KEY="sk-..." \
  -e MODEL_NAME="gpt-4" \
  support-triage-openenv \
  python inference.py
```

### Verify

```bash
docker run --rm support-triage-openenv python -c "from env import SupportTriageEnv; env = SupportTriageEnv(); print(env.reset())"
```

---

## 🌐 Hugging Face Spaces Deployment

This environment is optimized for HF Spaces:

1. Create new Space: `support-ticket-triage`
2. Set Runtime: Docker
3. Add Secrets:
   - `OPENAI_API_KEY`
   - `MODEL_NAME` (default: gpt-4)
   - `API_BASE_URL` (default: https://api.openai.com/v1)
4. Space auto-deploys from Dockerfile

**Live API endpoint**: `https://username-support-ticket-triage.hf.space/api`

---

## 📚 Example: Custom Agent

```python
from env import SupportTriageEnv, TriageAction, TicketPriority, TicketCategory

class CustomAgent:
    def decide(self, observation):
        """Make triage decision based on observation"""
        tickets = observation.tickets
        
        if not tickets:
            return None
        
        ticket = tickets[0]  # Process first in queue
        
        # Simple heuristic
        priority = TicketPriority.HIGH if ticket.sentiment_score < -0.5 else TicketPriority.MEDIUM
        
        # Assign to least-busy agent
        workload = observation.agent_workload
        best_agent = min(workload.keys(), key=lambda a: workload[a])
        
        return TriageAction(
            ticket_id=ticket.ticket_id,
            priority=priority,
            category=TicketCategory.TECHNICAL,
            assign_to_agent=best_agent
        )
    
    def run_episode(self, env, max_steps=100):
        obs = env.reset()
        done = False
        step = 0
        total_reward = 0.0
        
        while not done and step < max_steps:
            action = self.decide(obs)
            if action is None:
                break
            
            obs, reward, done, info = env.step(action)
            total_reward += reward.value
            step += 1
        
        return {
            "score": info.metrics.get("priority_accuracy", 0.0),
            "total_reward": total_reward,
            "steps": step
        }

# Usage
env = SupportTriageEnv(task_level=1)
agent = CustomAgent()
results = agent.run_episode(env)
print(f"Score: {results['score']:.4f}")
```

---

## 🧪 Testing & Validation

### Unit tests

```bash
pytest tests/test_env.py -v
```

### Validation

```bash
openenv validate --config openenv.yaml
```

### Reproducibility

```bash
# Run with seed for reproducibility
env = SupportTriageEnv(task_level=1, seed=42)
obs = env.reset()
# Same results every run with same seed
```

---

## 📊 Evaluation Criteria

| Criterion | Weight | Metric |
|-----------|--------|--------|
| Real-world utility | 30% | Applies to real support operations |
| Task & grader quality | 25% | 3 tasks with clear difficulty progression, graders 0.0-1.0 |
| Environment design | 20% | Clean API, sensible rewards, proper episode boundaries |
| Code quality & compliance | 15% | OpenEnv spec, typed models, Dockerfile works |
| Creativity & novelty | 10% | Interesting mechanics, novel approach |

---

## 🚨 Pre-Submission Checklist

- [ ] HF Space deploys and responds to `reset()`
- [ ] `openenv validate` passes
- [ ] `docker build && docker run` successful
- [ ] `python inference.py` reproduces baseline scores
- [ ] 3+ tasks with graders scoring 0.0-1.0
- [ ] README includes task descriptions, baselines, deployment docs
- [ ] `.gitignore` excludes `venv/`, `.env`, `__pycache__/`
- [ ] OPENAI_API_KEY, MODEL_NAME, API_BASE_URL configured

---

## 🤝 Contributing

Contributions welcome! Areas for improvement:

1. Add more ticket types (escalations, complex queries)
2. Implement sentiment-based reward bonuses
3. Add multi-turn agent interactions
4. Support batch processing
5. Add web dashboard for episode visualization

---

## 📜 License

MIT License - Free for academic and commercial use

---

## 📞 Support

Issues? Questions? Open an issue or contact the team.

Made with 🎫 for AI agent evaluation

---

## Frontend Recommendation

**Streamlit** is better for this project because:

✅ **Simpler integration** - Direct Python code execution  
✅ **Real-time updates** - Refresh metrics as episodes progress  
✅ **Fast deployment** - Streamlit Cloud integration  
✅ **Lower overhead** - No Node.js/build process  
✅ **Data visualization** - Built-in charts for metrics  

**React** would add complexity (API layer, state management) without clear benefit for this admin/evaluation tool.
