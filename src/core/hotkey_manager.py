import json
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class HotkeyManager:
    """Manages loading and mapping of global hotkeys"""
    
    DEFAULT_HOTKEYS = {
        "capture_screenshot": "f7",
        "process_clipboard": "f8",
        "show_overlay": "f9",
        "hide_overlay": "f10"
    }

    def __init__(self, config_path: Optional[str] = None):
        if config_path is None:
            # Default to src/config/hotkeys.json relative to this file
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, 'config', 'hotkeys.json')
        
        self.config_path = config_path
        self.hotkeys = self.DEFAULT_HOTKEYS.copy()
        self.load_config()

    def load_config(self) -> None:
        """Load hotkey configuration from JSON file"""
        if not os.path.exists(self.config_path):
            logger.info(f"Config file not found at {self.config_path}, using defaults.")
            self._ensure_config_dir()
            self.save_config()
            return

        try:
            with open(self.config_path, 'r') as f:
                user_config = json.load(f)
                # Update current hotkeys with user values, keeping defaults for missing keys
                self.hotkeys.update(user_config)
                logger.info(f"Loaded hotkey configuration from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load hotkey config: {e}. Using defaults.")

    def save_config(self) -> None:
        """Save current hotkey configuration to JSON file"""
        try:
            self._ensure_config_dir()
            with open(self.config_path, 'w') as f:
                json.dump(self.hotkeys, f, indent=4)
            logger.info(f"Saved hotkey configuration to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save hotkey config: {e}")

    def _ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists"""
        config_dir = os.path.dirname(self.config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)

    def get_hotkey(self, action: str) -> str:
        """Get the hotkey for a specific action"""
        return self.hotkeys.get(action, self.DEFAULT_HOTKEYS.get(action, ""))

    def set_hotkey(self, action: str, key: str) -> bool:
        """Update a hotkey and save to config"""
        if action in self.hotkeys:
            self.hotkeys[action] = key.lower()
            self.save_config()
            return True
        return False
