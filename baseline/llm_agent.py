#!/usr/bin/env python3
"""
LLM Agent for Med-Triage OpenEnv
Uses OpenAI API for advanced clinical decision-making
"""

import sys
import os
import json
from typing import Dict, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment import TriageAction, TriageActionType
from baseline.agent import BaselineAgent

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class LLMAgent(BaselineAgent):
    """LLM-based agent for med-triage using OpenAI API"""
    
    def __init__(self, model: str = "gpt-3.5-turbo", api_key: Optional[str] = None):
        """
        Initialize LLM agent
        
        Args:
            model: OpenAI model to use
            api_key: OpenAI API key (uses OPENAI_API_KEY env var if not provided)
        """
        super().__init__(use_llm=True, llm_model=model)
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not installed. Install with: pip install openai")
        
        # Initialize OpenAI client
        if api_key is None:
            api_key = os.getenv("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.conversation_history = []
    
    def _create_system_prompt(self) -> str:
        """Create system prompt for LLM"""
        return """You are an expert emergency medicine physician assisting with triage decisions.
        
Your role is to analyze patient presentations and recommend ESI (Emergency Severity Index) levels:
- ESI-1: Resuscitation - immediately life-threatening
- ESI-2: Emergency - high-risk situations
- ESI-3: Urgent - stable but require prompt evaluation
- ESI-4: Less Urgent - stable and minor illness
- ESI-5: Minimal - minor illness, minimal testing needed

Always prioritize patient safety. When in doubt, escalate to a higher acuity level.
Provide concise, actionable recommendations."""
    
    def _create_patient_summary(self, observation: Dict) -> str:
        """Create a summary of patients for the LLM"""
        patients = observation.get("patients", [])
        summary = f"Current ED Status (Step {observation.get('step', 0)}):\n"
        summary += f"Resources remaining: {observation.get('resource_units_remaining', 0)}\n\n"
        
        for patient in patients:
            summary += f"Patient {patient['id']}:\n"
            summary += f"  Status: {patient.get('status', 'unknown')}\n"
            summary += f"  Symptoms: {', '.join(patient.get('symptoms', []))}\n"
            summary += f"  Vitals: BP={patient['vitals']['bp']}, HR={patient['vitals']['hr']}, "
            summary += f"Temp={patient['vitals']['temp']:.1f}°C, O2={patient['vitals']['o2']}%\n"
            summary += f"  ESI Level: {patient.get('triage_level', 'Not assigned')}\n"
            summary += f"  Tests Ordered: {', '.join(patient.get('tests_ordered', [])) or 'None'}\n\n"
        
        return summary
    
    def decide(self, observation: Dict) -> Optional[TriageAction]:
        """
        Make a triage decision using LLM
        
        Args:
            observation: Current environment observation
        
        Returns:
            TriageAction to execute
        """
        patients = observation.get("patients", [])
        
        # Find first untriaged patient
        untriaged = [p for p in patients if p["status"] == "waiting"]
        
        if not untriaged:
            return None
        
        patient = untriaged[0]
        patient_id = patient["id"]
        
        # Build prompt for LLM
        patient_summary = self._create_patient_summary(observation)
        user_prompt = f"""{patient_summary}

Which ESI level should {patient_id} be assigned? Respond with ONLY a number 1-5 and brief reasoning.
Format: ESI_LEVEL: [1-5]
REASONING: [brief explanation]"""
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._create_system_prompt()},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent decisions
                max_tokens=100
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            
            # Extract ESI level from response
            lines = response_text.strip().split('\n')
            esi_level = None
            
            for line in lines:
                if "ESI_LEVEL:" in line:
                    try:
                        esi_level = int(line.split(":")[-1].strip())
                        break
                    except (ValueError, IndexError):
                        pass
            
            # Fallback to heuristic if parsing fails
            if esi_level is None or esi_level < 1 or esi_level > 5:
                return super().decide(observation)
            
            action = TriageAction(
                type=TriageActionType.ASSIGN_ESI,
                patient_id=patient_id,
                value=esi_level
            )
            
            self.decision_history.append(action)
            return action
            
        except Exception as e:
            print(f"⚠️ LLM error: {e}. Falling back to heuristic.")
            return super().decide(observation)


class HybridAgent(BaselineAgent):
    """Hybrid agent combining heuristics with LLM for complex cases"""
    
    def __init__(self, use_llm: bool = True, llm_model: str = "gpt-3.5-turbo"):
        """Initialize hybrid agent"""
        super().__init__(use_llm=use_llm, llm_model=llm_model)
        self.llm_agent = None
        
        if use_llm:
            try:
                self.llm_agent = LLMAgent(model=llm_model)
            except (ImportError, ValueError) as e:
                print(f"⚠️ LLM not available: {e}. Using heuristics only.")
    
    def decide(self, observation: Dict) -> Optional[TriageAction]:
        """
        Make a decision using hybrid approach
        Heuristics for straightforward cases, LLM for complex ones
        """
        patients = observation.get("patients", [])
        
        # Find first untriaged patient
        untriaged = [p for p in patients if p["status"] == "waiting"]
        
        if not untriaged:
            return None
        
        patient = untriaged[0]
        vitals = patient["vitals"]
        
        # Use heuristics for critical/obvious cases
        o2 = vitals["o2"]
        hr = vitals["hr"]
        bp = vitals["bp"]
        
        # Critical case - use heuristic
        if o2 < 90 or hr > 120 or bp < 80:
            return super().decide(observation)
        
        # Use LLM for complex cases
        if self.llm_agent:
            return self.llm_agent.decide(observation)
        else:
            return super().decide(observation)


if __name__ == "__main__":
    from environment import MedTriageEnv
    
    print("Testing LLM Agent...")
    print("Note: Requires OPENAI_API_KEY environment variable\n")
    
    try:
        env = MedTriageEnv(task_level=1)
        agent = HybridAgent(use_llm=False)  # Start with heuristics for testing
        
        results = agent.run_episode(env)
        
        print("\n=== Episode Results ===")
        print(f"Steps: {results['steps']}")
        print(f"Total Reward: {results['total_reward']:.2f}")
        print(f"Avg Reward: {results['avg_reward']:.2f}")
        print(f"Patients Triaged: {results['episode_summary']['patients_triaged']}")
        
    except Exception as e:
        print(f"Error: {e}")
