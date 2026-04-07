#!/usr/bin/env python3
"""
Baseline Agent for Med-Triage OpenEnv
Uses LLM API calls through the provided proxy for decision making
"""

import sys
import os
import json
from typing import Dict, List, Optional

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment.med_triage_env import TriageAction, TriageActionType

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class BaselineAgent:
    """Baseline agent using LLM API through provided proxy"""
    
    def __init__(self, config: Dict = None):
        """
        Initialize baseline agent with LLM API access
        
        Args:
            config: Optional config dict (ignored, uses env vars)
        """
        self.decision_history = []
        
        # Get API configuration from environment (injected by validator)
        self.api_base_url = os.getenv("API_BASE_URL")
        self.api_key = os.getenv("API_KEY")
        
        # Initialize OpenAI client with provided API proxy
        if self.api_base_url and self.api_key and OpenAI:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base_url
                )
                self.use_llm = True
                print(f"✓ LLM client initialized with API_BASE_URL: {self.api_base_url}", flush=True)
            except Exception as e:
                print(f"✗ Failed to initialize LLM client: {e}", flush=True)
                self.use_llm = False
                self.client = None
        else:
            print("⚠ API_BASE_URL or API_KEY not set, using heuristic mode", flush=True)
            self.use_llm = False
            self.client = None
    
    def get_llm_decision(self, patient: Dict) -> Optional[TriageAction]:
        """
        Get triage decision from LLM API through provided proxy
        
        Args:
            patient: Patient observation
        
        Returns:
            TriageAction based on LLM decision
        """
        if not self.use_llm or not self.client:
            return None
        
        try:
            # Prepare patient context for LLM
            vitals = patient.get("vitals", {})
            symptoms = patient.get("symptoms", [])
            
            prompt = f"""You are an emergency medicine triage expert. Based on the following patient presentation, 
assign an ESI (Emergency Severity Index) level (1-5):

Patient vitals:
- Heart Rate: {vitals.get('hr', 'N/A')} bpm
- Blood Pressure: {vitals.get('bp', 'N/A')} mmHg
- Oxygen Saturation: {vitals.get('o2', 'N/A')}%
- Temperature: {vitals.get('temp', 'N/A')}°C

Chief Complaints: {', '.join(symptoms) if symptoms else 'None reported'}

Respond with ONLY a single number 1-5:
1 = Immediate (life-threatening)
2 = Emergent (high risk situation)
3 = Urgent (moderate acuity)
4 = Less Urgent (low acuity)
5 = Non-Urgent (minimal acuity)"""

            # Call LLM API through proxy - this will use the provided API_BASE_URL and API_KEY
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a medical triage expert. Respond with only a number 1-5."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=10,
                timeout=10
            )
            
            # Parse ESI level from response
            response_text = response.choices[0].message.content.strip()
            try:
                esi_level = int(response_text)
                if 1 <= esi_level <= 5:
                    return TriageAction(
                        type=TriageActionType.ASSIGN_ESI,
                        patient_id=patient.get("id", "unknown"),
                        value=esi_level
                    )
            except (ValueError, AttributeError):
                pass
            
            return None
            
        except Exception as e:
            print(f"LLM API error: {e}", flush=True)
            return None
    
    def decide(self, observation: Dict) -> Optional[TriageAction]:
        """
        Make a triage decision based on observation
        
        Args:
            observation: Current environment observation
        
        Returns:
            TriageAction to execute
        """
        patients = observation.get("patients", [])
        
        if not patients:
            return None
        
        # Find untriaged patient
        untriaged = [p for p in patients if p.get("status") == "waiting"]
        
        if not untriaged:
            return None
        
        patient = untriaged[0]  # Process first patient
        patient_id = patient.get("id", "unknown")
        
        # Try LLM decision first (uses API_BASE_URL and API_KEY)
        if self.use_llm:
            llm_action = self.get_llm_decision(patient)
            if llm_action:
                self.decision_history.append(llm_action)
                return llm_action
        
        # Fallback to heuristic-based decision if LLM unavailable
        vitals = patient.get("vitals", {})
        symptoms = patient.get("symptoms", [])
        
        # Check urgency based on vitals
        hr = vitals.get("hr", 80)
        bp = vitals.get("bp", 120)
        o2 = vitals.get("o2", 95)
        
        # Critical vitals check
        if o2 < 90 or hr > 120 or (isinstance(bp, (int, float)) and bp < 80):
            esi_level = 2
        # Check for high-risk symptoms
        elif any(symptom in str(symptoms).lower() for symptom in ["chest pain", "difficulty breathing", "severe bleeding"]):
            esi_level = 2
        # Check for moderate symptoms
        elif any(symptom in str(symptoms).lower() for symptom in ["abdominal pain", "fever", "dizziness"]):
            esi_level = 3
        # Mild symptoms
        else:
            esi_level = 4
        
        action = TriageAction(
            type=TriageActionType.ASSIGN_ESI,
            patient_id=patient_id,
            value=esi_level
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
                "patients_triaged": len([p for p in obs["patients"] if p.get("status") == "triaged"]),
                "resource_units_used": env.resource_units - obs.get("resource_units_remaining", 0),
                "time_elapsed": obs.get("time_elapsed", 0)
            }
        }


if __name__ == "__main__":
    from environment.med_triage_env import MedTriageEnv
    
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
