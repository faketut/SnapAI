#!/usr/bin/env python3
"""
File Watcher Utility for Hot Reload
Monitors file changes and triggers reloads
"""

import os
import time
import threading
import logging
from pathlib import Path
from typing import Callable, Set, List

logger = logging.getLogger(__name__)

class FileWatcher:
    """Watches files for changes and triggers callbacks"""
    
    def __init__(self, watch_dirs: List[str], callback: Callable[[str], None]):
        self.watch_dirs = [Path(d) for d in watch_dirs]
        self.callback = callback
        self.running = False
        self.thread = None
        self.file_times = {}
        self.watched_extensions = {'.html', '.css', '.js', '.py'}
        
    def start(self):
        """Start watching files"""
        if self.running:
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._watch_loop, daemon=True)
        self.thread.start()
        logger.info(f"File watcher started for directories: {self.watch_dirs}")
        
    def stop(self):
        """Stop watching files"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
        logger.info("File watcher stopped")
        
    def _watch_loop(self):
        """Main watching loop"""
        while self.running:
            try:
                self._check_files()
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Error in file watcher: {e}")
                time.sleep(5)
                
    def _check_files(self):
        """Check all watched files for changes"""
        for watch_dir in self.watch_dirs:
            if not watch_dir.exists():
                continue
                
            for file_path in watch_dir.rglob('*'):
                if file_path.is_file() and file_path.suffix in self.watched_extensions:
                    self._check_file(file_path)
                    
    def _check_file(self, file_path: Path):
        """Check if a specific file has changed"""
        try:
            # Skip certain files and directories
            if self._should_ignore_file(file_path):
                return
                
            current_mtime = file_path.stat().st_mtime
            file_key = str(file_path)
            
            if file_key in self.file_times:
                if current_mtime > self.file_times[file_key]:
                    logger.info(f"File changed: {file_path}")
                    self.file_times[file_key] = current_mtime
                    self.callback(str(file_path))
            else:
                self.file_times[file_key] = current_mtime
                
        except (OSError, FileNotFoundError):
            # File might have been deleted or moved
            pass
    
    def _should_ignore_file(self, file_path: Path) -> bool:
        """Check if file should be ignored"""
        # Ignore __pycache__ directories
        if '__pycache__' in str(file_path):
            return True
        
        # Ignore temporary files
        ignore_extensions = ['.tmp', '.temp', '~', '.swp', '.pyc', '.pyo', '.log', '.pid']
        if any(str(file_path).endswith(ext) for ext in ignore_extensions):
            return True
        
        # Ignore test files
        if 'test_' in str(file_path) or str(file_path).endswith('_test.py'):
            return True
            
        return False

class HotReloadManager:
    """Manages hot reload functionality"""
    
    def __init__(self, server_instance):
        self.server = server_instance
        self.watcher = None
        self.last_reload = 0
        self.reload_cooldown = 2  # Minimum seconds between reloads
        
    def start(self):
        """Start hot reload monitoring"""
        if not self.server.debug_mode:
            return
            
        watch_dirs = ['templates', 'static', 'src']
        self.watcher = FileWatcher(watch_dirs, self._on_file_change)
        self.watcher.start()
        logger.info("Hot reload manager started")
        
    def stop(self):
        """Stop hot reload monitoring"""
        if self.watcher:
            self.watcher.stop()
            self.watcher = None
        logger.info("Hot reload manager stopped")
        
    def _on_file_change(self, file_path: str):
        """Handle file change events"""
        current_time = time.time()
        if current_time - self.last_reload < self.reload_cooldown:
            return
            
        self.last_reload = current_time
        
        # Determine what type of file changed
        if file_path.endswith(('.html', '.css', '.js')):
            logger.info(f"Template/Static file changed: {file_path}")
            # For Flask with debug mode, the reloader will handle this automatically
        elif file_path.endswith('.py'):
            logger.info(f"Python file changed: {file_path}")
            # For Python files, Flask's reloader will handle this
        else:
            logger.info(f"Other file changed: {file_path}")
