#!/usr/bin/env python3
"""
Baseline Agent for Med-Triage OpenEnv
Uses simple heuristics + LLM for decision making
"""

import sys
import os
import json
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment.med_triage_env import TriageAction, TriageActionType
import random

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class BaselineAgent:
    """Simple baseline agent for med-triage"""
    
    def __init__(self, use_llm: bool = False, llm_model: str = "gpt-3.5-turbo"):
        """
        Initialize baseline agent
        
        Args:
            use_llm: Whether to use LLM for decision making
            llm_model: LLM model to use
        """
        self.use_llm = use_llm
        self.llm_model = llm_model
        self.decision_history = []
    
    def decide(self, observation: Dict) -> TriageAction:
        """
        Make a triage decision based on observation
        
        Args:
            observation: Current environment observation
        
        Returns:
            TriageAction to execute
        """
        patients = observation["patients"]
        resource_units = observation["resource_units_remaining"]
        time_elapsed = observation["time_elapsed"]
        
        if not patients:
            return None
        
        # Find untriaged patient
        untriaged = [p for p in patients if p["status"] == "waiting"]
        
        if not untriaged:
            return None
        
        patient = untriaged[0]  # Process first patient
        patient_id = patient["id"]
        
        # Heuristic-based decision making
        vitals = patient["vitals"]
        symptoms = patient["symptoms"]
        
        # Check urgency based on vitals
        hr = vitals["hr"]
        bp = vitals["bp"]
        o2 = vitals["o2"]
        
        # Critical vitals check
        if o2 < 90 or hr > 120 or bp < 80:
            # Immediately escalate
            action = TriageAction(
                type=TriageActionType.ASSIGN_ESI,
                patient_id=patient_id,
                value=2
            )
        
        # Check for high-risk symptoms
        elif any(symptom in symptoms for symptom in ["chest pain", "difficulty breathing", "severe bleeding"]):
            action = TriageAction(
                type=TriageActionType.ASSIGN_ESI,
                patient_id=patient_id,
                value=3
            )
        
        # Check for moderate symptoms
        elif any(symptom in symptoms for symptom in ["abdominal pain", "fever", "dizziness"]):
            action = TriageAction(
                type=TriageActionType.ASSIGN_ESI,
                patient_id=patient_id,
                value=4
            )
        
        # Mild symptoms
        else:
            action = TriageAction(
                type=TriageActionType.ASSIGN_ESI,
                patient_id=patient_id,
                value=5
            )
        
        self.decision_history.append(action)
        return action
    
    def run_episode(self, env, max_steps: int = 50) -> Dict:
        """
        Run complete episode with baseline agent
        
        Args:
            env: Environment instance
            max_steps: Maximum steps per episode
        
        Returns:
            Episode statistics
        """
        obs = env.reset()
        done = False
        step = 0
        total_reward = 0
        actions_taken = []
        
        while not done and step < max_steps:
            action = self.decide(obs)
            
            if action is None:
                break
            
            obs, reward, done, info = env.step(action)
            total_reward += reward
            actions_taken.append(action.model_dump())
            step += 1
        
        return {
            "steps": step,
            "total_reward": total_reward,
            "avg_reward": total_reward / step if step > 0 else 0,
            "done": done,
            "actions": actions_taken,
            "episode_summary": {
                "patients_triaged": len([p for p in obs["patients"] if p["status"] == "triaged"]),
                "resource_units_used": env.resource_units - obs["resource_units_remaining"],
                "time_elapsed": obs["time_elapsed"]
            }
        }


if __name__ == "__main__":
    from environment import MedTriageEnv
    
    print("Testing Baseline Agent...")
    env = MedTriageEnv(task_level=1)
    agent = BaselineAgent()
    
    results = agent.run_episode(env)
    
    print("\n=== Episode Results ===")
    print(f"Steps: {results['steps']}")
    print(f"Total Reward: {results['total_reward']:.2f}")
    print(f"Avg Reward: {results['avg_reward']:.2f}")
    print(f"Patients Triaged: {results['episode_summary']['patients_triaged']}")
    print(f"Resources Used: {results['episode_summary']['resource_units_used']}")
