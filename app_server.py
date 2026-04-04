#!/usr/bin/env python3
"""
Flask web server for Med-Triage OpenEnv on HF Spaces.
Listens on port 7860 and provides interactive web UI for testing.
"""

import os
import sys
import json
import traceback

# Add current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template_string, jsonify, request
from environment.med_triage_env import MedTriageEnv
from baseline.agent import BaselineAgent

# Initialize Flask app
app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False

# Initialize environment and agent
env = None
agent = None
last_episode_result = None

def init_app():
    """Initialize environment and agent."""
    global env, agent
    try:
        env = MedTriageEnv(task_level=1)
        
        # Get API keys from environment
        # HF Spaces doesn't allow underscores in secret names, so we accept both formats
        config = {
            "groq_key": os.getenv("GROQ") or os.getenv("GROQ_API_KEY"),
            "gemini_key": os.getenv("GEMINI") or os.getenv("GEMINI_API_KEY"),
        }
        agent = BaselineAgent()
        print("✓ Environment and agent initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Error initializing: {e}")
        traceback.print_exc()
        return False

# HTML Template for web UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🏥 Med-Triage OpenEnv</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 800px;
            width: 100%;
            padding: 40px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 40px;
        }
        
        .header h1 {
            font-size: 32px;
            margin-bottom: 10px;
            color: #333;
        }
        
        .header p {
            color: #666;
            font-size: 16px;
        }
        
        .status-box {
            background: #f5f5f5;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #667eea;
        }
        
        .status-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin: 10px 0;
            font-size: 14px;
        }
        
        .status-label {
            font-weight: 600;
            color: #333;
        }
        
        .status-value {
            color: #666;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .badge-active {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-inactive {
            background: #f8d7da;
            color: #721c24;
        }
        
        .badge-info {
            background: #d1ecf1;
            color: #0c5460;
        }
        
        .tasks {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        
        .task-btn {
            padding: 15px 20px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .task-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
        }
        
        .task-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        .task-easy {
            background: #d4edda;
            color: #155724;
        }
        
        .task-easy:hover:not(:disabled) {
            background: #c3e6cb;
        }
        
        .task-medium {
            background: #fff3cd;
            color: #856404;
        }
        
        .task-medium:hover:not(:disabled) {
            background: #ffeaa7;
        }
        
        .task-hard {
            background: #f8d7da;
            color: #721c24;
        }
        
        .task-hard:hover:not(:disabled) {
            background: #f5c6cb;
        }
        
        .results {
            background: #f9f9f9;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            max-height: 400px;
            overflow-y: auto;
            display: none;
        }
        
        .results.visible {
            display: block;
        }
        
        .result-item {
            background: white;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 6px;
            border-left: 4px solid #667eea;
        }
        
        .result-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }
        
        .result-value {
            color: #666;
            font-size: 14px;
            line-height: 1.5;
        }
        
        .score {
            font-size: 24px;
            font-weight: bold;
            color: #667eea;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        .loading.visible {
            display: block;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-top: 20px;
            display: none;
        }
        
        .error.visible {
            display: block;
        }
        
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #e0e0e0;
            font-size: 12px;
            color: #999;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 Med-Triage OpenEnv</h1>
            <p>Clinical Decision-Making in Emergency Medicine</p>
        </div>
        
        <div class="status-box">
            <div class="status-item">
                <span class="status-label">Environment Status:</span>
                <span class="status-value" id="env-status">
                    <span class="status-badge badge-inactive">Loading...</span>
                </span>
            </div>
            <div class="status-item">
                <span class="status-label">GROQ API:</span>
                <span class="status-value" id="groq-status">
                    <span class="status-badge badge-inactive">Checking...</span>
                </span>
            </div>
            <div class="status-item">
                <span class="status-label">GEMINI API:</span>
                <span class="status-value" id="gemini-status">
                    <span class="status-badge badge-inactive">Checking...</span>
                </span>
            </div>
            <div class="status-item">
                <span class="status-label">Active Model:</span>
                <span class="status-value" id="model-status">
                    <span class="status-badge badge-info">-</span>
                </span>
            </div>
        </div>
        
        <div class="tasks">
            <button class="task-btn task-easy" onclick="runTask('easy')">
                🟢 Easy Task
            </button>
            <button class="task-btn task-medium" onclick="runTask('medium')">
                🟡 Medium Task
            </button>
            <button class="task-btn task-hard" onclick="runTask('hard')">
                🔴 Hard Task
            </button>
        </div>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p>Running episode...</p>
        </div>
        
        <div class="error" id="error"></div>
        
        <div class="results" id="results">
            <div id="results-content"></div>
        </div>
        
        <div class="footer">
            <p>Med-Triage OpenEnv • Powered by GROQ + GEMINI</p>
        </div>
    </div>
    
    <script>
        // Update status on page load
        window.addEventListener('load', () => {
            updateStatus();
            setInterval(updateStatus, 5000); // Update every 5 seconds
        });
        
        async function updateStatus() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                
                document.getElementById('env-status').innerHTML = 
                    '<span class="status-badge badge-active">Ready</span>';
                
                document.getElementById('groq-status').innerHTML = 
                    data.groq_available ? 
                    '<span class="status-badge badge-active">✓ Active</span>' :
                    '<span class="status-badge badge-inactive">✗ Inactive</span>';
                
                document.getElementById('gemini-status').innerHTML = 
                    data.gemini_available ? 
                    '<span class="status-badge badge-active">✓ Active</span>' :
                    '<span class="status-badge badge-inactive">✗ Inactive</span>';
                
                if (data.model_used) {
                    document.getElementById('model-status').innerHTML = 
                        '<span class="status-badge badge-info">' + data.model_used.toUpperCase() + '</span>';
                }
            } catch (e) {
                console.error('Status check failed:', e);
            }
        }
        
        async function runTask(difficulty) {
            const loading = document.getElementById('loading');
            const error = document.getElementById('error');
            const results = document.getElementById('results');
            
            loading.classList.add('visible');
            error.classList.remove('visible');
            results.classList.remove('visible');
            
            try {
                const response = await fetch('/run_episode', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ difficulty: difficulty })
                });
                
                const data = await response.json();
                
                if (!response.ok) {
                    throw new Error(data.error || 'Failed to run episode');
                }
                
                displayResults(data);
            } catch (err) {
                error.textContent = 'Error: ' + err.message;
                error.classList.add('visible');
            } finally {
                loading.classList.remove('visible');
            }
        }
        
        function displayResults(data) {
            const resultsContent = document.getElementById('results-content');
            const results = document.getElementById('results');
            
            let html = `
                <div class="result-item">
                    <div class="result-title">Episode Score</div>
                    <div class="result-value"><span class="score">${data.total_reward.toFixed(2)}</span></div>
                </div>
            `;
            
            if (data.reward_breakdown) {
                html += `
                    <div class="result-item">
                        <div class="result-title">Reward Breakdown</div>
                        <div class="result-value">
                            <strong>Priority Match:</strong> ${data.reward_breakdown.priority_match_reward?.toFixed(2) || 'N/A'}<br>
                            <strong>Category Match:</strong> ${data.reward_breakdown.category_match_reward?.toFixed(2) || 'N/A'}<br>
                            <strong>Agent Assignment:</strong> ${data.reward_breakdown.agent_assignment_reward?.toFixed(2) || 'N/A'}<br>
                            <strong>Queue Efficiency:</strong> ${data.reward_breakdown.queue_efficiency_reward?.toFixed(2) || 'N/A'}
                        </div>
                    </div>
                `;
            }
            
            if (data.model_used) {
                html += `
                    <div class="result-item">
                        <div class="result-title">Model Used</div>
                        <div class="result-value">${data.model_used.toUpperCase()}</div>
                    </div>
                `;
            }
            
            if (data.steps) {
                html += `
                    <div class="result-item">
                        <div class="result-title">Steps Taken</div>
                        <div class="result-value">${data.steps}</div>
                    </div>
                `;
            }
            
            resultsContent.innerHTML = html;
            results.classList.add('visible');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve main page."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "environment": "ready" if env else "not_initialized"
    })

