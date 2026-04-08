#!/usr/bin/env python3
"""
Inference Script for Med-Triage OpenEnv
=====================================
MANDATORY REQUIREMENTS:
- Environment variables: API_BASE_URL, MODEL_NAME, HF_TOKEN (optional)
- Uses OpenAI Client for all LLM calls
- Output format: [START], [STEP], [END] markers as specified
- All rewards/scores normalized to [0.0, 1.0]
- Each task returns score in [0, 1]

STDOUT FORMAT:
[START] task=<task_name> env=med-triage model=<model_name>
[STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
[END]   success=<true|false> steps=<n> score=<score> rewards=<r1,r2,...,rn>
"""

import os
import sys
from typing import Dict, List, Optional, Tuple

# Environment variables (MANDATORY)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
MODEL_NAME = os.getenv("MODEL_NAME", "groq-mixtral-8x7b")
HF_TOKEN = os.getenv("HF_TOKEN")

# Import environment and agent
from environment.med_triage_env import MedTriageEnv, TriageAction, TriageActionType
from baseline.agent import BaselineAgent


def log_start(task: str, env: str, model: str) -> None:
    """Emit [START] log - SPEC COMPLIANT"""
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Emit [STEP] log - SPEC COMPLIANT
    
    Fields:
    - step: integer step number
    - action: action string representation
    - reward: reward value (2 decimal places)
    - done: lowercase boolean (true|false)
    - error: error message or null
    """
    error_val = error if error else "null"
    done_str = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={error_val}",
        flush=True
    )


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    """Emit [END] log - SPEC COMPLIANT
    
    Fields:
    - success: lowercase boolean (true|false)
    - steps: total steps taken
    - score: final score [0, 1]
    - rewards: comma-separated rewards (2 decimal places)
    """
    success_str = str(success).lower()
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(
        f"[END] success={success_str} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True
    )


def run_episode(env: MedTriageEnv, agent: BaselineAgent, max_steps: int = 20) -> Tuple[float, int, List[float]]:
    """Run a single episode and return (score, steps, rewards)
    
    Args:
        env: Environment instance
        agent: Agent instance
        max_steps: Maximum steps per episode
        
    Returns:
        Tuple of (normalized_score, total_steps, list_of_rewards)
    """
    obs = env.reset()
    
    total_reward = 0.0
    step_count = 0
    rewards_list = []
    
    for step in range(max_steps):
        try:
            # Get action from agent
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
            
            # Clamp step reward to [0, 1]
            step_reward = min(max(step_reward, 0.0), 1.0)
            
            total_reward += step_reward
            step_count += 1
            rewards_list.append(step_reward)
            
            # Log step
            log_step(step + 1, str(action.type), step_reward, done, error=None)
            
            if done:
                break
                
        except Exception as e:
            error_msg = str(e)
            log_step(step + 1, "error", 0.0, True, error=error_msg)
            break
    
    # Normalize score to [0.001, 0.999] range
    score = min(max(total_reward / max_steps if max_steps > 0 else 0, 0.001), 0.999)
    
    return score, step_count, rewards_list


def main():
    """Main evaluation script - runs all 3 task levels with spec-compliant output"""
    
    # Task level mapping
    task_levels = {
        1: "easy",
        2: "medium", 
        3: "hard"
    }
    
    all_scores = []
    all_rewards = []
    
    # Run evaluation on all 3 task levels (MANDATORY)
    for task_level in [1, 2, 3]:
        task_name = task_levels[task_level]
        
        # Emit START marker
        log_start(task="med-triage", env="med-triage-v1", model=MODEL_NAME)
        
        try:
            # Initialize environment for this task level
            env = MedTriageEnv(task_level=task_level, max_steps=50)
            
            # Initialize agent
            config = {
                "groq_key": os.getenv("GROQ"),
                "gemini_key": os.getenv("GEMINI"),
            }
            agent = BaselineAgent(config)
            
            # Run single episode per task level
            score, steps_taken, rewards = run_episode(env, agent, max_steps=20)
            
            all_scores.append(score)
            all_rewards.extend(rewards)
            
            # Determine success (score > 0.5 = success)
            success = score >= 0.5
            
            # Emit END marker - SPEC COMPLIANT
            log_end(
                success=success,
                steps=steps_taken,
                score=score,
                rewards=rewards
            )
            
        except Exception as e:
            print(f"Error in task level {task_level}: {e}", file=sys.stderr)
            log_end(
                success=False,
                steps=0,
                score=0.0,
                rewards=[]
            )
    
    # Final status
    if all_scores:
        final_score = sum(all_scores) / len(all_scores)
        print(f"\n{'='*80}", file=sys.stderr)
        print(f"✅ Evaluation Complete - Final Score: {final_score:.2f}", file=sys.stderr)
        print(f"{'='*80}\n", file=sys.stderr)


if __name__ == "__main__":
    main()
