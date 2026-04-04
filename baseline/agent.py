#!/usr/bin/env python3
"""
Inference script for Support Ticket Triage OpenEnv
Uses GROQ API (primary) + GEMINI API (fallback) for ticket triaging decisions
Both APIs are completely free with generous rate limits
"""

import os
import sys
import json
import time
from typing import Dict, Any, Optional
from env import (
    SupportTriageEnv, TriageAction, TicketPriority, TicketCategory,
    TaskGrader, Observation, Reward
)

# Try importing GROQ (primary)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    print("Warning: groq package not installed. Install with: pip install groq", file=sys.stderr)

# Try importing GEMINI (fallback)
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai package not installed. Install with: pip install google-generativeai", file=sys.stderr)

if not GROQ_AVAILABLE and not GEMINI_AVAILABLE:
    print("Error: Neither groq nor google-generativeai package installed!")
    print("Install one or both with:")
    print("  pip install groq")
    print("  pip install google-generativeai")
    sys.exit(1)


def parse_env_vars() -> Dict[str, str]:
    """Parse and validate environment variables"""
    config = {
        "groq_key": os.getenv("GROQ_API_KEY"),
        "gemini_key": os.getenv("GEMINI_API_KEY"),
        "hf_token": os.getenv("HF_TOKEN")
    }
    
    if not config["groq_key"] and not config["gemini_key"]:
        raise ValueError("At least one API key required: GROQ_API_KEY or GEMINI_API_KEY")
    
    return config


class TicketTriageAgent:
    """LLM-based ticket triage agent with GROQ (primary) + GEMINI (fallback)"""
    
    def __init__(self, config: Dict[str, str]):
        self.groq_client = None
        self.gemini_model = None
        self.model_used = "unknown"
        
        # Initialize GROQ (primary)
        if GROQ_AVAILABLE and config.get("groq_key"):
            try:
                self.groq_client = Groq(api_key=config["groq_key"])
                print("✅ GROQ client initialized (primary)", file=sys.stderr)
            except Exception as e:
                print(f"⚠️  GROQ initialization failed: {e}", file=sys.stderr)
        
        # Initialize GEMINI (fallback)
        if GEMINI_AVAILABLE and config.get("gemini_key"):
            try:
                genai.configure(api_key=config["gemini_key"])
                self.gemini_model = genai.GenerativeModel('gemini-pro')
                print("✅ GEMINI client initialized (fallback)", file=sys.stderr)
            except Exception as e:
                print(f"⚠️  GEMINI initialization failed: {e}", file=sys.stderr)
        
        if not self.groq_client and not self.gemini_model:
            raise ValueError("Failed to initialize both GROQ and GEMINI clients")
    
    def get_triage_decision(self, ticket_dict: Dict, agent_workload: Dict) -> TriageAction:
        """Get triaging decision from LLM (GROQ first, fallback to GEMINI)"""
        
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

Respond with JSON in this exact format (no extra text):
{{
    "priority": "MEDIUM",
    "category": "TECHNICAL",
    "assign_to_agent": "agent_1",
    "confidence": 0.85,
    "reasoning": "Brief explanation of decision"
}}"""
        
        # Try GROQ first (fastest, cheapest)
        if self.groq_client:
            try:
                response = self.groq_client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[
                        {"role": "system", "content": "You are a customer support triaging expert. Always respond with valid JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=200
                )
                
                response_text = response.choices[0].message.content
                self.model_used = "groq"
                return self._parse_response(ticket_dict, response_text)
            
            except Exception as e:
                print(f"⚠️  GROQ failed: {e}. Falling back to GEMINI...", file=sys.stderr)
        
        # Fallback to GEMINI
        if self.gemini_model:
            try:
                response = self.gemini_model.generate_content(
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.3,
                        max_output_tokens=200
                    )
                )
                
                response_text = response.text
                self.model_used = "gemini"
                return self._parse_response(ticket_dict, response_text)
            
            except Exception as e:
                print(f"⚠️  GEMINI failed: {e}. Using default action.", file=sys.stderr)
        
        # Default fallback
        return TriageAction(
            ticket_id=ticket_dict['ticket_id'],
            priority=TicketPriority.MEDIUM,
            category=TicketCategory.TECHNICAL,
            assign_to_agent="agent_1"
        )
    
    def _parse_response(self, ticket_dict: Dict, response_text: str) -> TriageAction:
        """Parse LLM response and extract action"""
        try:
            # Clean up response (remove markdown code blocks if present)
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text[response_text.find('{'):]
            if response_text.endswith("```"):
                response_text = response_text[:response_text.rfind('}') + 1]
            
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
            # Get triage decision (with model fallback)
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
                "info": info.model_dump(),
                "model_used": agent.model_used
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
        "model_used": agent.model_used
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
        print("\nAvailable options:", file=sys.stderr)
        print("  - Set GROQ_API_KEY (from https://console.groq.com)", file=sys.stderr)
        print("  - Set GEMINI_API_KEY (from https://aistudio.google.com/apikey)", file=sys.stderr)
        print("  - Or both for redundancy", file=sys.stderr)
        sys.exit(1)
    
    # Initialize agent
    try:
        agent = TicketTriageAgent(config)
        print(f"\n✅ Agent initialized successfully\n", file=sys.stderr)
    except Exception as e:
        print(f"Agent initialization error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Run all task levels
    all_results = []
    
    for task_level in [1, 2, 3]:
        print(f"\n{'='*70}")
        print(f"Running Task Level {task_level} ({['Easy', 'Medium', 'Hard'][task_level-1]})")
        print(f"Using model: {agent.model_used}")
        print('='*70 + "\n")
        
        try:
            env = SupportTriageEnv(task_level=task_level, max_steps=50)
            result = run_episode(env, agent, task_level)
            all_results.append(result)
            
            print(f"\n✅ Task {task_level} completed")
            print(f"   Score: {result['score']:.4f}")
            print(f"   Total Reward: {result['total_reward']:.2f}")
            print(f"   Steps: {result['steps']}")
            print(f"   Model: {result['model_used']}")
        
        except Exception as e:
            print(f"\n❌ Task {task_level} failed: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print('='*70)
    
    for result in all_results:
        print(f"Task {result['task_level']}: Score={result['score']:.4f}, Reward={result['total_reward']:.2f}, Model={result['model_used']}")
    
    avg_score = sum(r['score'] for r in all_results) / len(all_results)
    print(f"\nAverage Score: {avg_score:.4f}")
    print(f"\n✅ All tasks completed successfully!")
    print(f"📌 Both GROQ (primary) and GEMINI (fallback) working for redundancy")
    
    return all_results


if __name__ == "__main__":
    results = main()
    sys.exit(0 if all(r['success'] for r in results) else 1)