@app.route('/status')
def status():
    """Return status of APIs and models."""
    groq_available = False
    gemini_available = False
    model_used = None
    
    if agent:
        groq_available = hasattr(agent, 'groq_client') and agent.groq_client is not None
        gemini_available = hasattr(agent, 'gemini_model') and agent.gemini_model is not None
        model_used = getattr(agent, 'model_used', None)
    
    return jsonify({
        "environment_ready": env is not None,
        "groq_available": groq_available,
        "gemini_available": gemini_available,
        "model_used": model_used,
        "apis_configured": groq_available or gemini_available
    })

@app.route('/run_episode', methods=['POST'])
def run_episode():
    """Run a complete episode and return results."""
    global last_episode_result
    
    if not env or not agent:
        return jsonify({
            "error": "Environment or agent not initialized"
        }), 500
    
    try:
        data = request.get_json() or {}
        difficulty = data.get('difficulty', 'medium')
        
        # Map difficulty to task level (1=easy, 2=medium, 3=hard)
        difficulty_map = {'easy': 1, 'medium': 2, 'hard': 3}
        task_level = difficulty_map.get(difficulty, 2)
        
        # Create environment with task level
        global env
        env = MedTriageEnv(task_level=task_level)
        
        # Reset environment
        obs = env.reset()
        
        steps = 0
        max_steps = 10
        total_reward = 0
        
        # Run episode
        while steps < max_steps:
            # Get action from agent
            action = agent.decide(obs)
            
            # Step environment
            obs, reward, done, info = env.step(action)
            
            # Extract reward value
            if isinstance(reward, dict):
                step_reward = reward.get('total_reward', 0)
            else:
                step_reward = float(reward) if reward else 0
            
            total_reward += step_reward
            steps += 1
            
            if done:
                break
        
        # Prepare response
        result = {
            "total_reward": total_reward,
            "steps": steps,
            "difficulty": difficulty,
            "model_used": getattr(agent, 'model_used', 'unknown')
        }
        
        # Add reward breakdown if available
        if hasattr(reward, 'components'):
            result["reward_breakdown"] = {
                "priority_match_reward": reward.components.get('priority_match', 0),
                "category_match_reward": reward.components.get('category_match', 0),
                "agent_assignment_reward": reward.components.get('agent_assignment', 0),
                "queue_efficiency_reward": reward.components.get('queue_efficiency', 0),
            }
        
        last_episode_result = result
        return jsonify(result)
        
    except Exception as e:
        print(f"Error running episode: {e}")
        traceback.print_exc()
        return jsonify({
            "error": str(e)
        }), 500

@app.route('/results')
def get_results():
    """Get last episode results."""
    if last_episode_result:
        return jsonify(last_episode_result)
    return jsonify({"error": "No results available"}), 404

if __name__ == '__main__':
    print("Initializing Med-Triage OpenEnv...")
    if init_app():
        print("Starting Flask server on 0.0.0.0:7860...")
        app.run(host='0.0.0.0', port=7860, debug=False)
    else:
        print("Failed to initialize app")
        exit(1)
