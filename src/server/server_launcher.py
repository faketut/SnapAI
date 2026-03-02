#!/usr/bin/env python3
"""
SnapAI Server Launcher
Direct launcher for the server components
"""

import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from .main_server import MainServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main server entry point"""
    server = MainServer()
    server.run()

if __name__ == "__main__":
    main()
