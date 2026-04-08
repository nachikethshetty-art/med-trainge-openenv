"""
Initialize demo episodes globally.
This module is imported first to ensure episodes are loaded.
"""

# Demo episodes for initial display
DEMO_EPISODES = [
    {"id": 1, "task_level": 1, "score": 0.9234, "steps": 12, "timestamp": "2026-04-08 10:23:45"},
    {"id": 2, "task_level": 1, "score": 0.8765, "steps": 15, "timestamp": "2026-04-08 10:24:02"},
    {"id": 3, "task_level": 1, "score": 0.8901, "steps": 13, "timestamp": "2026-04-08 10:24:18"},
    {"id": 4, "task_level": 2, "score": 0.7123, "steps": 8, "timestamp": "2026-04-08 10:24:35"},
    {"id": 5, "task_level": 2, "score": 0.6890, "steps": 9, "timestamp": "2026-04-08 10:24:52"},
    {"id": 6, "task_level": 3, "score": 0.5432, "steps": 11, "timestamp": "2026-04-08 10:25:09"},
]

print("[INIT_EPISODES] Demo episodes module loaded with {} episodes".format(len(DEMO_EPISODES)))
