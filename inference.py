#!/usr/bin/env python3
"""
Baseline Inference Script for Med-Triage OpenEnv Hackathon
Demonstrates agent evaluation across 3 difficulty levels with structured logging
"""

import os
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any

# Environment variables (set these before running)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.getenv("MODEL_NAME", "groq-mixtral-8x7b")
HF_TOKEN = os.getenv("HF_TOKEN", "")

# Import environment and agent
from environment.med_triage_env import SupportTriageEnv
from baseline.agent import TicketTriageAgent


def log_start(task_name: str, difficulty: str):
    """Emit [START] log"""
    timestamp = datetime.now().isoformat()
    log = {
        "event": "START",
        "timestamp": timestamp,
        "task": task_name,
        "difficulty": difficulty,
        "model": MODEL_NAME,
        "api_base": API_BASE_URL
    }
    print(json.dumps(log))
    sys.stdout.flush()


def log_step(step_num: int, action: Dict[str, Any], reward: float, done: bool):
    """Emit [STEP] log"""
    timestamp = datetime.now().isoformat()
    log = {
        "event": "STEP",
        "timestamp": timestamp,
        "step": step_num,
        "action": {
            "ticket_id": action.get("ticket_id"),
            "priority": action.get("priority"),
            "category": action.get("category"),
            "agent": action.get("agent_id")
        },
        "reward": round(float(reward), 4),
        "done": done
    }
    print(json.dumps(log))
    sys.stdout.flush()


def log_end(task_name: str, difficulty: str, total_reward: float, episodes: int, 
            avg_reward: float, success_rate: float, status: str):
    """Emit [END] log"""
    timestamp = datetime.now().isoformat()
    log = {
        "event": "END",
        "timestamp": timestamp,
        "task": task_name,
        "difficulty": difficulty,
        "total_reward": round(float(total_reward), 4),
        "episodes_run": episodes,
        "average_reward": round(float(avg_reward), 4),
        "success_rate": round(float(success_rate), 4),
        "status": status,
        "model": MODEL_NAME
    }
    print(json.dumps(log))
    sys.stdout.flush()


def run_episode(env: SupportTriageEnv, agent: TicketTriageAgent, difficulty: str, max_steps: int = 20):
    """Run a single episode and return metrics"""
    obs, info = env.reset(difficulty=difficulty)
    
    total_reward = 0
    step_count = 0
    actions_taken = []
    
    for step in range(max_steps):
        # Get action from agent
        try:
            action = agent.get_triage_decision(
                ticket_dict=obs.current_ticket.__dict__ if obs.current_ticket else {},
                agent_workload=obs.agent_workloads or {}
            )
            
            # Convert Pydantic model to dict if needed
            if hasattr(action, '__dict__'):
                action_dict = action.__dict__
            else:
                action_dict = action
                
            # Step environment
            obs, reward, done, truncated, info = env.step(action)
            
            # Accumulate reward
            if hasattr(reward, 'total_reward'):
                step_reward = reward.total_reward
            else:
                step_reward = float(reward)
            
            total_reward += step_reward
            step_count += 1
            actions_taken.append(action_dict)
            
            # Log step
            log_step(step + 1, action_dict, step_reward, done or truncated)
            
            if done or truncated:
                break
                
        except Exception as e:
            print(json.dumps({
                "event": "ERROR",
                "timestamp": datetime.now().isoformat(),
                "step": step + 1,
                "error": str(e)
            }))
            break
    
    return {
        "total_reward": total_reward,
        "steps": step_count,
        "avg_reward_per_step": total_reward / step_count if step_count > 0 else 0,
        "actions": actions_taken
    }


def main():
    """Main evaluation script"""
    
    print("=" * 80)
    print("🏥 Med-Triage OpenEnv - Baseline Agent Evaluation")
    print("=" * 80)
    print()
    
    # Initialize environment
    try:
        env = SupportTriageEnv()
    except Exception as e:
        print(json.dumps({
            "event": "ERROR",
            "message": f"Failed to initialize environment: {e}"
        }))
        sys.exit(1)
    
    # Initialize agent
    try:
        config = {
            "groq_key": os.getenv("GROQ"),
            "gemini_key": os.getenv("GEMINI"),
        }
        agent = TicketTriageAgent(config)
    except Exception as e:
        print(json.dumps({
            "event": "ERROR",
            "message": f"Failed to initialize agent: {e}"
        }))
        sys.exit(1)
    
    # Run evaluation on all 3 difficulty levels
    results = {}
    overall_scores = []
    
    for difficulty in ["easy", "medium", "hard"]:
        print(f"\n{'='*80}")
        print(f"📊 Evaluating: {difficulty.upper()} Difficulty")
        print(f"{'='*80}\n")
        
        log_start("Med-Triage", difficulty)
        
        # Run multiple episodes for this difficulty
        num_episodes = 3 if difficulty == "easy" else 2 if difficulty == "medium" else 1
        episodes_data = []
        
        for episode in range(num_episodes):
            print(f"Episode {episode + 1}/{num_episodes}...", end=" ", flush=True)
            
            try:
                episode_result = run_episode(env, agent, difficulty)
                episodes_data.append(episode_result)
                print(f"✓ Reward: {episode_result['total_reward']:.4f}")
                
            except Exception as e:
                print(f"✗ Error: {e}")
                continue
        
        # Calculate metrics for this difficulty
        if episodes_data:
            total_reward = sum(ep["total_reward"] for ep in episodes_data)
            avg_reward = total_reward / len(episodes_data)
            
            # Estimate success rate (reward > 0.5 = success)
            success_count = sum(1 for ep in episodes_data if ep["total_reward"] > 0.5)
            success_rate = success_count / len(episodes_data)
            
            results[difficulty] = {
                "episodes": len(episodes_data),
                "total_reward": total_reward,
                "average_reward": avg_reward,
                "success_rate": success_rate,
                "episodes_data": episodes_data
            }
            
            overall_scores.append(avg_reward)
            
            log_end(
                task_name="Med-Triage",
                difficulty=difficulty,
                total_reward=total_reward,
                episodes=len(episodes_data),
                avg_reward=avg_reward,
                success_rate=success_rate,
                status="completed"
            )
        else:
            log_end(
                task_name="Med-Triage",
                difficulty=difficulty,
                total_reward=0,
                episodes=0,
                avg_reward=0,
                success_rate=0,
                status="failed"
            )
    
    # Print summary
    print(f"\n{'='*80}")
    print("📈 SUMMARY RESULTS")
    print(f"{'='*80}\n")
    
    for difficulty, data in results.items():
        print(f"{difficulty.upper():10} | Episodes: {data['episodes']:2} | "
              f"Avg Reward: {data['average_reward']:.4f} | "
              f"Success Rate: {data['success_rate']:.1%}")
    
    if overall_scores:
        avg_score = sum(overall_scores) / len(overall_scores)
        print(f"\n{'OVERALL':10} | Average Score: {avg_score:.4f}")
    
    print(f"\n{'='*80}")
    print("✅ Evaluation Complete")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
