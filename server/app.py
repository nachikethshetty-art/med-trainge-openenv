#!/usr/bin/env python3
"""
Server application entry point for Med-Triage OpenEnv.
Provides a wrapper around the Flask app for multi-mode deployment.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app_server import app, init_app


def main():
    """Main entry point for the server application."""
    # Initialize environment and agent
    if not init_app():
        print("Failed to initialize application")
        sys.exit(1)
    
    # Get configuration from environment
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "7860"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print(f"\n🚀 Starting Med-Triage OpenEnv Server")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"\n📊 API Endpoints:")
    print(f"   - GET  /           (Web UI)")
    print(f"   - GET  /health     (Health check)")
    print(f"   - GET  /status     (Status information)")
    print(f"   - POST /reset      (Initialize episode)")
    print(f"   - POST /step       (Execute action)")
    print(f"   - POST /run_episode (Run complete episode)")
    print()
    
    # Run the Flask app
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
