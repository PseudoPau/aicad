#!/usr/bin/env python
"""
Main entry point for AI Warehouse Builder application
Runs the Streamlit frontend with proper backend path configuration
"""

import subprocess
import sys
from pathlib import Path

# Get the directory of this script
app_root = Path(__file__).parent
frontend_dir = app_root / "frontend"
app_file = frontend_dir / "app.py"

if not app_file.exists():
    print(f"Error: app.py not found at {app_file}")
    sys.exit(1)

# Run streamlit with proper working directory
print(f"Starting AI Warehouse Builder...")
print(f"App directory: {frontend_dir}")
print(f"Backend path will be added to sys.path automatically\n")

# Run streamlit
subprocess.run(
    [sys.executable, "-m", "streamlit", "run", str(app_file)],
    cwd=str(app_root),
    check=False
)
