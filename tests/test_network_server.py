#!/usr/bin/env python3
"""
Simple test server to verify network connectivity
"""

import socket
import threading
import time
import sys

def get_local_ip():
    """Get the local IP address"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "127.0.0.1"

def start_test_server(host, port):
    """Start a simple test server"""
    try:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((host, port))
        server.listen(5)
        
        print(f"Test server running on {host}:{port}")
        print(f"Access from mobile: http://{get_local_ip()}:{port}")
        print("Press Ctrl+C to stop")
        
        while True:
            client, addr = server.accept()
            print(f"Connection from {addr}")
            
            # Send a simple response
            response = f"""HTTP/1.1 200 OK
Content-Type: text/html

<html>
<head><title>SnapAI Test Server</title></head>
<body>
<h1>SnapAI Test Server</h1>
<p>Connection successful from {addr[0]}:{addr[1]}</p>
<p>Time: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
<p>If you can see this from your phone, network connectivity is working!</p>
</body>
</html>"""
            
            client.send(response.encode())
            client.close()
            
    except KeyboardInterrupt:
        print("\nTest server stopped")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        server.close()

def main():
    """Main function"""
    host = "0.0.0.0"
    port = 8080
    
    print("SnapAI Network Test Server")
    print("=" * 30)
    print(f"Starting test server on {host}:{port}")
    print(f"Local IP: {get_local_ip()}")
    print()
    
    start_test_server(host, port)

if __name__ == "__main__":
    main()
