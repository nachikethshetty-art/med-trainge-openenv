#!/usr/bin/env python3
"""
Generate episodes via API endpoint to display on dashboard
"""
import requests
import time
import json

API_URL = "http://localhost:7860/inference"

print("\n" + "="*80)
print("🏥 Generating Episodes for Dashboard")
print("="*80 + "\n")

# Configuration
tasks = [
    {"level": 1, "name": "EASY", "count": 3},
    {"level": 2, "name": "MEDIUM", "count": 2},
    {"level": 3, "name": "HARD", "count": 1},
]

all_episodes = []

for task in tasks:
    print(f"\n📊 {task['name']} (Level {task['level']})")
    print("-" * 50)
    
    for i in range(task['count']):
        print(f"  Generating episode {i+1}/{task['count']}...", end=" ", flush=True)
        
        try:
            response = requests.post(
                API_URL,
                json={"task_level": task['level'], "max_steps": 20},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                score = data.get("total_reward", 0)
                all_episodes.append({
                    "level": task['level'],
                    "score": score
                })
                print(f"✅ Score: {score:.4f}")
            else:
                print(f"❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")
        
        time.sleep(0.5)

# Summary
print("\n" + "="*80)
print("📈 Summary")
print("="*80)
print(f"Total Episodes: {len(all_episodes)}")
if all_episodes:
    scores = [e['score'] for e in all_episodes]
    print(f"Average Score: {sum(scores)/len(scores):.4f}")
    print(f"Best Score: {max(scores):.4f}")
    print(f"Worst Score: {min(scores):.4f}")

print("\n✅ All episodes generated!")
print("🌐 Dashboard: http://localhost:7860")
print("="*80 + "\n")
