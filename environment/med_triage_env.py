#!/usr/bin/env python3
"""
Support Ticket Triage OpenEnv
Real-world customer support ticket triaging environment
"""

import json
import random
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import numpy as np


# ============================================================================
# OpenEnv Models - Full Compliance
# ============================================================================

class TicketPriority(str, Enum):
    """Ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketCategory(str, Enum):
    """Ticket categories"""
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    FEATURE_REQUEST = "feature_request"
    BUG_REPORT = "bug_report"


class TicketStatus(str, Enum):
    """Ticket lifecycle status"""
    OPEN = "open"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class Ticket(BaseModel):
    """Individual support ticket"""
    ticket_id: str
    subject: str
    description: str
    customer_id: str
    created_at: str
    priority: TicketPriority
    category: TicketCategory
    status: TicketStatus
    assigned_to: Optional[str] = None
    sentiment_score: float = Field(ge=-1.0, le=1.0)  # -1 to 1
    wait_time_minutes: int = 0
    resolution_time_minutes: Optional[int] = None
    customer_satisfaction: Optional[float] = Field(None, ge=0.0, le=5.0)


class Observation(BaseModel):
    """Environment observation"""
    current_step: int
    queue_size: int
    tickets: List[Ticket]
    agent_workload: Dict[str, int]  # agent_id -> ticket_count
    time_remaining_seconds: int
    metrics: Dict[str, float] = {
        "avg_resolution_time": 0.0,
        "customer_satisfaction_avg": 0.0,
        "tickets_resolved_today": 0,
        "queue_wait_time_avg": 0.0
    }


class TriageAction(BaseModel):
    """Action to triage a ticket"""
    ticket_id: str
    priority: TicketPriority
    category: TicketCategory
    assign_to_agent: Optional[str] = None  # agent_id or None for auto-queue
    notes: Optional[str] = None


class Reward(BaseModel):
    """Reward structure"""
    value: float = Field(ge=-10.0, le=10.0)
    components: Dict[str, float] = {}  # Breakdown for transparency


class Info(BaseModel):
    """Episode info"""
    step: int
    done: bool
    episode_length: int
    total_reward: float
    success: bool
    metrics: Dict[str, Any] = {}


# ============================================================================
# Core Environment
# ============================================================================

class SupportTriageEnv:
    """
    Customer Support Ticket Triage Environment
    Simulates real-world ticket triaging with multiple agents and performance metrics
    """
    
    def __init__(self, task_level: int = 1, max_steps: int = 100, seed: int = None):
        """
        Initialize environment
        
        Args:
            task_level: 1 (easy), 2 (medium), 3 (hard)
            max_steps: Episode length
            seed: Random seed
        """
        self.task_level = task_level
        self.max_steps = max_steps
        self.seed_value = seed
        
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        
        # State tracking
        self.current_step = 0
        self.done = False
        self.tickets_queue: List[Ticket] = []
        self.agents = {"agent_1": 0, "agent_2": 0, "agent_3": 0}
        self.resolved_tickets: List[Ticket] = []
        self.episode_start_time = datetime.now()
        self.total_reward = 0.0
        
        # Metrics
        self.correctly_prioritized = 0
        self.correctly_categorized = 0
        self.total_triaged = 0
        
    def reset(self) -> Observation:
        """Reset environment and return initial observation"""
        self.current_step = 0
        self.done = False
        self.tickets_queue = []
        self.agents = {"agent_1": 0, "agent_2": 0, "agent_3": 0}
        self.resolved_tickets = []
        self.episode_start_time = datetime.now()
        self.total_reward = 0.0
        self.correctly_prioritized = 0
        self.correctly_categorized = 0
        self.total_triaged = 0
        
        # Generate initial tickets
        self._generate_initial_tickets()
        
        return self._get_observation()
    
    def state(self) -> Dict:
        """Get current state (OpenEnv spec)"""
        return {
            "step": self.current_step,
            "done": self.done,
            "queue_size": len(self.tickets_queue),
            "agents": self.agents.copy(),
            "resolved_tickets_count": len(self.resolved_tickets),
            "total_reward": self.total_reward
        }
    
    def _generate_initial_tickets(self):
        """Generate initial queue of tickets based on task level"""
        base_count = {1: 5, 2: 10, 3: 15}.get(self.task_level, 5)
        
        categories = list(TicketCategory)
        base_priorities = {
            1: [TicketPriority.LOW, TicketPriority.MEDIUM],  # Easy
            2: [TicketPriority.LOW, TicketPriority.MEDIUM, TicketPriority.HIGH],  # Medium
            3: list(TicketPriority)  # Hard - all priorities
        }
        
        priorities = base_priorities.get(self.task_level, [TicketPriority.LOW, TicketPriority.MEDIUM])
        
        for i in range(base_count):
            ticket = Ticket(
                ticket_id=f"T{self.current_step:05d}_{i:03d}",
                subject=self._generate_subject(),
                description=self._generate_description(),
                customer_id=f"C{random.randint(1000, 9999)}",
                created_at=datetime.now().isoformat(),
                priority=random.choice(priorities),
                category=random.choice(categories),
                status=TicketStatus.OPEN,
                sentiment_score=random.uniform(-1.0, 1.0)
            )
            self.tickets_queue.append(ticket)
    
    def _generate_subject(self) -> str:
        """Generate realistic ticket subject"""
        subjects = [
            "Payment failed on my account",
            "App crashes on login",
            "Cannot reset password",
            "Billing inquiry about recurring charges",
            "Feature request: dark mode",
            "Bug: search not working",
            "Account locked after failed attempts",
            "Upgrade subscription issue",
            "Performance problems on iOS",
            "Export data request"
        ]
        return random.choice(subjects)
    
    def _generate_description(self) -> str:
        """Generate realistic ticket description"""
        return f"Customer reported issue with detailed description. Severity level: {random.choice(['low', 'medium', 'high'])}."
    
    def step(self, action: TriageAction) -> Tuple[Observation, Reward, bool, Info]:
        """
        Execute action and return (observation, reward, done, info)
        
        Args:
            action: TriageAction object
        
        Returns:
            Tuple of (observation, reward, done, info)
        """
        reward_components = {}
        
        # Find ticket
        ticket = None
        for t in self.tickets_queue:
            if t.ticket_id == action.ticket_id:
                ticket = t
                break
        
        if ticket is None:
            reward_val = -1.0
            reward_components["invalid_ticket"] = -1.0
        else:
            # Remove from queue
            self.tickets_queue.remove(ticket)
            
            # Calculate reward
            reward_val, components = self._calculate_reward(ticket, action)
            reward_components.update(components)
            
            # Update metrics
            self.total_triaged += 1
            if action.priority == ticket.priority:
                self.correctly_prioritized += 1
            if action.category == ticket.category:
                self.correctly_categorized += 1
            
            # Assign to agent
            if action.assign_to_agent:
                self.agents[action.assign_to_agent] += 1
            
            # Mark as assigned
            ticket.status = TicketStatus.ASSIGNED
            ticket.assigned_to = action.assign_to_agent
            self.resolved_tickets.append(ticket)
        
        self.current_step += 1
        self.total_reward += reward_val
        
        # Check episode end
        if self.current_step >= self.max_steps or len(self.tickets_queue) == 0:
            self.done = True
        
        # Return OpenEnv format
        obs = self._get_observation()
        reward = Reward(value=reward_val, components=reward_components)
        info = Info(
            step=self.current_step,
            done=self.done,
            episode_length=self.current_step,
            total_reward=self.total_reward,
            success=self._is_successful(),
            metrics=self._get_metrics()
        )
        
        return obs, reward, self.done, info
    
    def _calculate_reward(self, ticket: Ticket, action: TriageAction) -> Tuple[float, Dict]:
        """Calculate reward for action"""
        components = {}
        total = 0.0
        
        # Priority classification accuracy (+1.0 for correct, -0.5 for wrong)
        if action.priority == ticket.priority:
            components["priority_correct"] = 1.0
            total += 1.0
        else:
            components["priority_incorrect"] = -0.5
            total -= 0.5
        
        # Category classification accuracy (+0.8 for correct, -0.3 for wrong)
        if action.category == ticket.category:
            components["category_correct"] = 0.8
            total += 0.8
        else:
            components["category_incorrect"] = -0.3
            total -= 0.3
        
        # Load balancing - even distribution bonus (+0.3)
        workload_std = np.std(list(self.agents.values()))
        if workload_std < 2.0:
            components["load_balanced"] = 0.3
            total += 0.3
        else:
            components["load_imbalanced"] = -0.2
            total -= 0.2
        
        # Sentiment handling (+0.4 for negative sentiment)
        if ticket.sentiment_score < -0.3:
            components["negative_sentiment_handled"] = 0.4
            total += 0.4
        
        return total, components
    
    def _is_successful(self) -> bool:
        """Determine if episode was successful"""
        if self.total_triaged == 0:
            return False
        accuracy = (self.correctly_prioritized + self.correctly_categorized) / (2 * self.total_triaged)
        return accuracy > 0.7
    
    def _get_metrics(self) -> Dict[str, Any]:
        """Get episode metrics"""
        if self.total_triaged == 0:
            return {
                "priority_accuracy": 0.0,
                "category_accuracy": 0.0,
                "load_balance_std": 0.0
            }
        
        return {
            "priority_accuracy": self.correctly_prioritized / self.total_triaged,
            "category_accuracy": self.correctly_categorized / self.total_triaged,
            "load_balance_std": float(np.std(list(self.agents.values()))),
            "tickets_triaged": self.total_triaged
        }
    
    def _get_observation(self) -> Observation:
        """Get current observation"""
        return Observation(
            current_step=self.current_step,
            queue_size=len(self.tickets_queue),
            tickets=self.tickets_queue[:5],  # Show top 5
            agent_workload=self.agents.copy(),
            time_remaining_seconds=max(0, (self.max_steps - self.current_step) * 10),
            metrics={
                "priority_accuracy": self.correctly_prioritized / max(1, self.total_triaged),
                "category_accuracy": self.correctly_categorized / max(1, self.total_triaged),
                "load_balance_std": float(np.std(list(self.agents.values()))),
                "tickets_resolved": len(self.resolved_tickets)
            }
        )


# ============================================================================
# Task Graders
# ============================================================================

class TaskGrader:
    """Evaluates agent performance on a task"""
    
    def __init__(self, task_level: int):
        self.task_level = task_level
    
    def grade(self, env: SupportTriageEnv, episode_reward: float, metrics: Dict) -> float:
        """
        Grade agent performance (0.0 to 1.0)
        
        Args:
            env: Environment after episode
            episode_reward: Total reward from episode
            metrics: Episode metrics
        
        Returns:
            Score 0.0-1.0
        """
        priority_acc = metrics.get("priority_accuracy", 0.0)
        category_acc = metrics.get("category_accuracy", 0.0)
        load_std = metrics.get("load_balance_std", 0.0)
        tickets_triaged = metrics.get("tickets_triaged", 0)
        
        # Thresholds vary by difficulty
        thresholds = {
            1: {"priority": 0.9, "category": 0.85, "load": 1.5},  # Easy
            2: {"priority": 0.80, "category": 0.75, "load": 1.0},  # Medium
            3: {"priority": 0.70, "category": 0.65, "load": 0.5}   # Hard
        }
        
        thresh = thresholds.get(self.task_level, thresholds[1])
        
        # Component scores (each 0-1)
        priority_score = min(1.0, priority_acc / thresh["priority"])
        category_score = min(1.0, category_acc / thresh["category"])
        load_score = min(1.0, 1.0 - (load_std / thresh["load"]))
        throughput_score = min(1.0, tickets_triaged / max(1, self.task_level * 5))
        
        # Weighted average
        final_score = (
            priority_score * 0.35 +
            category_score * 0.35 +
            load_score * 0.20 +
            throughput_score * 0.10
        )
        
        return min(1.0, max(0.0, final_score))


if __name__ == "__main__":
    # Test environment
    print("🎫 Support Ticket Triage OpenEnv\n")
    
    for task_level in [1, 2, 3]:
        print(f"\n{'='*60}")
        print(f"Task Level {task_level}")
        print('='*60)
        
        env = SupportTriageEnv(task_level=task_level, max_steps=10)
        obs = env.reset()
        
        print(f"Initial queue: {obs.queue_size} tickets")
        print(f"First ticket: {obs.tickets[0].ticket_id}")
        
        # Sample action
        if obs.tickets:
            ticket = obs.tickets[0]
            action = TriageAction(
                ticket_id=ticket.ticket_id,
                priority=TicketPriority.HIGH,
                category=TicketCategory.TECHNICAL,
                assign_to_agent="agent_1"
            )
            
            obs, reward, done, info = env.step(action)
            print(f"Reward: {reward.value:.2f}")
            print(f"Metrics: {info.metrics}")
