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

from flask import Flask, jsonify, request
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


@app.route("/", methods=["GET"])
def index():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "Med-Triage OpenEnv",
        "timestamp": datetime.now().isoformat()
    }), 200


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


if __name__ == "__main__":
    print(f"\n{'='*80}")
    print("🏥 Med-Triage OpenEnv - Flask Server")
    print(f"{'='*80}")
    print(f"API Base: {API_BASE_URL}")
    print(f"Model: {MODEL_NAME}")
    print(f"Port: {PORT}")
    print(f"{'='*80}\n")
    
    app.run(host="0.0.0.0", port=PORT, debug=False)
