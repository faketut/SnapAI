#!/usr/bin/env python3
"""
SnapAI Client Launcher
Direct launcher for the overlay client
"""

import sys
import os
import logging
import atexit
import platform

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from PyQt5.QtWidgets import QApplication
from .overlay_window import OverlayWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Lock file path
LOCK_FILE = os.path.join(os.path.dirname(__file__), '..', '..', '.overlay.lock')

def acquire_lock():
    """Acquire exclusive lock to prevent multiple overlay instances"""
    if os.path.exists(LOCK_FILE):
        # Check if the process is still running
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())
            
            if platform.system() == "Windows":
                import psutil
                if psutil.pid_exists(pid):
                    print("Another overlay instance is already running. Exiting.")
                    sys.exit(1)
            else:
                # Unix-like systems
                try:
                    os.kill(pid, 0)  # Check if process exists
                    print("Another overlay instance is already running. Exiting.")
                    sys.exit(1)
                except OSError:
                    # Process doesn't exist, remove stale lock file
                    os.remove(LOCK_FILE)
        except (ValueError, IOError):
            # Invalid lock file, remove it
            os.remove(LOCK_FILE)
    
    # Create new lock file
    try:
        with open(LOCK_FILE, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except IOError:
        print("Failed to create lock file. Exiting.")
        sys.exit(1)

def release_lock():
    """Release the lock file"""
    try:
        if os.path.exists(LOCK_FILE):
            os.remove(LOCK_FILE)
    except (IOError, OSError):
        pass

def main():
    """Main application entry point with proper cleanup"""
    # Acquire lock to prevent multiple instances
    if not acquire_lock():
        return
    
    # Register cleanup function
    atexit.register(release_lock)
    
    app = QApplication(sys.argv)
    window = OverlayWindow()
    window.show()
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("Application interrupted by user")
    finally:
        # Cleanup WebSocket client
        if hasattr(window, 'ws_client') and window.ws_client:
            window.ws_client.stop()
        # Release lock
        release_lock()

if __name__ == '__main__':
    main()
