#!/usr/bin/env python3
"""
🎫 SUPPORT TRIAGE OPENENV - INTERACTIVE TEST SCRIPT
Test the environment interactively like a frontend would
"""

from env import SupportTriageEnv, TriageAction
import json

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_observation(obs):
    """Display current observation"""
    print(f"📊 CURRENT STATE:")
    print(f"   Step: {obs.current_step}")
    print(f"   Queue Size: {obs.queue_size}")
    print(f"   Agent Workload: {obs.agent_workload}")
    print(f"   Metrics: {obs.metrics}")
    
    if obs.tickets:
        print(f"\n📋 TOP TICKETS IN QUEUE:")
        for i, ticket in enumerate(obs.tickets[:3], 1):
            print(f"\n   Ticket {i}: {ticket.ticket_id}")
            print(f"   Subject: {ticket.subject}")
            print(f"   Category: {ticket.category}")
            print(f"   Sentiment: {ticket.sentiment_score}")

def print_reward(reward):
    """Display reward breakdown"""
    print(f"\n💰 REWARD:")
    print(f"   Total: {reward.value:.2f}")
    print(f"   Components: {reward.components}")

def test_task_1():
    """Test Task 1: Easy"""
    print_header("TASK 1: EASY (5 tickets, LOW/MEDIUM priority)")
    
    env = SupportTriageEnv(task_level=1, seed=42)
    obs = env.reset()
    
    print_observation(obs)
    
    # Take first action
    if obs.tickets:
        ticket = obs.tickets[0]
        print(f"\n🎯 Taking Action on: {ticket.ticket_id}")
        
        action = TriageAction(
            ticket_id=ticket.ticket_id,
            priority="high",
            category="billing",
            assign_to_agent="agent_1",
            notes="Handling billing issue"
        )
        
        obs, reward, done, info = env.step(action)
        print_reward(reward)
        print(f"\n✅ Action executed successfully!")
        print(f"   Done: {done}")
        print(f"   Info: {json.dumps(info, indent=2)}")

def test_task_2():
    """Test Task 2: Medium"""
    print_header("TASK 2: MEDIUM (10 tickets, mixed priority)")
    
    env = SupportTriageEnv(task_level=2, seed=42)
    obs = env.reset()
    
    print_observation(obs)
    
    # Run 3 actions
    for step in range(3):
        if obs.tickets and not obs.done if hasattr(obs, 'done') else True:
            ticket = obs.tickets[0]
            print(f"\n🎯 Step {step+1}: Acting on {ticket.ticket_id}")
            
            action = TriageAction(
                ticket_id=ticket.ticket_id,
                priority="high",
                category="technical",
                assign_to_agent=f"agent_{(step % 3) + 1}",
                notes=f"Automated triage step {step+1}"
            )
            
            obs, reward, done, info = env.step(action)
            print(f"   Reward: {reward.value:.2f}")
            print(f"   Queue remaining: {obs.queue_size}")

def test_task_3():
    """Test Task 3: Hard"""
    print_header("TASK 3: HARD (15 tickets, CRITICAL priority)")
    
    env = SupportTriageEnv(task_level=3, seed=42)
    obs = env.reset()
    
    print_observation(obs)
    
    # Run 5 actions
    total_reward = 0
    for step in range(5):
        if obs.tickets:
            ticket = obs.tickets[0]
            print(f"\n🎯 Step {step+1}: Acting on {ticket.ticket_id}")
            
            action = TriageAction(
                ticket_id=ticket.ticket_id,
                priority="critical",
                category="bug_report",
                assign_to_agent=f"agent_{(step % 3) + 1}",
                notes=f"Critical issue handling step {step+1}"
            )
            
            obs, reward, done, info = env.step(action)
            total_reward += reward.value
            print(f"   Reward: {reward.value:.2f}")
            print(f"   Cumulative: {total_reward:.2f}")
            print(f"   Queue remaining: {obs.queue_size}")

