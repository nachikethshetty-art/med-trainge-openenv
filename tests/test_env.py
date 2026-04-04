#!/usr/bin/env python3
"""
Tests for Support Ticket Triage OpenEnv
"""

import sys
import os
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from env import (
    SupportTriageEnv, TriageAction, TicketPriority, TicketCategory,
    TaskGrader, Observation, Reward
)


class TestEnvironmentBasics:
    """Test basic environment functionality"""
    
    def test_env_creation(self):
        """Test environment can be created"""
        env = SupportTriageEnv(task_level=1)
        assert env is not None
        assert env.task_level == 1
    
    def test_reset(self):
        """Test reset returns valid observation"""
        env = SupportTriageEnv(task_level=1)
        obs = env.reset()
        
        assert isinstance(obs, Observation)
        assert obs.current_step == 0
        assert obs.queue_size > 0
        assert len(obs.tickets) > 0
    
    def test_action_execution(self):
        """Test step() executes action"""
        env = SupportTriageEnv(task_level=1)
        obs = env.reset()
        
        ticket = obs.tickets[0]
        action = TriageAction(
            ticket_id=ticket.ticket_id,
            priority=TicketPriority.HIGH,
            category=TicketCategory.TECHNICAL,
            assign_to_agent="agent_1"
        )
        
        obs, reward, done, info = env.step(action)
        
        assert isinstance(reward, Reward)
        assert isinstance(obs, Observation)
        assert isinstance(done, bool)
        assert reward.value is not None
    
    def test_state(self):
        """Test state() method"""
        env = SupportTriageEnv(task_level=1)
        env.reset()
        
        state = env.state()
        assert isinstance(state, dict)
        assert "step" in state
        assert "done" in state
        assert "queue_size" in state


class TestTaskLevels:
    """Test different task difficulty levels"""
    
    @pytest.mark.parametrize("task_level", [1, 2, 3])
    def test_task_level_creation(self, task_level):
        """Test each task level can be created"""
        env = SupportTriageEnv(task_level=task_level)
        obs = env.reset()
        
        assert obs.queue_size > 0
        assert env.task_level == task_level
    
    def test_task_1_easy(self):
        """Test Task 1 (Easy) has manageable queue"""
        env = SupportTriageEnv(task_level=1)
        obs = env.reset()
        
        # Task 1 should have ~5 tickets
        assert obs.queue_size <= 10
    
    def test_task_2_medium(self):
        """Test Task 2 (Medium) has larger queue"""
        env = SupportTriageEnv(task_level=2)
        obs = env.reset()
        
        # Task 2 should have ~10 tickets
        assert obs.queue_size >= 8
    
    def test_task_3_hard(self):
        """Test Task 3 (Hard) has larger queue"""
        env = SupportTriageEnv(task_level=3)
        obs = env.reset()
        
        # Task 3 should have ~15 tickets
        assert obs.queue_size >= 10


class TestRewards:
    """Test reward calculation"""
    
    def test_correct_priority_reward(self):
        """Test reward for correct priority"""
        env = SupportTriageEnv(task_level=1)
        obs = env.reset()
        
        ticket = obs.tickets[0]
        true_priority = ticket.priority
        
        action = TriageAction(
            ticket_id=ticket.ticket_id,
            priority=true_priority,  # Correct
            category=TicketCategory.TECHNICAL,
            assign_to_agent="agent_1"
        )
        
        _, reward, _, _ = env.step(action)
        assert reward.value > 0  # Should be positive for correct
    
    def test_invalid_ticket_penalty(self):
        """Test penalty for invalid ticket"""
        env = SupportTriageEnv(task_level=1)
        env.reset()
        
        action = TriageAction(
            ticket_id="INVALID_ID",
            priority=TicketPriority.HIGH,
            category=TicketCategory.TECHNICAL,
            assign_to_agent="agent_1"
        )
        
        _, reward, _, _ = env.step(action)
        assert reward.value < 0  # Penalty for invalid ticket


class TestGraders:
    """Test task graders"""
    
    def test_grader_creation(self):
        """Test grader can be created"""
        grader = TaskGrader(task_level=1)
        assert grader is not None
    
    def test_grader_scoring(self):
        """Test grader produces valid scores"""
        env = SupportTriageEnv(task_level=1)
        obs = env.reset()
        
        # Run simple episode
        for _ in range(3):
            if not obs.tickets:
                break
            
            ticket = obs.tickets[0]
            action = TriageAction(
                ticket_id=ticket.ticket_id,
                priority=ticket.priority,
                category=ticket.category,
                assign_to_agent="agent_1"
            )
            
            obs, reward, done, info = env.step(action)
        
        grader = TaskGrader(task_level=1)
        score = grader.grade(env, env.total_reward, info.metrics)
        
        assert 0.0 <= score <= 1.0
    
    @pytest.mark.parametrize("task_level", [1, 2, 3])
    def test_grader_range(self, task_level):
        """Test grader scores in valid range for all tasks"""
        env = SupportTriageEnv(task_level=task_level, max_steps=5)
        obs = env.reset()
        
        # Run minimal episode
        for _ in range(2):
            if not obs.tickets:
                break
            
            ticket = obs.tickets[0]
            action = TriageAction(
                ticket_id=ticket.ticket_id,
                priority=ticket.priority,
                category=ticket.category,
                assign_to_agent="agent_1"
            )
            
            obs, reward, done, info = env.step(action)
        
        grader = TaskGrader(task_level)
        score = grader.grade(env, env.total_reward, info.metrics)
        
        assert 0.0 <= score <= 1.0, f"Task {task_level} score out of range: {score}"


class TestEpisodeCompletion:
    """Test full episodes"""
    
    def test_episode_terminates(self):
        """Test episode terminates properly"""
        env = SupportTriageEnv(task_level=1, max_steps=10)
        obs = env.reset()
        
        step_count = 0
        while not env.done and step_count < 20:
            if not obs.tickets:
                break
            
            ticket = obs.tickets[0]
            action = TriageAction(
                ticket_id=ticket.ticket_id,
                priority=ticket.priority,
                category=ticket.category,
                assign_to_agent="agent_1"
            )
            
            obs, reward, done, info = env.step(action)
            step_count += 1
        
        assert env.done or step_count >= 10
    
    def test_reproducibility_with_seed(self):
        """Test reproducibility with fixed seed"""
        # First run
        env1 = SupportTriageEnv(task_level=1, seed=42)
        obs1 = env1.reset()
        queue_size_1 = obs1.queue_size
        first_ticket_1 = obs1.tickets[0].ticket_id if obs1.tickets else None
        
        # Second run with same seed
        env2 = SupportTriageEnv(task_level=1, seed=42)
        obs2 = env2.reset()
        queue_size_2 = obs2.queue_size
        first_ticket_2 = obs2.tickets[0].ticket_id if obs2.tickets else None
        
        assert queue_size_1 == queue_size_2
        assert first_ticket_1 == first_ticket_2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
