#!/usr/bin/env python3
"""
Test WebSocket connection to verify server is working
"""

import asyncio
import websockets
import json
import sys

async def test_websocket_connection():
    """Test connection to WebSocket server"""
    try:
        print("Testing WebSocket connection to localhost:8765...")
        
        async with websockets.connect('ws://localhost:8765') as websocket:
            print("✓ Connected to WebSocket server")
            
            # Send a ping message
            ping_message = {"command": "ping"}
            await websocket.send(json.dumps(ping_message))
            print("✓ Sent ping message")
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            data = json.loads(response)
            print(f"✓ Received response: {data}")
            
            # Send a sync request
            sync_message = {"command": "sync_request"}
            await websocket.send(json.dumps(sync_message))
            print("✓ Sent sync request")
            
            # Wait for sync response
            sync_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
            sync_data = json.loads(sync_response)
            print(f"✓ Received sync response: {sync_data}")
            
            print("\n✅ WebSocket server is working correctly!")
            return True
            
    except websockets.exceptions.ConnectionRefused:
        print("✗ Connection refused - WebSocket server is not running")
        return False
    except asyncio.TimeoutError:
        print("✗ Timeout - WebSocket server is not responding")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False

async def main():
    """Main test function"""
    print("WebSocket Connection Test")
    print("=" * 30)
    
    success = await test_websocket_connection()
    
    if not success:
        print("\n❌ WebSocket connection test failed")
        print("Make sure the server is running with: python main.py")
    else:
        print("\n✅ WebSocket connection test passed")
    
    return success

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
