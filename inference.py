#!/usr/bin/env python3
"""
Baseline Inference Script for Med-Triage OpenEnv Hackathon
Demonstrates agent evaluation across 3 task levels with structured logging
"""

import os
import json
import sys
import time
from datetime import datetime
from typing import Dict, Any

# Environment variables
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.getenv("MODEL_NAME", "groq-mixtral-8x7b")

# Import environment and agent
from environment.med_triage_env import MedTriageEnv, TriageAction, TriageActionType
from baseline.agent import BaselineAgent


def log_start(task_name: str, task_level: str):
    """Emit [START] log"""
    timestamp = datetime.now().isoformat()
    log = {
        "event": "START",
        "timestamp": timestamp,
        "task": task_name,
        "task_level": task_level,
        "model": MODEL_NAME,
        "api_base": API_BASE_URL
    }
    print(json.dumps(log))
    sys.stdout.flush()


def log_step(step_num: int, action_type: str, reward: float, done: bool):
    """Emit [STEP] log"""
    timestamp = datetime.now().isoformat()
    log = {
        "event": "STEP",
        "timestamp": timestamp,
        "step": step_num,
        "action_type": action_type,
        "reward": round(float(reward), 4),
        "done": done
    }
    print(json.dumps(log))
    sys.stdout.flush()


def log_end(task_name: str, task_level: str, total_reward: float, episodes: int, 
            avg_reward: float, success_rate: float, status: str):
    """Emit [END] log"""
    timestamp = datetime.now().isoformat()
    log = {
        "event": "END",
        "timestamp": timestamp,
        "task": task_name,
        "task_level": task_level,
        "total_reward": round(float(total_reward), 4),
        "episodes_run": episodes,
        "average_reward": round(float(avg_reward), 4),
        "success_rate": round(float(success_rate), 4),
        "status": status,
        "model": MODEL_NAME
    }
    print(json.dumps(log))
    sys.stdout.flush()


def run_episode(env: MedTriageEnv, agent: BaselineAgent, max_steps: int = 20) -> Dict:
    """Run a single episode and return metrics"""
    obs = env.reset()
    
    total_reward = 0.0
    step_count = 0
    actions_taken = []
    
    for step in range(max_steps):
        # Get action from agent
        try:
            action = agent.decide(obs)
            
            if action is None:
                break
            
            # Step environment
            obs, reward, done, info = env.step(action)
            
            # Extract reward value
            if isinstance(reward, dict):
                step_reward = reward.get("total_reward", 0.0)
            else:
                step_reward = float(reward) if reward else 0.0
            
            total_reward += step_reward
            step_count += 1
            actions_taken.append(str(action.type))
            
            # Log step
            log_step(step + 1, str(action.type), step_reward, done)
            
            if done:
                break
                
        except Exception as e:
            print(json.dumps({
                "event": "ERROR",
                "timestamp": datetime.now().isoformat(),
                "step": step + 1,
                "error": str(e)
            }), file=sys.stderr)
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
    
    # Map task levels to names
    task_levels = {
        1: "easy",
        2: "medium", 
        3: "hard"
    }
    
    # Run evaluation on all 3 task levels
    results = {}
    overall_scores = []
    
    for task_level in [1, 2, 3]:
        task_name = task_levels[task_level]
        print(f"\n{'='*80}")
        print(f"📊 Evaluating: {task_name.upper()} (Task Level {task_level})")
        print(f"{'='*80}\n")
        
        log_start("Med-Triage", task_name)
        
        # Initialize environment for this task level
        try:
            env = MedTriageEnv(task_level=task_level, max_steps=50)
        except Exception as e:
            print(json.dumps({
                "event": "ERROR",
                "message": f"Failed to initialize environment: {e}"
            }))
            continue
        
        # Initialize agent
        try:
            config = {
                "groq_key": os.getenv("GROQ"),
                "gemini_key": os.getenv("GEMINI"),
            }
            agent = BaselineAgent(config)
        except Exception as e:
            print(json.dumps({
                "event": "ERROR",
                "message": f"Failed to initialize agent: {e}"
            }))
            continue
        
        # Run multiple episodes for this task level
        if task_level == 1:
            num_episodes = 3
        elif task_level == 2:
            num_episodes = 2
        elif task_level == 3:
            num_episodes = 1
        else:
            num_episodes = 1
        episodes_data = []
        
        for episode in range(num_episodes):
            print(f"Episode {episode + 1}/{num_episodes}...", end=" ", flush=True)
            
            try:
                episode_result = run_episode(env, agent, max_steps=20)
                episodes_data.append(episode_result)
                print(f"✓ Reward: {episode_result['total_reward']:.4f}")
                
            except Exception as e:
                print(f"✗ Error: {e}")
                continue
        
        # Calculate metrics for this task level
        if episodes_data:
            total_reward = sum(ep["total_reward"] for ep in episodes_data)
            avg_reward = total_reward / len(episodes_data)
            
            # Clamp average reward to strictly between 0 and 1 (exclusive bounds)
            avg_reward = min(max(avg_reward, 0.001), 0.999)
            
            # Estimate success rate (reward > 5.0 = success)
            success_count = sum(1 for ep in episodes_data if ep["total_reward"] > 5.0)
            success_rate = success_count / len(episodes_data)
            
            # Clamp success rate to strictly between 0 and 1 (exclusive bounds)
            success_rate = min(max(success_rate, 0.001), 0.999)
            
            results[task_name] = {
                "episodes": len(episodes_data),
                "total_reward": total_reward,
                "average_reward": avg_reward,
                "success_rate": success_rate,
                "episodes_data": episodes_data
            }
            
            overall_scores.append(avg_reward)
            
            log_end(
                task_name="Med-Triage",
                task_level=task_name,
                total_reward=total_reward,
                episodes=len(episodes_data),
                avg_reward=avg_reward,
                success_rate=success_rate,
                status="completed"
            )
        else:
            log_end(
                task_name="Med-Triage",
                task_level=task_name,
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
    
    for task_name, data in results.items():
        print(f"{task_name.upper():10} | Episodes: {data['episodes']:2} | "
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
