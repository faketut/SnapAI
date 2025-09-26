#!/usr/bin/env python3
"""
SnapAI Main Entry Point
Process manager for server and overlay components
"""

import sys
import os
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.process_manager.process_manager import ProcessManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """Main entry point"""
    manager = ProcessManager()
    manager.run()

if __name__ == '__main__':
    main()
