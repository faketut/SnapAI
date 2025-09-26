import subprocess
import sys
import os
import time
import signal
import logging
import psutil
import platform
import threading
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Constants
STARTUP_WAIT = 3  # seconds to wait for processes to start
MAX_RESTART_ATTEMPTS = 3
RESTART_DELAY = 2  # seconds between restart attempts
HEALTH_CHECK_INTERVAL = 5  # seconds between health checks
MAX_PROCESS_WAIT = 10  # seconds to wait for process termination


class ProcessManager:
    """Manages server and overlay processes with auto-restart capabilities"""
    
    def __init__(self):
        self.server_proc: Optional[subprocess.Popen] = None
        self.overlay_proc: Optional[subprocess.Popen] = None
        self.running = True
        self.restart_counts: Dict[str, int] = {"server": 0, "overlay": 0}
        # Get the project root directory (3 levels up from this file)
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        """Check if a port is available with timeout"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)  # 1 second timeout
            try:
                s.bind(('localhost', port))
                return True
            except (socket.error, OSError):
                return False

    def _check_overlay_running(self) -> bool:
        """Check if overlay process is already running"""
        lock_file = os.path.join(self.base_path, '.overlay.lock')
        if not os.path.exists(lock_file):
            return False
        
        try:
            with open(lock_file, 'r') as f:
                pid = int(f.read().strip())
            
            if platform.system() == "Windows":
                return psutil.pid_exists(pid)
            else:
                # Unix-like systems
                try:
                    os.kill(pid, 0)  # Check if process exists
                    return True
                except OSError:
                    # Process doesn't exist, remove stale lock file
                    os.remove(lock_file)
                    return False
        except (ValueError, IOError):
            # Invalid lock file, remove it
            if os.path.exists(lock_file):
                os.remove(lock_file)
            return False

    def _check_server_health(self) -> bool:
        """Check if server is responding to health checks"""
        try:
            import requests
            response = requests.get(f'http://localhost:8080/health', timeout=5)
            return response.status_code == 200
        except Exception:
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

            # Check if overlay is already running
            if self._check_overlay_running():
                logger.info("Overlay process is already running, skipping overlay start")
                self.overlay_proc = None  # Mark as None since we didn't start it
            else:
                # Start overlay.py
                self.overlay_proc = self._create_process('overlay.py')
                logger.info("Started overlay process")

            # Quick check for immediate failures (only if we started the process)
            if self.overlay_proc is not None:
                time.sleep(1)
                if self.overlay_proc.poll() is not None:
                    stdout, stderr = self.overlay_proc.communicate()
                    raise RuntimeError(f"Overlay failed to start: {stderr}")

        except Exception as e:
            logger.error(f"Failed to start processes: {e}")
            self.cleanup()
            sys.exit(1)

    def cleanup(self):
        """Clean up processes with improved error handling and timeout"""
        logger.info("Cleaning up processes...")
        
        def kill_proc_tree(proc: subprocess.Popen, name: str):
            if not proc or proc.poll() is not None:
                return
                
            try:
                process = psutil.Process(proc.pid)
                children = process.children(recursive=True)
                
                # Terminate children first
                for child in children:
                    try:
                        child.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass

                # Terminate main process
                proc.terminate()
                
                try:
                    proc.wait(timeout=MAX_PROCESS_WAIT)
                    logger.info(f"{name} process terminated gracefully")
                except subprocess.TimeoutExpired:
                    logger.warning(f"{name} process did not terminate gracefully, force killing...")
                    
                    # Kill children
                    for child in children:
                        try:
                            child.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    # Kill main process
                    proc.kill()
                    try:
                        proc.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        logger.error(f"Failed to kill {name} process")
                    
            except (psutil.NoSuchProcess, ProcessLookupError, psutil.AccessDenied):
                pass
            except Exception as e:
                logger.error(f"Error cleaning up {name} process: {e}")
                try:
                    proc.kill()
                except:
                    pass

        # Clean up both processes concurrently
        cleanup_tasks = []
        if self.server_proc:
            cleanup_tasks.append(threading.Thread(target=lambda: kill_proc_tree(self.server_proc, "Server")))
        if self.overlay_proc:
            cleanup_tasks.append(threading.Thread(target=lambda: kill_proc_tree(self.overlay_proc, "Overlay")))
        
        # Start cleanup tasks
        for task in cleanup_tasks:
            task.start()
        
        # Wait for cleanup to complete
        for task in cleanup_tasks:
            task.join(timeout=MAX_PROCESS_WAIT + 2)

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

    def run(self):
        """Main process management loop"""
        # Register signal handlers
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

        try:
            self.start_processes()
            
            # Keep the main process running with improved health checking
            while self.running:
                try:
                    # Check server process
                    if self.server_proc and self.server_proc.poll() is not None:
                        logger.error("Server process terminated unexpectedly")
                        
                        # Try to get error output
                        try:
                            _, stderr = self.server_proc.communicate(timeout=1)
                            if stderr:
                                logger.error(f"Server error output: {stderr}")
                        except subprocess.TimeoutExpired:
                            logger.warning("Server process output timeout")
                        
                        if not self._try_restart_process("server"):
                            logger.error("Failed to restart server, shutting down")
                            break
                    elif self.server_proc and not self._check_server_health():
                        logger.warning("Server is not responding to health checks, restarting...")
                        if not self._try_restart_process("server"):
                            logger.error("Failed to restart unresponsive server, shutting down")
                            break

                    # Check overlay process (only if we started it)
                    if self.overlay_proc and self.overlay_proc.poll() is not None:
                        logger.error("Overlay process terminated unexpectedly")
                        
                        # Try to get error output
                        try:
                            _, stderr = self.overlay_proc.communicate(timeout=1)
                            if stderr:
                                logger.error(f"Overlay error output: {stderr}")
                        except subprocess.TimeoutExpired:
                            logger.warning("Overlay process output timeout")
                        
                        if not self._try_restart_process("overlay"):
                            logger.error("Failed to restart overlay, shutting down")
                            break
                    elif self.overlay_proc is None:
                        # Check if the external overlay process is still running
                        if not self._check_overlay_running():
                            logger.warning("External overlay process stopped, attempting to restart")
                            if not self._try_restart_process("overlay"):
                                logger.error("Failed to restart overlay, shutting down")
                                break

                    time.sleep(HEALTH_CHECK_INTERVAL)
                    
                except KeyboardInterrupt:
                    logger.info("Received keyboard interrupt in main loop")
                    break
                except Exception as e:
                    logger.error(f"Error in main loop: {e}")
                    time.sleep(1)

        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
        except Exception as e:
            logger.error(f"Main process error: {e}")
        finally:
            self.cleanup()
            sys.exit(0)
