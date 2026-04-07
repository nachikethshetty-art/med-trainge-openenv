#!/usr/bin/env python3
"""
Med-Triage OpenEnv - Clinical Triage Environment
Temporal reasoning + resource-constrained decision making
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
import random


# Simple gym-like base class for compatibility
class Env:
    """Minimal gym.Env replacement"""
    def render(self, mode='human'):
        pass


class TriageActionType(str, Enum):
    """Valid triage actions"""
    ASSIGN_ESI = "assign_esi"
    ORDER_TEST = "order_test"
    MONITOR = "monitor"
    QUERY = "query"
    DISCHARGE = "discharge"


class TriageAction(BaseModel):
    """Structured action for triage decisions"""
    type: TriageActionType
    patient_id: str
    value: Optional[int] = None  # ESI level (1-5)
    tool: Optional[str] = None    # Test type
    minutes: Optional[int] = None # Monitor duration
    text: Optional[str] = None    # Query text


class PatientState(str, Enum):
    """Patient health states"""
    STABLE = "A"              # Stable condition
    DECOMPENSATING = "B"      # Getting worse (hidden)
    CRITICAL = "C"            # Critical state
    DISCHARGED = "D"          # Discharged


class Patient:
    """Represents a patient in the ER"""
    
    def __init__(self, patient_id: str, symptoms: List[str], condition: str):
        self.id = patient_id
        self.symptoms = symptoms
        self.true_condition = condition  # Hidden from agent
        self.state = PatientState.STABLE
        self.state_timer = 0  # Time until next state change
        self.deterioration_rate = 0.0  # How quickly patient deteriorates
        self.deterioration_threshold = None  # When to trigger deterioration
        self.vitals = {
            "bp": np.random.randint(110, 150),  # Systolic BP
            "hr": np.random.randint(60, 100),    # Heart rate
            "temp": np.random.uniform(37.0, 38.5),  # Temperature
            "o2": np.random.randint(95, 100)     # O2 saturation
        }
        self.triage_level = None  # ESI level (1-5)
        self.tests_ordered = []
        self.status = "waiting"
        self.expired = False
        self.deterioration_detected_at = None  # Track when deterioration was detected
    
    def update_vitals(self, deteriorate: bool = False):
        """Update vitals based on patient state"""
        if deteriorate:
            self.vitals["bp"] -= np.random.randint(2, 5)
            self.vitals["hr"] += np.random.randint(3, 8)
            self.vitals["temp"] += np.random.uniform(0.1, 0.5)
            self.vitals["o2"] -= np.random.randint(1, 3)
        else:
            # Small random fluctuations
            self.vitals["bp"] += np.random.randint(-2, 3)
            self.vitals["hr"] += np.random.randint(-2, 3)
            self.vitals["o2"] = min(100, self.vitals["o2"] + np.random.randint(-1, 2))
    
    def check_critical(self):
        """Check if patient has reached critical state"""
        if self.vitals["o2"] < 88 or self.vitals["hr"] > 120 or self.vitals["bp"] < 80:
            self.state = PatientState.CRITICAL
            return True
        return False
    
    def get_observation(self) -> Dict:
        """Get observable patient data (hidden state excluded)"""
        return {
            "id": self.id,
            "symptoms": self.symptoms,
            "vitals": self.vitals.copy(),
            "status": self.status,
            "triage_level": self.triage_level,
            "tests_ordered": self.tests_ordered.copy()
        }


class MedTriageEnv(Env):
    """
    Med-Triage OpenEnv Environment
    Evaluates AI agents on temporal clinical reasoning
    """
    
    def __init__(self, task_level: int = 1, max_steps: int = 50, seed: int = None):
        """
        Initialize environment
        
        Args:
            task_level: 1 (clear-cut), 2 (resource war), 3 (sepsis bomb)
            max_steps: Maximum steps per episode
            seed: Random seed for reproducibility
        """
        self.task_level = task_level
        self.max_steps = max_steps
        self.seed_value = seed
        
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
        
        # Environment state
        self.patients = []
        self.current_step = 0
        self.resource_units = self._get_resource_units()
        self.episode_reward = 0.0
        self.done = False
        
        # Episode history
        self.action_history = []
        self.reward_history = []
    
    def _get_resource_units(self) -> int:
        """Get available resource units based on task level"""
        if self.task_level == 1:
            return 20  # Plenty of resources
        elif self.task_level == 2:
            return 5   # Limited resources
        else:
            return 8   # Moderate resources
    
    def _generate_patients(self):
        """Generate patient cohort based on task level"""
        self.patients = []
        
        if self.task_level == 1:
            # Clear-cut cases
            self.patients.append(Patient("P1", ["fever", "cough"], "pneumonia"))
            self.patients.append(Patient("P2", ["laceration"], "wound"))
            self.patients.append(Patient("P3", ["headache"], "migraine"))
        
        elif self.task_level == 2:
            # Resource war - mixed severity
            self.patients.append(Patient("P1", ["chest pain"], "stable_angina"))
            self.patients.append(Patient("P2", ["abdominal pain"], "appendicitis"))
            self.patients.append(Patient("P3", ["dizziness"], "dehydration"))
        
        else:  # task_level == 3
            # Sepsis time bomb - critical hidden condition with temporal dynamics
            sepsis_patient = Patient("P1", ["mild fever", "fatigue"], "sepsis")
            sepsis_patient.deterioration_threshold = 15  # Deteriorate after 15 steps
            sepsis_patient.deterioration_rate = 0.8  # Aggressive deterioration
            self.patients.append(sepsis_patient)
            
            self.patients.append(Patient("P2", ["nausea"], "gastroenteritis"))
            self.patients.append(Patient("P3", ["cough"], "cold"))
    
    def reset(self) -> Dict:
        """Reset environment and return initial observation"""
        self.current_step = 0
        self.episode_reward = 0.0
        self.done = False
        self.action_history = []
        self.reward_history = []
        self.resource_units = self._get_resource_units()
        
        self._generate_patients()
        
        return self._get_observation()
    
    def _get_observation(self) -> Dict:
        """Get current observation"""
        return {
            "patients": [p.get_observation() for p in self.patients],
            "resource_units_remaining": self.resource_units,
            "time_elapsed": self.current_step,
            "step": self.current_step,
            "max_steps": self.max_steps
        }
    
    def step(self, action: TriageAction) -> Tuple[Dict, float, bool, Dict]:
        """
        Execute action and return (observation, reward, done, info)
        
        Args:
            action: TriageAction object with decision
        
        Returns:
            Tuple of (observation, reward, done, info)
        """
        reward = 0.0
        info = {"action": action.model_dump()}
        
        # Find patient
        patient = None
        for p in self.patients:
            if p.id == action.patient_id:
                patient = p
                break
        
        if patient is None:
            reward = -0.5
            info["error"] = "Patient not found"
            self.current_step += 1
            return self._get_observation(), reward, False, info
        
        # Process action
        if action.type == TriageActionType.ASSIGN_ESI:
            reward += self._assign_esi(patient, action.value)
        
        elif action.type == TriageActionType.ORDER_TEST:
            reward += self._order_test(patient, action.tool)
        
        elif action.type == TriageActionType.MONITOR:
            reward += self._monitor_patient(patient, action.minutes)
        
        elif action.type == TriageActionType.QUERY:
            reward += self._nurse_query(patient, action.text)
        
        elif action.type == TriageActionType.DISCHARGE:
            reward += self._discharge_patient(patient)
        
        # Update environment
        self.current_step += 1
        self.episode_reward += reward
        self.action_history.append(action)
        self.reward_history.append(reward)
        
        # Update patient states (temporal dynamics)
        self._update_patient_states()
        
        # Check termination conditions
        all_triaged = all(p.status in ["discharged", "triaged"] for p in self.patients)
        patient_expired = any(p.expired for p in self.patients)
        
        if patient_expired:
            self.done = True
            reward = -2.0  # Critical miss penalty
        elif all_triaged:
            self.done = True
        elif self.current_step >= self.max_steps:
            self.done = True
        
        return self._get_observation(), reward, self.done, info
    
    def _update_patient_states(self):
        """Update patient states based on temporal dynamics"""
        for patient in self.patients:
            # Check if patient should deteriorate (Task 3)
            if patient.deterioration_threshold is not None:
                if self.current_step >= patient.deterioration_threshold:
                    if patient.state == PatientState.STABLE:
                        patient.state = PatientState.DECOMPENSATING
                        patient.deterioration_detected_at = None
                    
                    # Deteriorate vitals aggressively
                    patient.update_vitals(deteriorate=True)
                    
                    # Check for critical state
                    if patient.check_critical():
                        # Critical patient should be escalated
                        if patient.status not in ["triaged", "discharged"]:
                            # Not properly triaged - high risk
                            if patient.triage_level and patient.triage_level > 2:
                                # Under-triaged critical patient
                                patient.expired = True
    
    def _assign_esi(self, patient: Patient, esi_level: int) -> float:
        """Assign ESI triage level"""
        if patient.triage_level is not None:
            return -0.2  # Already triaged
        
        patient.triage_level = esi_level
        patient.status = "triaged"
        
        # Calculate reward based on accuracy
        correct_level = self._get_true_esi(patient)
        
        if esi_level == correct_level:
            return 1.0
        elif abs(esi_level - correct_level) == 1:
            return 0.5  # Close call
        else:
            return -1.0 if esi_level > correct_level else -0.5  # Under/over triage
    
    def _get_true_esi(self, patient: Patient) -> int:
        """Get true ESI level for patient"""
        if patient.state == PatientState.CRITICAL:
            return 2
        elif patient.state == PatientState.DECOMPENSATING:
            return 3
        elif patient.true_condition in ["appendicitis", "sepsis", "pneumonia"]:
            return 3
        elif patient.true_condition in ["stable_angina", "gastroenteritis"]:
            return 4
        else:
            return 5
    
    def _order_test(self, patient: Patient, test_type: str) -> float:
        """Order a diagnostic test"""
        if self.resource_units <= 0:
            return -0.1  # No resources
        
        self.resource_units -= 1
        patient.tests_ordered.append(test_type)
        
        # Appropriate testing gets small reward
        if test_type in ["blood_culture", "ct_scan", "ekg"]:
            return 0.1
        else:
            return -0.2  # Over-testing
    
    def _monitor_patient(self, patient: Patient, minutes: int) -> float:
        """Monitor patient for specified duration"""
        if minutes is None or minutes < 1:
            return 0.0
        
        reward = 0.0
        
        # Simulate time passing
        for _ in range(minutes):
            patient.update_vitals(deteriorate=(patient.state == PatientState.DECOMPENSATING))
            
            # Check for deterioration
            if patient.check_critical():
                patient.expired = True
                return -2.0  # Patient expired during monitoring
        
        # Early detection of deterioration = reward
        if patient.state == PatientState.DECOMPENSATING:
            reward += 0.3  # Caught early deterioration
        
        return reward
    
    def _nurse_query(self, patient: Patient, query: str) -> float:
        """Query nurse for additional information"""
        if query is None or len(query) < 3:
            return -0.1  # Spam query
        
        return 0.1  # Smart information gathering
    
    def _discharge_patient(self, patient: Patient) -> float:
        """Discharge patient"""
        patient.status = "discharged"
        
        if patient.state == PatientState.CRITICAL:
            return -2.0  # Discharged critical patient
        
        return 0.5  # Appropriate discharge
    
    def render(self, mode='human'):
        """Render current state"""
        print(f"\n=== Step {self.current_step} ===")
        print(f"Resource Units: {self.resource_units}")
        print(f"Episode Reward: {self.episode_reward:.2f}")
        print("\nPatients:")
        for p in self.patients:
            print(f"  {p.id}: {p.status} | ESI: {p.triage_level} | HR: {p.vitals['hr']} | BP: {p.vitals['bp']}")
    
    def state(self) -> Dict:
        """Get current environment state"""
        return self._get_observation()


if __name__ == "__main__":
    # Test environment
    env = MedTriageEnv(task_level=1)
    obs = env.reset()
    print("Initial observation:", obs)
    
    # Sample action
    action = TriageAction(
        type=TriageActionType.ASSIGN_ESI,
        patient_id="P1",
        value=3
    )
    obs, reward, done, info = env.step(action)
    print(f"Reward: {reward}, Done: {done}")
    env.render()
