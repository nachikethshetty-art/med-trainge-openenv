#!/usr/bin/env python3
"""
Flask web server for HF Spaces - listens on port 7860
Provides API endpoints for running the OpenEnv environment
"""

import os
import json
import sys
from flask import Flask, jsonify, request, render_template_string
from env import SupportTriageEnv, TriageAction, TicketPriority, TicketCategory
from inference import TicketTriageAgent, parse_env_vars

app = Flask(__name__)

# Initialize agent (will use GROQ primary, GEMINI fallback)
try:
    config = parse_env_vars()
    agent = TicketTriageAgent(config)
    print("✅ Agent initialized successfully", file=sys.stderr)
except ValueError as e:
    print(f"⚠️  Agent initialization warning: {e}", file=sys.stderr)
    print("⚠️  API keys not yet configured. Please add secrets to HF Space.", file=sys.stderr)
    agent = None
except Exception as e:
    print(f"⚠️  Agent init error: {e}", file=sys.stderr)
    agent = None


# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Support Ticket Triage OpenEnv</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
        .container { max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }
        h2 { color: #555; margin-top: 30px; }
        .status { padding: 10px; margin: 10px 0; border-radius: 4px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; }
        .card { border: 1px solid #ddd; padding: 15px; border-radius: 4px; }
        code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎫 Support Ticket Triage OpenEnv</h1>
        
        <div class="status info">
            <strong>OpenEnv Environment:</strong> Ready for agents to interact with
        </div>
        
        <h2>📊 Environment Status</h2>
        <div class="grid">
            <div class="card">
                <h3>🟢 API Keys</h3>
                <p id="api-status">Loading...</p>
            </div>
            <div class="card">
                <h3>⚡ Model</h3>
                <p id="model-status">Loading...</p>
            </div>
        </div>

        <h2>🚀 Quick Test</h2>
        <button onclick="runTest(1)">Test Task 1 (Easy)</button>
        <button onclick="runTest(2)">Test Task 2 (Medium)</button>
        <button onclick="runTest(3)">Test Task 3 (Hard)</button>
        <div id="test-result" style="margin-top: 20px;"></div>

        <h2>📝 API Endpoints</h2>
        <div class="card">
            <p><code>GET /</code> - This page</p>
            <p><code>GET /status</code> - Check environment status (JSON)</p>
            <p><code>POST /run_episode</code> - Run an episode</p>
            <p><code>GET /health</code> - Health check</p>
        </div>

        <h2>📖 Documentation</h2>
        <div class="card">
            <p><strong>GitHub:</strong> <a href="https://github.com/nachikethshetty-art/med-trainge-openenv" target="_blank">View Repository</a></p>
            <p><strong>Environment:</strong> Real-world support ticket triaging with multi-objective optimization</p>
            <p><strong>Tasks:</strong> 3 levels (Easy, Medium, Hard)</p>
            <p><strong>APIs:</strong> GROQ (primary) + GEMINI (fallback) - Both FREE</p>
        </div>
    </div>

    <script>
        function updateStatus() {
            fetch('/status')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('api-status').innerHTML = 
                        data.groq_available ? '✅ GROQ Active' : '⚠️ GROQ Inactive';
                    if (data.gemini_available) {
                        document.getElementById('api-status').innerHTML += '<br>✅ GEMINI Available (Fallback)';
                    }
                    document.getElementById('model-status').innerHTML = 
                        '<code>' + (data.model_used || 'Not tested yet') + '</code>';
                })
                .catch(e => console.error(e));
        }

        function runTest(taskLevel) {
            document.getElementById('test-result').innerHTML = '<div class="status info">Running...</div>';
            fetch('/run_episode', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({task_level: taskLevel})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('test-result').innerHTML = 
                        '<div class="status success">' +
                        '<strong>✅ Task ' + taskLevel + ' Success!</strong><br>' +
                        'Score: ' + data.score.toFixed(4) + '<br>' +
                        'Reward: ' + data.total_reward.toFixed(2) + '<br>' +
                        'Model: ' + (data.model_used || 'unknown') +
                        '</div>';
                } else {
                    document.getElementById('test-result').innerHTML = 
                        '<div class="status error"><strong>❌ Test Failed</strong><br>' + (data.error || 'Unknown error') + '</div>';
                }
            })
            .catch(e => {
                document.getElementById('test-result').innerHTML = 
                    '<div class="status error"><strong>❌ Error:</strong> ' + e.message + '</div>';
            });
        }

        // Update on load
        updateStatus();
        setInterval(updateStatus, 5000);
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """Main page"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "agent_ready": agent is not None
    })


@app.route('/status')
def status():
    """Check environment and API status"""
    try:
        from groq import Groq
        groq_available = os.getenv('GROQ_API_KEY') is not None
    except:
        groq_available = False
    
    try:
        import google.generativeai as genai
        gemini_available = os.getenv('GEMINI_API_KEY') is not None
    except:
        gemini_available = False
    
    return jsonify({
        "groq_available": groq_available,
        "gemini_available": gemini_available,
        "agent_ready": agent is not None,
        "model_used": getattr(agent, 'model_used', 'unknown') if agent else None
    })


@app.route('/run_episode', methods=['POST'])
def run_episode():
    """Run a single episode"""
    try:
        data = request.get_json() or {}
        task_level = data.get('task_level', 1)
        
        if not (1 <= task_level <= 3):
            return jsonify({
                "success": False,
                "error": "task_level must be 1, 2, or 3"
            }), 400
        
        if not agent:
            return jsonify({
                "success": False,
                "error": "Agent not initialized. Check API keys."
            }), 500
        
        # Create environment
        env = SupportTriageEnv(task_level=task_level, max_steps=50)
        
        # Run episode
        obs = env.reset()
        total_reward = 0.0
        steps = 0
        
        while steps < env.max_steps and obs.tickets:
            ticket = obs.tickets[0]
            ticket_dict = ticket.model_dump()
            
            try:
                action = agent.get_triage_decision(ticket_dict, obs.agent_workload)
                obs, reward, done, info = env.step(action)
                total_reward += reward.value
                steps += 1
                
                if done:
                    break
            except Exception as e:
                return jsonify({
                    "success": False,
                    "error": f"Step error: {str(e)}"
                }), 500
        
        # Grade performance
        from env import TaskGrader
        grader = TaskGrader(task_level)
        score = grader.grade(env, total_reward, info.metrics)
        
        return jsonify({
            "success": info.success,
            "task_level": task_level,
            "score": float(score),
            "total_reward": float(total_reward),
            "steps": steps,
            "model_used": getattr(agent, 'model_used', 'unknown')
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 7860))
    print(f"\n🚀 Starting server on port {port}...", file=sys.stderr)
    print(f"📌 Open http://localhost:{port}", file=sys.stderr)
    app.run(host='0.0.0.0', port=port, debug=False)
