#!/usr/bin/env python3
"""
Tests for Med-Triage OpenEnv
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from environment import MedTriageEnv, TriageAction, TriageActionType


def test_env_creation():
    """Test environment creation"""
    env = MedTriageEnv(task_level=1)
    assert env is not None
    print("✅ Environment creation test passed")


def test_env_reset():
    """Test environment reset"""
    env = MedTriageEnv(task_level=1)
    obs = env.reset()
    
    assert obs is not None
    assert "patients" in obs
    assert "resource_units_remaining" in obs
    assert "time_elapsed" in obs
    print("✅ Environment reset test passed")


def test_env_step():
    """Test environment step"""
    env = MedTriageEnv(task_level=1)
    obs = env.reset()
    
    # Get first patient
    patient_id = obs["patients"][0]["id"]
    
    # Create action
    action = TriageAction(
        type=TriageActionType.ASSIGN_ESI,
        patient_id=patient_id,
        value=3
    )
    
    obs, reward, done, info = env.step(action)
    
    assert obs is not None
    assert isinstance(reward, float)
    assert isinstance(done, bool)
    assert isinstance(info, dict)
    print("✅ Environment step test passed")


def test_task_levels():
    """Test different task levels"""
    for task_level in [1, 2, 3]:
        env = MedTriageEnv(task_level=task_level)
        obs = env.reset()
        
        assert len(obs["patients"]) > 0
        assert obs["resource_units_remaining"] > 0
        print(f"✅ Task level {task_level} test passed")


def test_episode_completion():
    """Test complete episode"""
    env = MedTriageEnv(task_level=1, max_steps=20)
    obs = env.reset()
    
    step = 0
    total_reward = 0
    
    while not env.done and step < 20:
        # Triage first available patient
        for patient in obs["patients"]:
            if patient["status"] == "waiting":
                action = TriageAction(
                    type=TriageActionType.ASSIGN_ESI,
                    patient_id=patient["id"],
                    value=3
                )
                obs, reward, done, info = env.step(action)
                total_reward += reward
                step += 1
                break
        else:
            break
    
    print(f"✅ Episode completion test passed (Steps: {step}, Reward: {total_reward:.2f})")


if __name__ == "__main__":
    print("\n=== Running Med-Triage Tests ===\n")
    
    test_env_creation()
    test_env_reset()
    test_env_step()
    test_task_levels()
    test_episode_completion()
    
    print("\n✅ All tests passed!")
