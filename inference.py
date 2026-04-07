#!/usr/bin/env python3
"""
Baseline Inference Script for Med-Triage OpenEnv Hackathon
Demonstrates agent evaluation across 3 task levels with structured [START]/[STEP]/[END] logging
"""

import os
import sys
from datetime import datetime
from typing import Dict, Any

# Import environment and agent
from environment.med_triage_env import MedTriageEnv, TriageAction, TriageActionType
from baseline.agent import BaselineAgent


def log_start(task_name: str, task_level: str):
    """Emit [START] block to stdout"""
    print(f"[START] task={task_name} level={task_level}", flush=True)


def log_step(step_num: int, reward: float, done: bool):
    """Emit [STEP] block to stdout"""
    print(f"[STEP] step={step_num} reward={reward:.4f} done={done}", flush=True)


def log_end(task_name: str, task_level: str, total_reward: float, episodes: int, 
            avg_reward: float, success_rate: float, steps: int):
    """Emit [END] block to stdout"""
    print(f"[END] task={task_name} level={task_level} score={avg_reward:.4f} episodes={episodes} steps={steps} success_rate={success_rate:.2f}", flush=True)



def run_episode(env: MedTriageEnv, agent: BaselineAgent, max_steps: int = 20) -> Dict:
    """Run a single episode and return metrics"""
    obs = env.reset()
    
    total_reward = 0.0
    step_count = 0
    
    for step in range(max_steps):
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
            
            # Log step with structured format
            log_step(step + 1, step_reward, done)
            
            if done:
                break
                
        except Exception as e:
            print(f"[ERROR] step={step + 1} error={str(e)}", flush=True)
            break
    
    return {
        "total_reward": total_reward,
        "steps": step_count,
        "avg_reward_per_step": total_reward / step_count if step_count > 0 else 0,
    }



def main():
    """Main evaluation script"""
    
    print("=" * 80, flush=True)
    print("🏥 Med-Triage OpenEnv - Baseline Agent Evaluation", flush=True)
    print("=" * 80, flush=True)
    print(flush=True)
    
    # Map task levels to names
    task_levels = {
        1: "easy",
        2: "medium", 
        3: "hard"
    }
    
    # Run evaluation on all 3 task levels
    results = {}
    all_steps = 0
    
    for task_level in [1, 2, 3]:
        task_name = task_levels[task_level]
        print(f"\n{'='*80}", flush=True)
        print(f"📊 Evaluating: {task_name.upper()} (Task Level {task_level})", flush=True)
        print(f"{'='*80}\n", flush=True)
        
        # Emit [START] block
        log_start("Med-Triage", task_name)
        
        # Initialize environment for this task level
        try:
            env = MedTriageEnv(task_level=task_level, max_steps=50)
        except Exception as e:
            print(f"[ERROR] Failed to initialize environment: {e}", flush=True)
            continue
        
        # Initialize agent
        try:
            config = {
                "groq_key": os.getenv("GROQ"),
                "gemini_key": os.getenv("GEMINI"),
            }
            agent = BaselineAgent(config)
        except Exception as e:
            print(f"[ERROR] Failed to initialize agent: {e}", flush=True)
            continue
        
        # Run multiple episodes for this task level
        num_episodes = 3 if task_level == 1 else 2 if task_level == 2 else 1
        episodes_data = []
        total_episode_steps = 0
        
        for episode in range(num_episodes):
            print(f"Episode {episode + 1}/{num_episodes}...", flush=True)
            
            try:
                episode_result = run_episode(env, agent, max_steps=20)
                episodes_data.append(episode_result)
                total_episode_steps += episode_result["steps"]
                print(f"✓ Episode {episode + 1} complete - Reward: {episode_result['total_reward']:.4f}", flush=True)
                
            except Exception as e:
                print(f"[ERROR] Episode {episode + 1} failed: {e}", flush=True)
                continue
        
        # Calculate metrics for this task level
        if episodes_data:
            total_reward = sum(ep["total_reward"] for ep in episodes_data)
            avg_reward = total_reward / len(episodes_data)
            
            # Estimate success rate (reward > 5.0 = success)
            success_count = sum(1 for ep in episodes_data if ep["total_reward"] > 5.0)
            success_rate = success_count / len(episodes_data)
            
            results[task_name] = {
                "episodes": len(episodes_data),
                "total_reward": total_reward,
                "average_reward": avg_reward,
                "success_rate": success_rate,
                "steps": total_episode_steps
            }
            
            all_steps += total_episode_steps
            
            # Emit [END] block with required format
            log_end(
                task_name="Med-Triage",
                task_level=task_name,
                total_reward=total_reward,
                episodes=len(episodes_data),
                avg_reward=avg_reward,
                success_rate=success_rate,
                steps=total_episode_steps
            )
        else:
            # Emit [END] block even on failure
            log_end(
                task_name="Med-Triage",
                task_level=task_name,
                total_reward=0,
                episodes=0,
                avg_reward=0,
                success_rate=0,
                steps=0
            )
    
    # Print summary
    print(f"\n{'='*80}", flush=True)
    print("📈 SUMMARY RESULTS", flush=True)
    print(f"{'='*80}\n", flush=True)
    
    for task_name, data in results.items():
        print(f"{task_name.upper():10} | Episodes: {data['episodes']:2} | "
              f"Avg Reward: {data['average_reward']:.4f} | "
              f"Success Rate: {data['success_rate']:.1%} | "
              f"Steps: {data['steps']}", flush=True)
    
    print(f"\n{'='*80}", flush=True)
    print("✅ Evaluation Complete", flush=True)
    print(f"{'='*80}\n", flush=True)



if __name__ == "__main__":
    main()
