#!/usr/bin/env python3
"""
Legacy entry point for codebase visualizer.

This file is a compatibility wrapper. For new usage, prefer:
    python -m visualizer --repo <path>

This wrapper redirects to the new visualizer package.
"""

import sys
from pathlib import Path

# Add current directory to path so we can import visualizer
sys.path.insert(0, str(Path(__file__).parent))

# Import and run the new CLI
from visualizer.cli import main

if __name__ == '__main__':
    sys.exit(main())
