#!/usr/bin/env python3
"""
🎫 SUPPORT TRIAGE OPENENV - WEB FRONTEND DASHBOARD
Interactive HTML dashboard for testing the environment
"""

from flask import Flask, render_template_string, jsonify, request
from env import SupportTriageEnv, TriageAction, TaskGrader
import json
import threading

app = Flask(__name__)

# Global environment instance
env = None
current_episode = {
    "task_level": 1,
    "total_reward": 0,
    "steps": 0,
    "done": False,
    "score": 0.0,
    "history": []
}

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Support Triage OpenEnv - Interactive Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .tagline {
            font-size: 1.1em;
            opacity: 0.95;
        }
        
        .dashboard {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.15);
        }
        
        .card h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .control-section {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        .control-row {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            flex-wrap: wrap;
            align-items: center;
        }
        
        .control-row label {
            font-weight: 600;
            color: #333;
            min-width: 120px;
        }
        
        select, input, button {
            padding: 10px 15px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 1em;
            transition: all 0.3s ease;
        }
        
        select:focus, input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        button {
            background: #667eea;
            color: white;
            border: none;
            cursor: pointer;
            font-weight: 600;
            min-width: 120px;
        }
        
        button:hover {
            background: #764ba2;
            transform: scale(1.02);
        }
        
        button:active {
            transform: scale(0.98);
        }
        
        .button-group {
            display: flex;
            gap: 10px;
        }
        
        .button-danger {
            background: #e74c3c;
        }
        
        .button-danger:hover {
            background: #c0392b;
        }
        
        .button-success {
            background: #27ae60;
        }
        
        .button-success:hover {
            background: #229954;
        }
        
        .stat-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-box {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
        }
        
        .queue-section {
            margin-top: 20px;
        }
        
        .ticket-list {
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        
        .ticket-item {
            padding: 12px;
            border-bottom: 1px solid #eee;
            background: #f9f9f9;
            transition: background 0.3s ease;
        }
        
        .ticket-item:hover {
            background: #f0f0f0;
        }
        
        .ticket-item:last-child {
            border-bottom: none;
        }
        
        .ticket-id {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .ticket-subject {
            font-size: 0.95em;
            color: #333;
            margin-bottom: 5px;
        }
        
        .ticket-meta {
            display: flex;
            gap: 10px;
            font-size: 0.85em;
            color: #666;
        }
        
        .badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .badge-low {
            background: #d4edda;
            color: #155724;
        }
        
        .badge-medium {
            background: #fff3cd;
            color: #856404;
        }
        
        .badge-high {
            background: #f8d7da;
            color: #721c24;
        }
        
        .badge-critical {
            background: #d63031;
            color: white;
        }
        
        .action-controls {
            margin-top: 15px;
            padding: 15px;
            background: #f5f5f5;
            border-radius: 8px;
        }
        
        .history-section {
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
            background: #f9f9f9;
        }
        
        .history-item {
            padding: 8px;
            border-bottom: 1px solid #eee;
            font-size: 0.9em;
            font-family: monospace;
            color: #333;
        }
        
        .history-item.reward-positive {
            color: #27ae60;
        }
        
        .history-item.reward-negative {
            color: #e74c3c;
        }
        
        .reward-display {
            font-size: 1.2em;
            font-weight: bold;
            padding: 10px;
            border-radius: 6px;
            margin-top: 10px;
        }
        
        .reward-positive {
            background: #d4edda;
            color: #155724;
        }
        
        .reward-negative {
            background: #f8d7da;
            color: #721c24;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
            color: #667eea;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .alert {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
            display: none;
        }
        
        .alert-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .alert-error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .full-width {
            grid-column: 1 / -1;
        }
        
        @media (max-width: 768px) {
            .dashboard {
                grid-template-columns: 1fr;
            }
            h1 {
                font-size: 1.8em;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎫 Support Ticket Triage OpenEnv</h1>
            <p class="tagline">Real-world customer support ticket triaging environment</p>
        </header>
        
        <div id="alert"></div>
        
        <!-- Control Section -->
        <div class="control-section">
            <h2>⚙️ Episode Controls</h2>
            
            <div class="control-row">
                <label>Task Level:</label>
                <select id="taskLevel">
                    <option value="1">1 - Easy (5 tickets, LOW/MEDIUM)</option>
                    <option value="2" selected>2 - Medium (10 tickets, mixed)</option>
                    <option value="3">3 - Hard (15 tickets, CRITICAL)</option>
                </select>
                <button onclick="resetEpisode()" class="button-success">🔄 Reset Episode</button>
            </div>
            
            <div id="loading" class="loading">
                <div class="spinner"></div>
                <p>Loading environment...</p>
            </div>
        </div>
        
        <!-- Stats Section -->
        <div class="stat-grid" id="statsGrid">
            <div class="stat-box">
                <div class="stat-label">Current Task</div>
                <div class="stat-value" id="currentTask">2</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Queue Size</div>
                <div class="stat-value" id="queueSize">10</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Total Reward</div>
                <div class="stat-value" id="totalReward">0.00</div>
            </div>
            <div class="stat-box">
                <div class="stat-label">Steps Completed</div>
                <div class="stat-value" id="stepCount">0</div>
            </div>
        </div>
        
        <!-- Main Dashboard -->
        <div class="dashboard">
            <!-- Queue Section -->
            <div class="card">
                <h2>📋 Ticket Queue</h2>
                <div class="queue-section">
                    <div class="ticket-list" id="ticketList">
                        <div style="padding: 20px; text-align: center; color: #999;">
                            Click "Reset Episode" to load tickets
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Action Section -->
            <div class="card">
                <h2>🎯 Triage Action</h2>
                <div class="action-controls">
                    <div class="control-row">
                        <label>Priority:</label>
                        <select id="prioritySelect">
                            <option value="low">Low</option>
                            <option value="medium" selected>Medium</option>
                            <option value="high">High</option>
                            <option value="critical">Critical</option>
                        </select>
                    </div>
                    
                    <div class="control-row">
                        <label>Category:</label>
                        <select id="categorySelect">
                            <option value="billing">Billing</option>
                            <option value="technical" selected>Technical</option>
                            <option value="account">Account</option>
                            <option value="feature_request">Feature Request</option>
                            <option value="bug_report">Bug Report</option>
                        </select>
                    </div>
                    
                    <div class="control-row">
                        <label>Assign To:</label>
                        <select id="agentSelect">
                            <option value="agent_1">Agent 1</option>
                            <option value="agent_2" selected>Agent 2</option>
                            <option value="agent_3">Agent 3</option>
                        </select>
                    </div>
                    
                    <div class="control-row">
                        <button onclick="takeAction()" class="button-success">✅ Execute Action</button>
                        <button onclick="autoRun()" class="button-success">⚡ Auto Run (5 steps)</button>
                    </div>
                    
                    <div id="rewardDisplay"></div>
                </div>
            </div>
            
            <!-- Workload Section -->
            <div class="card">
                <h2>👥 Agent Workload</h2>
                <canvas id="workloadChart"></canvas>
                <div style="margin-top: 15px; font-size: 0.9em; color: #666;">
                    <div id="workloadStats"></div>
                </div>
            </div>
            
            <!-- Metrics Section -->
            <div class="card">
                <h2>📊 Performance Metrics</h2>
                <canvas id="metricsChart"></canvas>
                <div style="margin-top: 15px; font-size: 0.9em; color: #666;">
                    <div id="metricsStats"></div>
                </div>
            </div>
            
            <!-- History Section -->
            <div class="card full-width">
                <h2>📜 Step History</h2>
                <div class="history-section" id="historyList">
                    <div style="text-align: center; color: #999;">Episode history will appear here</div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let workloadChart = null;
        let metricsChart = null;
        
        function showAlert(message, type = 'info') {
            const alert = document.getElementById('alert');
            alert.className = `alert alert-${type}`;
            alert.textContent = message;
            alert.style.display = 'block';
            setTimeout(() => { alert.style.display = 'none'; }, 5000);
        }
        
        async function resetEpisode() {
            const taskLevel = document.getElementById('taskLevel').value;
            document.getElementById('loading').style.display = 'block';
            
            try {
                const response = await fetch('/api/reset', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ task_level: parseInt(taskLevel) })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    updateDashboard(data.observation);
                    showAlert('Episode reset successfully!', 'success');
                } else {
                    showAlert('Error: ' + data.message, 'error');
                }
            } catch (error) {
                showAlert('Error resetting episode: ' + error.message, 'error');
            } finally {
                document.getElementById('loading').style.display = 'none';
            }
        }
        
        async function takeAction() {
            const priority = document.getElementById('prioritySelect').value;
            const category = document.getElementById('categorySelect').value;
            const agent = document.getElementById('agentSelect').value;
            
            try {
                const response = await fetch('/api/step', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ priority, category, agent })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    updateDashboard(data.observation, data.reward, data.done);
                    showAlert('Action executed! Reward: ' + data.reward.toFixed(2), 'success');
                } else {
                    showAlert('Error: ' + data.message, 'error');
                }
            } catch (error) {
                showAlert('Error taking action: ' + error.message, 'error');
            }
        }
        
        async function autoRun() {
            for (let i = 0; i < 5; i++) {
                await new Promise(resolve => setTimeout(resolve, 500));
                await takeAction();
            }
        }
        
        function updateDashboard(obs, reward = null, done = false) {
            // Update stats
            document.getElementById('currentTask').textContent = obs.task_level || '2';
            document.getElementById('queueSize').textContent = obs.queue_size;
            document.getElementById('totalReward').textContent = obs.total_reward?.toFixed(2) || '0.00';
            document.getElementById('stepCount').textContent = obs.steps || '0';
            
            // Update ticket list
            const ticketList = document.getElementById('ticketList');
            if (obs.tickets && obs.tickets.length > 0) {
                ticketList.innerHTML = obs.tickets.slice(0, 5).map(ticket => `
                    <div class="ticket-item">
                        <div class="ticket-id">${ticket.ticket_id}</div>
                        <div class="ticket-subject">${ticket.subject.substring(0, 50)}...</div>
                        <div class="ticket-meta">
                            <span class="badge badge-${ticket.priority}">${ticket.priority.toUpperCase()}</span>
                            <span>${ticket.category}</span>
                            <span>Sentiment: ${(ticket.sentiment_score * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                `).join('');
            }
            
            // Update workload chart
            if (obs.agent_workload) {
                updateWorkloadChart(obs.agent_workload);
            }
            
            // Update metrics chart
            if (obs.metrics) {
                updateMetricsChart(obs.metrics);
            }
            
            // Update reward display
            if (reward !== null) {
                const rewardClass = reward >= 0 ? 'reward-positive' : 'reward-negative';
                document.getElementById('rewardDisplay').innerHTML = `
                    <div class="reward-display ${rewardClass}">
                        Step Reward: ${reward >= 0 ? '+' : ''}${reward.toFixed(2)}
                    </div>
                `;
            }
            
            // Add to history
            const historyList = document.getElementById('historyList');
            const historyItem = document.createElement('div');
            historyItem.className = `history-item ${reward && reward >= 0 ? 'reward-positive' : 'reward-negative'}`;
            historyItem.textContent = `Step ${obs.steps}: ${obs.agent_workload ? 'Action taken' : 'Ready'} | Reward: ${reward ? reward.toFixed(2) : 'N/A'} | Queue: ${obs.queue_size}`;
            
            if (historyList.children[0]?.textContent.includes('history will appear')) {
                historyList.innerHTML = '';
            }
            historyList.insertBefore(historyItem, historyList.firstChild);
            
            if (done) {
                showAlert('Episode completed!', 'success');
            }
        }
        
        function updateWorkloadChart(workload) {
            const ctx = document.getElementById('workloadChart');
            const labels = Object.keys(workload);
            const data = Object.values(workload);
            
            if (workloadChart) {
                workloadChart.destroy();
            }
            
            workloadChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Tickets Assigned',
                        data: data,
                        backgroundColor: ['#667eea', '#764ba2', '#f093fb']
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: { beginAtZero: true }
                    }
                }
            });
            
            const workloadStats = `
                ${labels.map((l, i) => `<div>${l}: ${data[i]} tickets</div>`).join('')}
            `;
            document.getElementById('workloadStats').innerHTML = workloadStats;
        }
        
        function updateMetricsChart(metrics) {
            const ctx = document.getElementById('metricsChart');
            const labels = Object.keys(metrics);
            const data = Object.values(metrics).map(v => typeof v === 'number' ? (v * 100).toFixed(0) : 0);
            
            if (metricsChart) {
                metricsChart.destroy();
            }
            
            metricsChart = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Metrics (%)',
                        data: data,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.2)',
                        pointBackgroundColor: '#667eea'
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        r: { beginAtZero: true, max: 100 }
                    }
                }
            });
            
            const metricsStats = `
                ${labels.map((l, i) => `<div>${l}: ${data[i]}%</div>`).join('')}
            `;
            document.getElementById('metricsStats').innerHTML = metricsStats;
        }
        
        // Initialize on load
        window.addEventListener('load', () => {
            resetEpisode();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/reset', methods=['POST'])
def api_reset():
    global env, current_episode
    
    data = request.json
    task_level = data.get('task_level', 1)
    
    try:
        env = SupportTriageEnv(task_level=task_level, seed=42)
        obs = env.reset()
        
        current_episode = {
            "task_level": task_level,
            "total_reward": 0,
            "steps": 0,
            "done": False,
            "score": 0.0,
            "history": []
        }
        
        return jsonify({
            "status": "success",
            "observation": {
                "task_level": task_level,
                "queue_size": obs.queue_size,
                "tickets": [
                    {
                        "ticket_id": t.ticket_id,
                        "subject": t.subject,
                        "category": t.category.value,
                        "priority": t.priority.value,
                        "sentiment_score": t.sentiment_score
                    }
                    for t in obs.tickets[:5]
                ],
                "agent_workload": obs.agent_workload,
                "metrics": obs.metrics,
                "steps": 0,
                "total_reward": 0.0
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

@app.route('/api/step', methods=['POST'])
def api_step():
    global env, current_episode
    
    if env is None:
        return jsonify({"status": "error", "message": "Environment not initialized"}), 400
    
    data = request.json
    
    try:
        # Get current ticket
        obs = env.reset() if current_episode["steps"] == 0 else env.state()
        
        if not obs or "tickets" not in obs:
            obs = env.reset()
        
        # In the actual env, we need to step through properly
        # For now, simulate based on current state
        first_ticket = None
        
        # Since we can't directly access observations, create action with sensible defaults
        priority = data.get('priority', 'medium').lower()
        category = data.get('category', 'technical').lower()
        agent = data.get('agent', 'agent_1')
        
        action = TriageAction(
            ticket_id=f"T{current_episode['steps']:05d}_000",
            priority=priority,
            category=category,
            assign_to_agent=agent,
            notes="Manual triage from frontend"
        )
        
        obs, reward, done, info = env.step(action)
        
        current_episode["steps"] += 1
        current_episode["total_reward"] += reward.value
        current_episode["done"] = done
        current_episode["history"].append({
            "step": current_episode["steps"],
            "reward": reward.value,
            "action": {
                "priority": priority,
                "category": category,
                "agent": agent
            }
        })
        
        # Calculate score if done
        if done:
            grader = TaskGrader(current_episode["task_level"])
            current_episode["score"] = grader.grade(
                env,
                current_episode["total_reward"],
                obs.metrics
            )
        
        return jsonify({
            "status": "success",
            "reward": reward.value,
            "done": done,
            "observation": {
                "task_level": current_episode["task_level"],
                "queue_size": obs.queue_size,
                "tickets": [
                    {
                        "ticket_id": t.ticket_id,
                        "subject": t.subject,
                        "category": t.category.value,
                        "priority": t.priority.value,
                        "sentiment_score": t.sentiment_score
                    }
                    for t in obs.tickets[:5]
                ],
                "agent_workload": obs.agent_workload,
                "metrics": obs.metrics,
                "steps": current_episode["steps"],
                "total_reward": current_episode["total_reward"]
            }
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400

if __name__ == '__main__':
    print("""
    
    ╔════════════════════════════════════════════════════════════╗
    ║   🎫 SUPPORT TRIAGE OPENENV - WEB DASHBOARD                ║
    ║                                                            ║
    ║   🌐 Open your browser:                                   ║
    ║      http://127.0.0.1:8080                                ║
    ║                                                            ║
    ║   Press CTRL+C to stop the server                         ║
    ╚════════════════════════════════════════════════════════════╝
    
    """)
    
    app.run(debug=False, host='0.0.0.0', port=8080, threaded=True)
