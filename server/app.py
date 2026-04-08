#!/usr/bin/env python3
"""
Flask web server for Med-Triage OpenEnv on HF Spaces.
This is the entry point for the server/app.py as expected by openenv validate.
Listens on port 7860 and provides REST API endpoints.
"""

import os
import sys

# Add parent directory to path so we can import from root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import and run the main app_server module
from app_server import app as flask_app
from app_server import main as app_main


def main():
    """Main entry point for server/app.py."""
    app_main()


if __name__ == "__main__":
    main()
