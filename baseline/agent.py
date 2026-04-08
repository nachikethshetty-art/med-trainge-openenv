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
    
    def __init__(self, use_llm: bool = True, llm_model: str = "gpt-3.5-turbo", config: dict = None):
        """
        Initialize baseline agent
        
        Args:
            use_llm: Whether to use LLM for decision making (default True)
            llm_model: LLM model to use
            config: Optional config dict (for compatibility)
        """
        self.use_llm = use_llm
        self.llm_model = llm_model
        self.decision_history = []
        
        # Initialize LLM client - ALWAYS use the provided API_BASE_URL and API_KEY
        if OpenAI:
            # Get API credentials from environment (MANDATORY for LiteLLM proxy)
            self.api_base_url = os.getenv("API_BASE_URL")
            self.api_key = os.getenv("API_KEY")
            
            # Validate that proxy credentials are provided
            if not self.api_base_url or not self.api_key:
                raise ValueError(
                    "Missing required environment variables: API_BASE_URL and API_KEY. "
                    "These must be provided by the evaluation framework."
                )
            
            # Initialize OpenAI client with the proxy endpoint
            self.llm_client = OpenAI(
                api_key=self.api_key,
                base_url=self.api_base_url
            )
        else:
            self.llm_client = None
    
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
        
        # Use LLM if available and enabled
        if self.use_llm and self.llm_client:
            return self._decide_with_llm(patient, resource_units, time_elapsed)
        else:
            return self._decide_with_heuristics(patient)
    
    def _decide_with_llm(self, patient: Dict, resource_units: int, time_elapsed: int) -> TriageAction:
        """
        Use LLM to make triage decision
        Makes API call through the injected API_BASE_URL and API_KEY
        """
        try:
            vitals = patient["vitals"]
            symptoms = patient["symptoms"]
            
            # Prepare context for LLM
            prompt = f"""You are an emergency medicine triage specialist. 
Given the following patient information, assign an ESI (Emergency Severity Index) level (1-5):
- Level 1: Immediate/Life-threatening
- Level 2: Emergent
- Level 3: Urgent
- Level 4: Semi-urgent
- Level 5: Non-urgent

Patient ID: {patient['id']}
Vitals: HR={vitals['hr']}, BP={vitals['bp']}, O2={vitals['o2']}%
Symptoms: {', '.join(symptoms)}
Resources available: {resource_units} units
Time elapsed: {time_elapsed}s

Respond with ONLY a single integer (1-5) representing the ESI level."""
            
            # Make API call through the LiteLLM proxy
            response = self.llm_client.chat.completions.create(
                model=self.llm_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=10
            )
            
            # Parse ESI level from response
            esi_level = int(response.choices[0].message.content.strip())
            esi_level = max(1, min(esi_level, 5))  # Clamp to [1, 5]
            
            action = TriageAction(
                type=TriageActionType.ASSIGN_ESI,
                patient_id=patient["id"],
                value=esi_level
            )
            
            self.decision_history.append(action)
            return action
            
        except Exception as e:
            # Fall back to heuristics if LLM fails
            print(f"LLM error: {e}, falling back to heuristics", file=sys.stderr)
            return self._decide_with_heuristics(patient)
    
    def _decide_with_heuristics(self, patient: Dict) -> TriageAction:
        """
        Use heuristics for triage decision (fallback)
        """
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
                patient_id=patient["id"],
                value=2
            )
        
        # Check for high-risk symptoms
        elif any(symptom in symptoms for symptom in ["chest pain", "difficulty breathing", "severe bleeding"]):
            action = TriageAction(
                type=TriageActionType.ASSIGN_ESI,
                patient_id=patient["id"],
                value=3
            )
        
        # Check for moderate symptoms
        elif any(symptom in symptoms for symptom in ["abdominal pain", "fever", "dizziness"]):
            action = TriageAction(
                type=TriageActionType.ASSIGN_ESI,
                patient_id=patient["id"],
                value=4
            )
        
        # Mild symptoms
        else:
            action = TriageAction(
                type=TriageActionType.ASSIGN_ESI,
                patient_id=patient["id"],
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
