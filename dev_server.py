#!/usr/bin/env python3
"""
SnapAI Development Server with Hot Reload
Development server with auto-reload for templates, static files, and Python modules
"""

import sys
import os
import logging
import argparse

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.server.main_server import MainServer

# Configure logging for development
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def check_port_available(port):
    """Check if a port is available"""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('localhost', port))
            return True
        except OSError:
            return False

def main():
    """Main development server entry point"""
    parser = argparse.ArgumentParser(description='SnapAI Development Server')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--http-port', type=int, default=8080, help='HTTP port')
    parser.add_argument('--ws-port', type=int, default=8765, help='WebSocket port')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode with hot reload')
    
    args = parser.parse_args()
    
    # Check if ports are available
    if not check_port_available(args.http_port):
        print(f"❌ HTTP port {args.http_port} is already in use")
        print("💡 Try: python dev_server.py --http-port 8081")
        sys.exit(1)
    
    if not check_port_available(args.ws_port):
        print(f"⚠️  WebSocket port {args.ws_port} is already in use")
        print("💡 WebSocket functionality may be limited")
    
    print("🚀 Starting SnapAI Development Server...")
    print(f"📱 Mobile Client: http://{args.host}:{args.http_port}/")
    print(f"🔌 WebSocket: ws://{args.host}:{args.ws_port}")
    print(f"🔥 Hot Reload: {'Enabled' if args.debug else 'Disabled'}")
    print("=" * 50)
    
    try:
        # Create and run server with debug mode
        server = MainServer(
            host=args.host,
            http_port=args.http_port,
            ws_port=args.ws_port,
            debug_mode=args.debug
        )
        server.run()
    except KeyboardInterrupt:
        print("\n👋 Development server stopped")
    except Exception as e:
        print(f"❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
