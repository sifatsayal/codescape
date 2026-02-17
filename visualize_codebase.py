#!/usr/bin/env python3
"""
Entry point for codebase visualizer.

Run with no arguments to visualize the current directory:
    python visualize_codebase.py

Use the "Load repo" control in the top nav to open another repo by path.
You can also run with an explicit repo:
    python -m visualizer --repo <path>
"""

import sys
from pathlib import Path

# Add current directory to path so we can import visualizer
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the new CLI
from visualizer.cli import main

if __name__ == '__main__':
    sys.exit(main())
