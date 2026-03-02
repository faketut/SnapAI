#!/usr/bin/env python3
"""
Network diagnostic tool for SnapAI mobile access
"""

import socket
import subprocess
import sys
import os
import platform

def get_local_ip():
    """Get the local IP address"""
    try:
        # Connect to a remote address to determine local IP
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
        return local_ip
    except Exception:
        return "127.0.0.1"

def check_port_binding(host, port):
    """Check if a port is bound to a specific host"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex((host, port))
            return result == 0
    except Exception:
        return False

def check_firewall_windows():
    """Check Windows Firewall status"""
    try:
        result = subprocess.run(
            ['netsh', 'advfirewall', 'show', 'allprofiles', 'state'],
            capture_output=True, text=True, timeout=10
        )
        return result.stdout
    except Exception as e:
        return f"Error checking firewall: {e}"

def test_network_connectivity():
    """Test network connectivity"""
    print("Network Diagnostic Tool")
    print("=" * 40)
    
    # Get local IP
    local_ip = get_local_ip()
    print(f"Local IP address: {local_ip}")
    
    # Check if we can bind to all interfaces
    print(f"\nTesting port binding:")
    
    # Test localhost
    localhost_8080 = check_port_binding("127.0.0.1", 8080)
    localhost_8765 = check_port_binding("127.0.0.1", 8765)
    
    print(f"Port 8080 on localhost: {'✓ Available' if not localhost_8080 else '✗ In use'}")
    print(f"Port 8765 on localhost: {'✓ Available' if not localhost_8765 else '✗ In use'}")
    
    # Test external IP
    external_8080 = check_port_binding(local_ip, 8080)
    external_8765 = check_port_binding(local_ip, 8765)
    
    print(f"Port 8080 on {local_ip}: {'✓ Available' if not external_8080 else '✗ In use'}")
    print(f"Port 8765 on {local_ip}: {'✓ Available' if not external_8765 else '✗ In use'}")
    
    # Check firewall (Windows)
    if platform.system() == "Windows":
        print(f"\nWindows Firewall Status:")
        firewall_status = check_firewall_windows()
        print(firewall_status)
    
    # Provide connection URLs
    print(f"\nConnection URLs for mobile device:")
    print(f"HTTP: http://{local_ip}:8080")
    print(f"WebSocket: ws://{local_ip}:8765")
    
    # Check if ports are accessible from external
    if external_8080 or external_8765:
        print(f"\n⚠️  Warning: Ports are already in use!")
        print("Make sure no other application is using these ports.")
    
    # Network troubleshooting tips
    print(f"\nTroubleshooting Tips:")
    print("1. Make sure your phone and PC are on the same WiFi network")
    print("2. Check Windows Firewall - allow Python through firewall")
    print("3. Try disabling Windows Firewall temporarily to test")
    print("4. Check if your router blocks device-to-device communication")
    print("5. Try using the PC's IP address instead of localhost")
    
    return local_ip

def create_firewall_rule():
    """Create Windows Firewall rule for Python"""
    if platform.system() != "Windows":
        print("Firewall rules only supported on Windows")
        return
    
    print("\nCreating Windows Firewall rule for Python...")
    try:
        # Get Python executable path
        python_exe = sys.executable
        
        # Create inbound rule for Python
        cmd = [
            'netsh', 'advfirewall', 'firewall', 'add', 'rule',
            'name=SnapAI Python Server',
            'dir=in',
            'action=allow',
            f'program={python_exe}',
            'enable=yes'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ Firewall rule created successfully")
        else:
            print(f"✗ Failed to create firewall rule: {result.stderr}")
            
    except Exception as e:
        print(f"✗ Error creating firewall rule: {e}")

def main():
    """Main diagnostic function"""
    local_ip = test_network_connectivity()
    
    print(f"\n" + "=" * 40)
    print("Next Steps:")
    print("1. Start SnapAI: python main.py")
    print("2. Open http://" + local_ip + ":8080 on your phone")
    print("3. If it doesn't work, try creating firewall rule:")
    
    response = input("\nCreate Windows Firewall rule? (y/N): ")
    if response.lower() == 'y':
        create_firewall_rule()

if __name__ == "__main__":
    main()
