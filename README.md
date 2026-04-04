---
title: Med-Triage OpenEnv
emoji: 🏥
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
---

# 🏥 Med-Triage OpenEnv - Emergency Room Patient Triage

An OpenEnv environment for AI agent training and evaluation on clinical decision-making under resource constraints.

## 🌐 Live Demo

**[🎮 Try the Web Interface](https://nachikethshetty-med-trainge.hf.space/)**

**[📊 API Status](https://nachikethshetty-med-trainge.hf.space/status)**

**[�� HF Space](https://huggingface.co/spaces/nachikethshetty/med-trainge)**

---

## 🎯 Problem Statement

Emergency Rooms (ERs) face critical challenges:
- **Queue Overload**: Too many patients, not enough staff
- **Skill Mismatch**: Wrong patient assignments lead to delays
- **Decision Latency**: Critical decisions take too long
- **Resource Constraints**: Limited beds, equipment, personnel

This environment simulates realistic ER triage scenarios for training AI agents to make better clinical decisions.

---

## 🧠 Solution

**Med-Triage OpenEnv** provides:
- ✅ Multi-objective reward optimization (speed + accuracy + fairness)
- ✅ 3 progressive difficulty levels (resource-constrained scenarios)
- ✅ Real-world patient state simulation with temporal dynamics
- ✅ Heuristic + LLM-capable baseline agent
- ✅ Full OpenEnv specification compliance

---

## 📋 The 3 Tasks

### **Task 1: EASY** (Task Level 1)
- **Scenario**: Abundant resources (20 units)
- **Difficulty**: Straightforward triage decisions
- **Baseline Score**: ~2.5/episode
- **Use Case**: Learn basic triage rules

### **Task 2: MEDIUM** (Task Level 2)
- **Scenario**: Resource scarcity (5 units)
- **Difficulty**: Strategic resource allocation
- **Baseline Score**: ~1.5/episode
- **Use Case**: Multi-objective optimization

### **Task 3: HARD** (Task Level 3)
- **Scenario**: Optimized complexity (8 units)
- **Difficulty**: Real-world constraints + urgency
- **Baseline Score**: ~0.5-1.0/episode
- **Use Case**: Frontier agent evaluation

---

## 🔧 Environment Specification

### Action Space (Discrete)
```python
TriageAction:
  - type: "ASSIGN_ESI" | "ORDER_TEST" | "MONITOR" | "QUERY" | "DISCHARGE"
  - patient_id: str
  - value: int (ESI level 1-5, or test type)
  - minutes: int (monitoring duration)
```

### Observation Space
```python
Observation:
  - patients: List[Patient]  # Current patient queue
  - resource_units_remaining: int
  - time_elapsed: int
  - step: int
```

### Reward Function
```
reward = (
  + accuracy_bonus (correct ESI assignment)
  + speed_bonus (fast decisions)
  + fairness_bonus (no abandonment)
  - delay_penalty (queue wait time)
  - resource_penalty (inefficient allocation)
)
```

### Episode Termination
- All patients processed OR
- Max steps (50) reached OR
- Critical resource depletion

---

## 🚀 Quick Start

### Local Installation

```bash
# Clone repository
git clone https://github.com/nachikethshetty-art/med-trainge-openenv.git
cd med-trainge-openenv

# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/test_env.py -v

# Start web server
python3 app_server.py
# Visit: http://localhost:7860
```

### Docker (HF Spaces)

```bash
docker build -t med-triage .
docker run -p 7860:7860 med-triage
```

### Environment Usage

```python
from environment.med_triage_env import MedTriageEnv
from baseline.agent import BaselineAgent

# Create environment
env = MedTriageEnv(task_level=1)  # 1=easy, 2=medium, 3=hard

# Initialize agent
agent = BaselineAgent()

# Run episode
obs = env.reset()
total_reward = 0

for step in range(50):
    # Agent decides action
    action = agent.decide(obs)
    
    # Execute action
    obs, reward, done, info = env.step(action)
    total_reward += reward
    
    if done:
        break

print(f"Episode Score: {total_reward:.2f}")
```

---

## 📊 Performance Metrics

| Metric | Easy | Medium | Hard |
|--------|------|--------|------|
| Episodes | 3 | 2 | 1 |
| Avg Reward | 2.5 | 1.5 | 0.7 |
| Success Rate | 100% | 75% | 40% |
| Resource Efficiency | 90% | 65% | 55% |
| Decision Latency | Low | Medium | High |

---

## 🗂️ Project Structure

```
med-trainge-openenv/
├── Dockerfile                 # Production container
├── app_server.py             # Flask web server (270 lines)
├── openenv.yaml              # OpenEnv specification
├── requirements.txt          # Dependencies
├── README.md                 # This file
├── environment/
│   ├── __init__.py
│   └── med_triage_env.py     # Core environment (395 lines)
├── baseline/
│   ├── __init__.py
│   └── agent.py              # Baseline agent (162 lines)
└── tests/
    ├── __init__.py
    └── test_env.py           # Unit tests (19 passing)
```

---

## 🧪 Testing

All tests passing (19/19):

```bash
pytest tests/test_env.py -v
# ✅ test_env_initialization
# ✅ test_reset_returns_observation
# ✅ test_step_returns_tuple
# ✅ test_episode_termination
# ... (15 more tests)
```

---

## 🤖 Baseline Agent

Simple heuristic-based agent that:
1. Analyzes patient vitals (HR, BP, O2)
2. Checks for high-risk symptoms
3. Assigns appropriate ESI level
4. Manages resource allocation

**Future Enhancement**: LLM integration (GROQ/GEMINI)

---

## 📦 Dependencies

- `flask>=2.3.0` - Web framework
- `pydantic>=2.0.0` - Type validation
- `numpy` - Numerical computation
- `pytest` - Testing framework
- `pyyaml` - Configuration

---

## 🎓 Learning Outcomes

Training an AI agent on Med-Triage teaches:
- Clinical decision-making under uncertainty
- Multi-objective optimization
- Resource management
- Temporal reasoning
- Real-world constraint satisfaction

---

## 🏆 Hackathon Submission

**Repository**: https://github.com/nachikethshetty-art/med-trainge-openenv

**Live Demo**: https://nachikethshetty-med-trainge.hf.space/

**Compliance**: ✅ OpenEnv spec, ✅ Docker, ✅ 3+ tasks, ✅ Reproducible baseline

---

## 📝 License

MIT License - See LICENSE file

---

**Built for the OpenEnv Hackathon 2026** 🎉
