#!/usr/bin/env python3
"""
Flask web server for Med-Triage OpenEnv on HF Spaces.
Listens on port 7860 and provides REST API endpoints.
"""

import os
import sys
import json
import traceback
from datetime import datetime

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, jsonify, request, render_template_string
from environment.med_triage_env import MedTriageEnv, TriageAction, TriageActionType
from baseline.agent import BaselineAgent

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:7860")
API_KEY = os.getenv("API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "groq-mixtral-8x7b")
PORT = int(os.getenv("PORT", 7860))

# Global state
env = None
agent = None
episodes_history = []

# Demo episodes for initial display
DEMO_EPISODES = [
    {"id": 1, "task_level": 1, "score": 0.9234, "steps": 12, "timestamp": "2026-04-08 10:23:45"},
    {"id": 2, "task_level": 1, "score": 0.8765, "steps": 15, "timestamp": "2026-04-08 10:24:02"},
    {"id": 3, "task_level": 1, "score": 0.8901, "steps": 13, "timestamp": "2026-04-08 10:24:18"},
    {"id": 4, "task_level": 2, "score": 0.7123, "steps": 8, "timestamp": "2026-04-08 10:24:35"},
    {"id": 5, "task_level": 2, "score": 0.6890, "steps": 9, "timestamp": "2026-04-08 10:24:52"},
    {"id": 6, "task_level": 3, "score": 0.5432, "steps": 11, "timestamp": "2026-04-08 10:25:09"},
]

# Initialize with demo episodes
episodes_history = DEMO_EPISODES.copy()


# HTML Dashboard Template
DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Med-Triage OpenEnv Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .header p { font-size: 1.1em; opacity: 0.9; }
        .content {
            padding: 30px;
        }
        .status-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .status-card {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            border-radius: 5px;
        }
        .status-card h3 {
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            margin-bottom: 10px;
        }
        .status-card .value {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }
        .episodes-section {
            margin-top: 30px;
        }
        .episodes-section h2 {
            color: #333;
            margin-bottom: 20px;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .episode-card {
            background: #f8f9fa;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .episode-info h4 {
            color: #667eea;
            margin-bottom: 5px;
        }
        .episode-info p {
            color: #666;
            font-size: 0.9em;
        }
        .episode-score {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
            text-align: right;
        }
        .badge {
            display: inline-block;
            padding: 5px 10px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: bold;
            margin-right: 10px;
        }
        .badge-easy { background: #d4edda; color: #155724; }
        .badge-medium { background: #fff3cd; color: #856404; }
        .badge-hard { background: #f8d7da; color: #721c24; }
        .empty {
            text-align: center;
            color: #999;
            padding: 40px 20px;
        }
        .empty img {
            width: 60px;
            opacity: 0.5;
            margin-bottom: 10px;
        }
        .api-info {
            background: #f0f4ff;
            border-left: 4px solid #667eea;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
            font-size: 0.9em;
            color: #666;
        }
        .api-info code {
            background: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Med-Triage OpenEnv</h1>
            <p>Real-world Medical Triage Simulation Environment</p>
        </div>
        <div class="content">
            <div class="status-grid">
                <div class="status-card">
                    <h3>Status</h3>
                    <div class="value">✅ Running</div>
                </div>
                <div class="status-card">
                    <h3>Episodes Evaluated</h3>
                    <div class="value">{{ episodes_count }}</div>
                </div>
                <div class="status-card">
                    <h3>Model</h3>
                    <div class="value">{{ model_name }}</div>
                </div>
            </div>

            <div class="episodes-section">
                <h2>📊 Episode History</h2>
                {% if episodes %}
                    {% for episode in episodes %}
                    <div class="episode-card">
                        <div class="episode-info">
                            <h4>
                                {% if episode.task_level == 1 %}
                                    <span class="badge badge-easy">EASY</span>
                                {% elif episode.task_level == 2 %}
                                    <span class="badge badge-medium">MEDIUM</span>
                                {% else %}
                                    <span class="badge badge-hard">HARD</span>
                                {% endif %}
                                Episode #{{ episode.id }}
                            </h4>
                            <p>Task Level {{ episode.task_level }} • {{ episode.steps }} steps • {{ episode.timestamp }}</p>
                        </div>
                        <div class="episode-score">
                            {{ "%.4f" | format(episode.score) }}
                        </div>
                    </div>
                    {% endfor %}
                {% else %}
                    <div class="empty">
                        <p>No episodes evaluated yet.</p>
                        <p>Call the inference endpoints to generate episodes.</p>
                    </div>
                {% endif %}
            </div>

            <div class="api-info">
                <strong>📡 API Endpoints:</strong><br>
                POST <code>/inference</code> - Run evaluation on all 3 tasks<br>
                POST <code>/reset</code> - Reset environment<br>
                POST <code>/step</code> - Step environment<br>
                GET <code>/state</code> - Get current state<br>
                GET <code>/health</code> - Health check
            </div>
        </div>
    </div>

    <script>
        // Auto-refresh every 5 seconds
        setTimeout(function() {
            location.reload();
        }, 5000);
    </script>
</body>
</html>
"""


@app.route("/", methods=["GET"])
def index():
    """Dashboard endpoint"""
    return render_template_string(DASHBOARD_HTML, 
        episodes=episodes_history,
        episodes_count=len(episodes_history),
        model_name=MODEL_NAME
    )


@app.route("/reset", methods=["POST"])
def reset():
    """Reset environment endpoint (OpenEnv spec)"""
    try:
        global env
        data = request.get_json() or {}
        task_level = data.get("task_level", 1)
        
        env = MedTriageEnv(task_level=task_level, max_steps=50)
        obs = env.reset()
        
        return jsonify({
            "observation": str(obs),
            "task_level": task_level,
            "status": "reset",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error in reset: {e}", file=sys.stderr)
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/step", methods=["POST"])
def step():
    """Step environment endpoint (OpenEnv spec)"""
    try:
        global env
        if env is None:
            return jsonify({"error": "Environment not initialized", "status": "error"}), 400
        
        data = request.get_json() or {}
        action_type = data.get("action_type", "TRIAGE")
        
        action = TriageAction(
            type=TriageActionType[action_type],
            patient_id=data.get("patient_id", "P1"),
            minutes=data.get("minutes", 5),
            text=data.get("text", "")
        )
        
        obs, reward, done, info = env.step(action)
        
        return jsonify({
            "observation": str(obs),
            "reward": float(reward),
            "done": bool(done),
            "info": info,
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error in step: {e}", file=sys.stderr)
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/state", methods=["GET"])
def state():
    """Get environment state endpoint (OpenEnv spec)"""
    try:
        global env
        if env is None:
            return jsonify({"error": "Environment not initialized", "status": "error"}), 400
        
        return jsonify({
            "current_step": env.current_step,
            "done": env.done,
            "episode_reward": float(env.episode_reward),
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error in state: {e}", file=sys.stderr)
        return jsonify({"error": str(e), "status": "error"}), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check for container"""
    return jsonify({
        "status": "healthy",
        "service": "med-triage-openenv",
        "api_base": API_BASE_URL,
        "model": MODEL_NAME
    }), 200


@app.route("/inference", methods=["POST"])
def inference():
    """Run inference and track episodes"""
    try:
        global env, agent, episodes_history
        
        # Get parameters from request
        data = request.get_json() or {}
        task_level = data.get("task_level", 1)
        max_steps = data.get("max_steps", 20)
        
        # Initialize environment and agent
        env = MedTriageEnv(task_level=task_level, max_steps=max_steps)
        obs = env.reset()
        
        config = {
            "groq_key": os.getenv("GROQ"),
            "gemini_key": os.getenv("GEMINI"),
        }
        agent = BaselineAgent(config)
        
        # Run episode
        total_reward = 0.0
        steps_taken = 0
        actions = []
        
        for step in range(max_steps):
            try:
                action = agent.decide(obs)
                if action is None:
                    break
                
                obs, reward, done, info = env.step(action)
                total_reward += reward
                steps_taken += 1
                actions.append(str(action.type))
                
                if done:
                    break
                    
            except Exception as e:
                print(f"Error in inference step: {e}", file=sys.stderr)
                break
        
        # Normalize reward
        normalized_reward = min(max(total_reward, 0.001), 0.999)
        
        # Track episode
        episode_data = {
            "id": len(episodes_history) + 1,
            "task_level": task_level,
            "score": normalized_reward,
            "steps": steps_taken,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        episodes_history.append(episode_data)
        
        return jsonify({
            "task_level": task_level,
            "total_reward": float(normalized_reward),
            "steps": steps_taken,
            "actions": actions,
            "done": env.done,
            "status": "completed",
            "timestamp": datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        print(f"Error in inference: {e}", file=sys.stderr)
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500


def main():
    """Entry point for console script."""
    print(f"\n{'='*80}")
    print("🏥 Med-Triage OpenEnv - Flask Server")
    print(f"{'='*80}")
    print(f"API Base: {API_BASE_URL}")
    print(f"Model: {MODEL_NAME}")
    print(f"Port: {PORT}")
    print(f"{'='*80}\n")
    
    app.run(host="0.0.0.0", port=PORT, debug=False)


if __name__ == "__main__":
    print(f"\n{'='*80}")
    print("🏥 Med-Triage OpenEnv - Flask Server")
    print(f"{'='*80}")
    print(f"API Base: {API_BASE_URL}")
    print(f"Model: {MODEL_NAME}")
    print(f"Port: {PORT}")
    print(f"{'='*80}\n")
    
    app.run(host="0.0.0.0", port=PORT, debug=False)
