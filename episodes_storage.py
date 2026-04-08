"""
Persistent episodes storage using JSON file.
Episodes are saved to disk and loaded on startup.
"""

import json
import os
from datetime import datetime

EPISODES_FILE = "/tmp/episodes_history.json"

# Demo episodes for initial display
DEMO_EPISODES = [
    {"id": 1, "task_level": 1, "score": 0.9234, "steps": 12, "timestamp": "2026-04-08 10:23:45"},
    {"id": 2, "task_level": 1, "score": 0.8765, "steps": 15, "timestamp": "2026-04-08 10:24:02"},
    {"id": 3, "task_level": 1, "score": 0.8901, "steps": 13, "timestamp": "2026-04-08 10:24:18"},
    {"id": 4, "task_level": 2, "score": 0.7123, "steps": 8, "timestamp": "2026-04-08 10:24:35"},
    {"id": 5, "task_level": 2, "score": 0.6890, "steps": 9, "timestamp": "2026-04-08 10:24:52"},
    {"id": 6, "task_level": 3, "score": 0.5432, "steps": 11, "timestamp": "2026-04-08 10:25:09"},
]


def load_episodes():
    """Load episodes from JSON file or return demo episodes if file doesn't exist."""
    try:
        if os.path.exists(EPISODES_FILE):
            with open(EPISODES_FILE, 'r') as f:
                episodes = json.load(f)
                print(f"[EPISODES] Loaded {len(episodes)} episodes from {EPISODES_FILE}")
                return episodes
    except Exception as e:
        print(f"[EPISODES] Error loading from file: {e}")
    
    # Return demo episodes if file doesn't exist or error occurred
    print(f"[EPISODES] Using demo episodes ({len(DEMO_EPISODES)} episodes)")
    save_episodes(DEMO_EPISODES)
    return DEMO_EPISODES.copy()


def save_episodes(episodes):
    """Save episodes to JSON file."""
    try:
        os.makedirs(os.path.dirname(EPISODES_FILE), exist_ok=True)
        with open(EPISODES_FILE, 'w') as f:
            json.dump(episodes, f, indent=2)
        print(f"[EPISODES] Saved {len(episodes)} episodes to {EPISODES_FILE}")
    except Exception as e:
        print(f"[EPISODES] Error saving to file: {e}")


def add_episode(task_level, score, steps):
    """Add a new episode and save to file."""
    episodes = load_episodes()
    episode_id = max([e.get('id', 0) for e in episodes]) + 1 if episodes else 1
    new_episode = {
        "id": episode_id,
        "task_level": task_level,
        "score": score,
        "steps": steps,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    episodes.append(new_episode)
    save_episodes(episodes)
    print(f"[EPISODES] Added episode {episode_id} with score {score}")
    return episodes