def test_full_episode():
    """Run a complete episode"""
    print_header("FULL EPISODE: Complete Task 2 from start to finish")
    
    env = SupportTriageEnv(task_level=2, seed=123)
    obs = env.reset()
    
    total_reward = 0
    step_count = 0
    
    print(f"📊 Starting Episode with {obs.queue_size} tickets\n")
    
    while obs.queue_size > 0 and step_count < 20:
        step_count += 1
        ticket = obs.tickets[0]
        
        # Simple strategy: assign to agent with least workload
        agent_with_min_load = min(
            obs.agent_workload.items(), 
            key=lambda x: x[1]
        )[0]
        
        action = TriageAction(
            ticket_id=ticket.ticket_id,
            priority="high" if ticket.priority == "critical" else "medium",
            category=ticket.category.value.lower(),
            assign_to_agent=agent_with_min_load,
            notes="Strategic assignment for load balancing"
        )
        
        obs, reward, done, info = env.step(action)
        total_reward += reward.value
        
        print(f"Step {step_count}: {ticket.ticket_id} → {agent_with_min_load} | "
              f"Reward: {reward.value:+.2f} | Queue: {obs.queue_size}")
    
    print(f"\n🏁 EPISODE COMPLETE!")
    print(f"   Total Steps: {step_count}")
    print(f"   Total Reward: {total_reward:.2f}")
    print(f"   Average per step: {total_reward/step_count:.2f}")
    
    # Grade the episode
    from env import TaskGrader
    grader = TaskGrader(env.task_level)
    score = grader.grade(env, total_reward, obs.metrics)
    print(f"   Final Score: {score:.2f}/1.0")

def interactive_mode():
    """Interactive mode to manually test environment"""
    print_header("INTERACTIVE MODE - Manual Testing")
    
    task_level = int(input("Enter task level (1-3): "))
    env = SupportTriageEnv(task_level=task_level)
    obs = env.reset()
    
    print_observation(obs)
    
    step = 0
    while obs.queue_size > 0 and step < 50:
        step += 1
        print(f"\n--- STEP {step} ---")
        print(f"Queue size: {obs.queue_size}")
        
        if obs.tickets:
            ticket = obs.tickets[0]
            print(f"\nCurrent ticket: {ticket.ticket_id}")
            print(f"Subject: {ticket.subject[:50]}...")
            
            # Get action from user
            try:
                print("\nChoose action:")
                priority = input("Priority (LOW/MEDIUM/HIGH/CRITICAL): ").upper()
                category = input("Category (BILLING/TECHNICAL/ACCOUNT/FEATURE_REQUEST/BUG_REPORT): ").upper()
                agent = input("Assign to agent (agent_1/agent_2/agent_3): ")
                
                action = TriageAction(
                    ticket_id=ticket.ticket_id,
                    priority=priority,
                    category=category,
                    assign_to_agent=agent,
                    notes="Manual test action"
                )
                
                obs, reward, done, info = env.step(action)
                print_reward(reward)
                
                continue_prompt = input("\nContinue? (y/n): ")
                if continue_prompt.lower() != 'y':
                    break
                    
            except Exception as e:
                print(f"Error: {e}")
                break

def main():
    """Main menu"""
    print("\n" + "="*60)
    print("  🎫 SUPPORT TRIAGE OPENENV - TEST SUITE")
    print("="*60)
    print("\nChoose a test:")
    print("1. Task 1 (Easy) - Quick test")
    print("2. Task 2 (Medium) - Standard test")
    print("3. Task 3 (Hard) - Challenging test")
    print("4. Full Episode - Complete run-through")
    print("5. Interactive Mode - Manual testing")
    print("6. All Tests - Run everything")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice == "1":
        test_task_1()
    elif choice == "2":
        test_task_2()
    elif choice == "3":
        test_task_3()
    elif choice == "4":
        test_full_episode()
    elif choice == "5":
        interactive_mode()
    elif choice == "6":
        test_task_1()
        test_task_2()
        test_task_3()
        test_full_episode()
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
