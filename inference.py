#!/usr/bin/env python3
"""
Inference script for Support Ticket Triage OpenEnv
Uses OpenAI API for ticket triaging decisions
"""

import os
import sys
import json
import time
from typing import Dict, Any
from env import (
    SupportTriageEnv, TriageAction, TicketPriority, TicketCategory,
    TaskGrader, Observation, Reward
)

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai package not installed. Install with: pip install openai")
    sys.exit(1)


def parse_env_vars() -> Dict[str, str]:
    """Parse and validate environment variables"""
    config = {
        "api_key": os.getenv("OPENAI_API_KEY"),
        "api_base": os.getenv("API_BASE_URL", "https://api.openai.com/v1"),
        "model": os.getenv("MODEL_NAME", "gpt-4"),
        "hf_token": os.getenv("HF_TOKEN")
    }
    
    if not config["api_key"]:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    return config


class TicketTriageAgent:
    """LLM-based ticket triage agent"""
    
    def __init__(self, config: Dict[str, str]):
        self.client = OpenAI(
            api_key=config["api_key"],
            base_url=config.get("api_base")
        )
        self.model = config["model"]
        self.conversation_history = []
    
    def get_triage_decision(self, ticket_dict: Dict, agent_workload: Dict) -> TriageAction:
        """Get triaging decision from LLM"""
        
        prompt = f"""You are an expert customer support manager. Analyze this ticket and provide triaging decisions.

Ticket ID: {ticket_dict['ticket_id']}
Subject: {ticket_dict['subject']}
Description: {ticket_dict['description']}
Sentiment Score: {ticket_dict['sentiment_score']:.2f} (-1=very negative, 1=very positive)
Customer ID: {ticket_dict['customer_id']}

Current agent workload:
{json.dumps(agent_workload, indent=2)}

Available priorities: LOW, MEDIUM, HIGH, CRITICAL
Available categories: BILLING, TECHNICAL, ACCOUNT, FEATURE_REQUEST, BUG_REPORT

Respond with JSON in this exact format:
{{
    "priority": "MEDIUM",
    "category": "TECHNICAL",
    "assign_to_agent": "agent_1",
    "confidence": 0.85,
    "reasoning": "Brief explanation of decision"
}}"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a customer support triaging expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON response
            decision = json.loads(response_text)
            
            action = TriageAction(
                ticket_id=ticket_dict['ticket_id'],
                priority=TicketPriority(decision.get("priority", "MEDIUM").lower()),
                category=TicketCategory(decision.get("category", "TECHNICAL").lower()),
                assign_to_agent=decision.get("assign_to_agent", "agent_1"),
                notes=decision.get("reasoning", "")
            )
            
            return action
        
        except json.JSONDecodeError as e:
            print(f"Warning: JSON parsing failed: {e}. Using default action.", file=sys.stderr)
            return TriageAction(
                ticket_id=ticket_dict['ticket_id'],
                priority=TicketPriority.MEDIUM,
                category=TicketCategory.TECHNICAL,
                assign_to_agent="agent_1"
            )
        except Exception as e:
            print(f"Error in LLM call: {e}", file=sys.stderr)
            raise


def run_episode(env: SupportTriageEnv, agent: TicketTriageAgent, task_level: int) -> Dict[str, Any]:
    """Run single episode"""
    
    print(f"[START] task_level={task_level}, timestamp={time.time()}")
    
    obs = env.reset()
    done = False
    step = 0
    total_reward = 0.0
    step_data = []
    
    while not done and step < env.max_steps:
        if not obs.tickets:
            break
        
        # Get first ticket from queue
        ticket = obs.tickets[0]
        ticket_dict = ticket.model_dump()
        
        try:
            # Get triage decision
            action = agent.get_triage_decision(ticket_dict, obs.agent_workload)
            
            # Execute action
            obs, reward, done, info = env.step(action)
            
            total_reward += reward.value
            step += 1
            
            # Log step in [STEP] format
            step_record = {
                "action": {
                    "ticket_id": action.ticket_id,
                    "priority": action.priority.value,
                    "category": action.category.value,
                    "assign_to_agent": action.assign_to_agent
                },
                "reward": reward.value,
                "reward_components": reward.components,
                "obs": {
                    "queue_size": obs.queue_size,
                    "agent_workload": obs.agent_workload,
                    "metrics": obs.metrics
                },
                "info": info.model_dump()
            }
            
            print(f"[STEP] {json.dumps(step_record)}")
            step_data.append(step_record)
        
        except Exception as e:
            print(f"Error during step: {e}", file=sys.stderr)
            break
    
    # Grade performance
    grader = TaskGrader(task_level)
    score = grader.grade(env, total_reward, info.metrics)
    
    # Final result
    result = {
        "task_level": task_level,
        "total_reward": total_reward,
        "steps": step,
        "success": info.success,
        "score": score,
        "metrics": info.metrics,
        "model": agent.model
    }
    
    print(f"[END] {json.dumps(result)}")
    
    return result


def main():
    """Main inference runner"""
    
    # Parse config
    try:
        config = parse_env_vars()
    except ValueError as e:
        print(f"Configuration error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Initialize agent
    agent = TicketTriageAgent(config)
    
    # Run all task levels
    all_results = []
    
    for task_level in [1, 2, 3]:
        print(f"\n{'='*70}")
        print(f"Running Task Level {task_level} ({['Easy', 'Medium', 'Hard'][task_level-1]})")
        print('='*70 + "\n")
        
        try:
            env = SupportTriageEnv(task_level=task_level, max_steps=50)
            result = run_episode(env, agent, task_level)
            all_results.append(result)
            
            print(f"\n✅ Task {task_level} completed")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Total Reward: {result['total_reward']:.2f}")
            print(f"   Steps: {result['steps']}")
        
        except Exception as e:
            print(f"\n❌ Task {task_level} failed: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    
    for result in all_results:
        print(f"Task {result['task_level']}: Score={result['score']:.4f}, Reward={result['total_reward']:.2f}")
    
    avg_score = sum(r['score'] for r in all_results) / len(all_results)
    print(f"\nAverage Score: {avg_score:.4f}")
    
    return all_results


if __name__ == "__main__":
    results = main()
    sys.exit(0 if all(r['success'] for r in results) else 1)
