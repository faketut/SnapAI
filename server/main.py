import subprocess
import sys
import os
import time
import signal
import logging
import psutil
from typing import Optional, Dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
STARTUP_WAIT = 3  # seconds to wait for processes to start
MAX_RESTART_ATTEMPTS = 3
RESTART_DELAY = 2  # seconds between restart attempts

class ProcessManager:
    def __init__(self):
        self.server_proc: Optional[subprocess.Popen] = None
        self.overlay_proc: Optional[subprocess.Popen] = None
        self.running = True
        self.restart_counts: Dict[str, int] = {"server": 0, "overlay": 0}
        self.base_path = os.path.dirname(os.path.abspath(__file__))

    def _create_process(self, script_name: str, env: Optional[dict] = None) -> subprocess.Popen:
        """Create a new process with proper environment and error handling"""
        script_path = os.path.join(self.base_path, script_name)
        if not os.path.exists(script_path):
            raise FileNotFoundError(f"Script not found: {script_path}")

        # Prepare environment
        proc_env = os.environ.copy()
        if env:
            proc_env.update(env)

        # Create process with proper configuration
        return subprocess.Popen(
            [sys.executable, script_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=proc_env,
            cwd=self.base_path,
            universal_newlines=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP  # Windows-specific
        )

    def _check_port_available(self, port: int) -> bool:
        """Check if a port is available"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('localhost', port))
                return True
            except socket.error:
                return False

    def start_processes(self):
        """Start server and overlay processes with proper error handling"""
        try:
            # Check if ports are available
            if not self._check_port_available(8080):
                raise RuntimeError("Port 8080 is already in use")
            if not self._check_port_available(8765):
                raise RuntimeError("Port 8765 is already in use")

            # Start server.py
            self.server_proc = self._create_process('server.py')
            logger.info("Started server process")

            # Wait for server to initialize
            time.sleep(STARTUP_WAIT)

            if self.server_proc.poll() is not None:
                # Server failed to start
                stdout, stderr = self.server_proc.communicate()
                raise RuntimeError(f"Server failed to start: {stderr}")

            # Start overlay.py
            self.overlay_proc = self._create_process('overlay.py')
            logger.info("Started overlay process")

            # Quick check for immediate failures
            time.sleep(1)
            if self.overlay_proc.poll() is not None:
                stdout, stderr = self.overlay_proc.communicate()
                raise RuntimeError(f"Overlay failed to start: {stderr}")

        except Exception as e:
            logger.error(f"Failed to start processes: {e}")
            self.cleanup()
            sys.exit(1)

    def cleanup(self):
        """Clean up processes with proper error handling"""
        logger.info("Cleaning up processes...")
        
        def kill_proc_tree(proc: subprocess.Popen, name: str):
            try:
                process = psutil.Process(proc.pid)
                children = process.children(recursive=True)
                
                # Terminate children first
                for child in children:
                    try:
                        child.terminate()
                    except psutil.NoSuchProcess:
                        pass

                # Terminate main process
                proc.terminate()
                
                try:
                    proc.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    logger.warning(f"{name} process did not terminate gracefully, force killing...")
                    
                    # Kill children
                    for child in children:
                        try:
                            child.kill()
                        except psutil.NoSuchProcess:
                            pass
                    
                    # Kill main process
                    proc.kill()
                    proc.wait(timeout=2)
                    
            except (psutil.NoSuchProcess, ProcessLookupError):
                pass
            except Exception as e:
                logger.error(f"Error cleaning up {name} process: {e}")
                try:
                    proc.kill()
                except:
                    pass

        # Clean up both processes
        if self.server_proc:
            kill_proc_tree(self.server_proc, "Server")
        if self.overlay_proc:
            kill_proc_tree(self.overlay_proc, "Overlay")

    def _try_restart_process(self, proc_name: str) -> bool:
        """Attempt to restart a failed process"""
        if self.restart_counts[proc_name] >= MAX_RESTART_ATTEMPTS:
            logger.error(f"{proc_name} failed too many times, giving up")
            return False

        logger.info(f"Attempting to restart {proc_name}...")
        self.restart_counts[proc_name] += 1
        time.sleep(RESTART_DELAY)

        try:
            if proc_name == "server":
                self.server_proc = self._create_process('server.py')
                time.sleep(STARTUP_WAIT)
            else:  # overlay
                self.overlay_proc = self._create_process('overlay.py')
            
            logger.info(f"Successfully restarted {proc_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to restart {proc_name}: {e}")
            return False

    def handle_signal(self, signum, frame):
        logger.info(f"Received signal {signum}")
        self.running = False
        self.cleanup()
        sys.exit(0)

def main():
    manager = ProcessManager()
    
    # Register signal handlers
    signal.signal(signal.SIGINT, manager.handle_signal)
    signal.signal(signal.SIGTERM, manager.handle_signal)

    try:
        manager.start_processes()
        
        # Keep the main process running
        while manager.running:
            # Check server process
            if manager.server_proc and manager.server_proc.poll() is not None:
                logger.error("Server process terminated unexpectedly")
                
                # Try to get error output
                _, stderr = manager.server_proc.communicate()
                if stderr:
                    logger.error(f"Server error output: {stderr}")
                
                if not manager._try_restart_process("server"):
                    break

            # Check overlay process
            if manager.overlay_proc and manager.overlay_proc.poll() is not None:
                logger.error("Overlay process terminated unexpectedly")
                
                # Try to get error output
                _, stderr = manager.overlay_proc.communicate()
                if stderr:
                    logger.error(f"Overlay error output: {stderr}")
                
                if not manager._try_restart_process("overlay"):
                    break

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt, shutting down...")
    except Exception as e:
        logger.error(f"Main process error: {e}")
    finally:
        manager.cleanup()
        sys.exit(0)

if __name__ == '__main__':
    main()