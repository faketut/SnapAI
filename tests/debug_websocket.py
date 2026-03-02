#!/usr/bin/env python3
"""
Debug script to test WebSocket server independently
"""

import sys
import os
import asyncio
import logging

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_websocket_server():
    """Test WebSocket server startup"""
    print("Testing WebSocket server startup...")
    
    try:
        from src.server.websocket_server import WebSocketServer
        from src.core.websocket_handler import WebSocketHandler
        
        print("✓ Imports successful")
        
        # Test WebSocket server creation
        ws_server = WebSocketServer('0.0.0.0', 8765)
        print("✓ WebSocket server created")
        
        # Test WebSocket handler creation
        ws_handler = WebSocketHandler()
        print("✓ WebSocket handler created")
        
        # Test server startup
        print("Starting WebSocket server...")
        ws_server.start()
        
        # Wait a bit to see if it starts
        await asyncio.sleep(2)
        
        if ws_server.thread and ws_server.thread.is_alive():
            print("✓ WebSocket server thread is running")
        else:
            print("✗ WebSocket server thread is not running")
            
        # Test if we can connect to it
        try:
            import websockets
            async with websockets.connect('ws://localhost:8765') as ws:
                print("✓ Successfully connected to WebSocket server")
                await ws.send('{"command": "ping"}')
                response = await ws.recv()
                print(f"✓ Received response: {response}")
        except Exception as e:
            print(f"✗ Failed to connect to WebSocket server: {e}")
        
        # Cleanup
        ws_server.stop()
        print("✓ WebSocket server stopped")
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

async def test_server_launcher():
    """Test the server launcher"""
    print("\nTesting server launcher...")
    
    try:
        from src.server.main_server import MainServer
        
        print("✓ MainServer import successful")
        
        # Create server instance
        server = MainServer(debug_mode=True)
        print("✓ MainServer created")
        
        # Test WebSocket server initialization
        if hasattr(server, 'ws_server') and server.ws_server:
            print("✓ WebSocket server initialized")
        else:
            print("✗ WebSocket server not initialized")
            
        # Test Flask app initialization
        if hasattr(server, 'flask_app') and server.flask_app:
            print("✓ Flask app initialized")
        else:
            print("✗ Flask app not initialized")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("WebSocket Server Debug Test")
    print("=" * 40)
    
    # Test imports and basic functionality
    asyncio.run(test_websocket_server())
    asyncio.run(test_server_launcher())
    
    print("\n" + "=" * 40)
    print("Debug test completed")

if __name__ == "__main__":
    main()
