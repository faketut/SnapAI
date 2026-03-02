#!/usr/bin/env python3
"""
SnapAI Main Entry Point
Process manager for server and overlay components
"""

import sys
import os
import logging
import argparse

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
    parser = argparse.ArgumentParser(description="SnapAI Process Manager")
    parser.add_argument("--server", action="store_true", help="Start the server component")
    parser.add_argument("--client", action="store_true", help="Start the client overlay")
    args = parser.parse_args()

    if args.server:
        from src.server.main_server import MainServer
        server = MainServer()
        server.run()
    elif args.client:
        from src.clients.client_launcher import main as client_main
        client_main()
    else:
        # Default: Start the process manager
        manager = ProcessManager()
        manager.run()

if __name__ == '__main__':
    main()
