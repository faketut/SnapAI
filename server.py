#!/usr/bin/env python3
"""
SnapAI Server Entry Point
Modular server implementation with Flask and WebSocket
"""

import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.server.main_server import MainServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

if __name__ == "__main__":
    server = MainServer()
    server.run()
