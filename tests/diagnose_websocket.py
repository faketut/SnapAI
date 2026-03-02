#!/usr/bin/env python3
"""
Comprehensive WebSocket diagnostic script
"""

import sys
import os
import asyncio
import logging
import subprocess
import time
import socket

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def check_port_availability(port):
    """Check if a port is available"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return result != 0  # True if port is available
    except Exception as e:
        print(f"Error checking port {port}: {e}")
        return False

def check_dependencies():
    """Check if all required dependencies are installed"""
    print("Checking dependencies...")
    
    required_packages = [
        'websockets',
        'flask',
        'PyQt5',
        'keyboard',
        'PIL',
        'numpy',
        'psutil',
        'google.generativeai',
        'python-dotenv'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {missing_packages}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    return True

async def test_websocket_server_directly():
    """Test WebSocket server by creating it directly"""
    print("\nTesting WebSocket server directly...")
    
    try:
        from src.server.websocket_server import WebSocketServer
        from src.core.websocket_handler import WebSocketHandler
        
        # Create server
        ws_server = WebSocketServer('0.0.0.0', 8765)
        print("✓ WebSocket server created")
        
        # Start server
        ws_server.start()
        print("✓ WebSocket server started")
        
        # Wait for startup
        await asyncio.sleep(2)
        
        # Check if running
        if ws_server.is_running():
            print("✓ WebSocket server is running")
        else:
            print("✗ WebSocket server is not running")
            return False
        
        # Test connection
        try:
            import websockets
            async with websockets.connect('ws://localhost:8765') as ws:
                print("✓ Successfully connected to WebSocket server")
                
                # Send ping
                await ws.send('{"command": "ping"}')
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"✓ Received ping response: {response}")
                
        except Exception as e:
            print(f"✗ Failed to connect to WebSocket server: {e}")
            return False
        
        # Cleanup
        ws_server.stop()
        print("✓ WebSocket server stopped")
        return True
        
    except Exception as e:
        print(f"✗ Error testing WebSocket server: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_server_launcher():
    """Test the server launcher"""
    print("\nTesting server launcher...")
    
    try:
        from src.server.main_server import MainServer
        
        # Create server
        server = MainServer(debug_mode=True)
        print("✓ MainServer created")
        
        # Start WebSocket server only
        server.ws_server.start()
        print("✓ WebSocket server started via MainServer")
        
        # Wait for startup
        await asyncio.sleep(2)
        
        # Check if running
        if server.ws_server.is_running():
            print("✓ WebSocket server is running via MainServer")
        else:
            print("✗ WebSocket server is not running via MainServer")
            return False
        
        # Test connection
        try:
            import websockets
            async with websockets.connect('ws://localhost:8765') as ws:
                print("✓ Successfully connected to WebSocket server via MainServer")
                
                # Send ping
                await ws.send('{"command": "ping"}')
                response = await asyncio.wait_for(ws.recv(), timeout=5.0)
                print(f"✓ Received ping response: {response}")
                
        except Exception as e:
            print(f"✗ Failed to connect to WebSocket server via MainServer: {e}")
            return False
        
        # Cleanup
        server.ws_server.stop()
        print("✓ WebSocket server stopped via MainServer")
        return True
        
    except Exception as e:
        print(f"✗ Error testing server launcher: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_process_manager():
    """Check if process manager can start the server"""
    print("\nTesting process manager...")
    
    try:
        from src.process_manager.process_manager import ProcessManager
        
        # Create process manager
        pm = ProcessManager()
        print("✓ ProcessManager created")
        
        # Check if it can create server process
        try:
            server_proc = pm._create_process('src.server.server_launcher')
            print("✓ Server process created")
            
            # Wait a moment
            time.sleep(2)
            
            # Check if process is running
            if server_proc.poll() is None:
                print("✓ Server process is running")
                
                # Cleanup
                server_proc.terminate()
                server_proc.wait(timeout=5)
                print("✓ Server process terminated")
                return True
            else:
                stdout, stderr = server_proc.communicate()
                print(f"✗ Server process failed: {stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Error creating server process: {e}")
            return False
        
    except Exception as e:
        print(f"✗ Error testing process manager: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main diagnostic function"""
    print("WebSocket Diagnostic Tool")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Dependency check failed")
        return False
    
    # Check port availability
    print(f"\nChecking port 8765 availability...")
    if check_port_availability(8765):
        print("✓ Port 8765 is available")
    else:
        print("✗ Port 8765 is already in use")
    
    # Test WebSocket server directly
    if not await test_websocket_server_directly():
        print("\n❌ Direct WebSocket server test failed")
        return False
    
    # Test server launcher
    if not await test_server_launcher():
        print("\n❌ Server launcher test failed")
        return False
    
    # Test process manager
    if not check_process_manager():
        print("\n❌ Process manager test failed")
        return False
    
    print("\n✅ All tests passed! WebSocket server should be working.")
    print("\nTo run the full application:")
    print("  python main.py")
    print("\nTo test WebSocket connection:")
    print("  python test_websocket_connection.py")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
