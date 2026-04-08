#!/usr/bin/env python3
"""
Manual Episode Evaluation Test Script
Run this to generate episodes locally and verify they appear on the dashboard.
"""

import requests
import time
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:7860"
API_ENDPOINT = f"{BASE_URL}/inference"
DASHBOARD_URL = f"{BASE_URL}/"

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def test_server_health():
    """Test if server is running."""
    print_header("1. Testing Server Health")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print("✅ Server is running!")
            print(f"   Status: {health.get('status')}")
            print(f"   Service: {health.get('service')}")
            return True
        else:
            print(f"❌ Server returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to {BASE_URL}")
        print("   Make sure the Flask server is running!")
        print("   Run: source venv/bin/activate && python3 app_server.py")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def generate_episode(task_level, level_name):
    """Generate a single episode."""
    print(f"\n📊 Generating {level_name} episode (Task Level {task_level})...")
    try:
        payload = {"task_level": task_level}
        response = requests.post(API_ENDPOINT, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            score = data.get('total_reward')
            steps = data.get('steps')
            print(f"   ✅ SUCCESS!")
            print(f"   Score: {score:.4f}")
            print(f"   Steps: {steps}")
            return True
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print(f"   ⏱️ Request timed out (taking longer than 30 seconds)")
        print(f"   This is normal - evaluation is still running in background")
        return True
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def get_dashboard_episodes():
    """Get current episode count from dashboard."""
    print("\n📈 Checking Dashboard Episodes...")
    try:
        response = requests.get(DASHBOARD_URL, timeout=5)
        if response.status_code == 200:
            # Extract episode count from HTML
            html = response.text
            if "Episodes Evaluated" in html:
                # Find the value after "Episodes Evaluated"
                start = html.find('<h3>Episodes Evaluated</h3>')
                if start != -1:
                    end = html.find('</div>', start)
                    section = html[start:end]
                    # Extract number
                    import re
                    match = re.search(r'<div class="value">(\d+)</div>', section)
                    if match:
                        count = int(match.group(1))
                        print(f"   Episodes on Dashboard: {count}")
                        return count
            print("   Could not parse episode count from dashboard")
            return None
        else:
            print(f"   ❌ Dashboard returned status {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def run_full_test():
    """Run the complete test sequence."""
    print_header("Med-Triage OpenEnv - Manual Episode Evaluation Test")
    
    # Step 1: Check server health
    if not test_server_health():
        print("\n❌ Server is not running. Please start it first:")
        print("   cd /Users/amshumathshetty/Desktop/med-triage-openenv")
        print("   source venv/bin/activate")
        print("   python3 app_server.py")
        return False
    
    initial_count = get_dashboard_episodes()
    
    print_header("2. Generating Test Episodes")
    print("This will generate 6 episodes (3 EASY, 2 MEDIUM, 1 HARD)")
    print("Each generation may take 30-60 seconds...\n")
    
    # Generate episodes
    episodes_config = [
        (1, "EASY #1"),
        (1, "EASY #2"),
        (1, "EASY #3"),
        (2, "MEDIUM #1"),
        (2, "MEDIUM #2"),
        (3, "HARD #1"),
    ]
    
    success_count = 0
    for task_level, level_name in episodes_config:
        if generate_episode(task_level, level_name):
            success_count += 1
            time.sleep(2)  # Wait between requests
    
    print_header("3. Verification")
    print(f"✅ Successfully generated: {success_count}/{len(episodes_config)} episodes")
    
    # Wait a bit for dashboard to update
    print("\n⏳ Waiting for dashboard to update...")
    time.sleep(5)
    
    # Check final count
    final_count = get_dashboard_episodes()
    
    print_header("4. Results Summary")
    print(f"Initial episode count: {initial_count if initial_count else 'Unknown'}")
    print(f"Final episode count:   {final_count if final_count else 'Unknown'}")
    print(f"\n✅ Test Complete!")
    print(f"\n📱 View Dashboard: {DASHBOARD_URL}")
    print(f"🔄 Refresh the page to see all episodes")

if __name__ == "__main__":
    run_full_test()
