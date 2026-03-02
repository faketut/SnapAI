import pytest
import os
import json
from src.core.hotkey_manager import HotkeyManager

def test_hotkey_manager_default():
    """Test HotkeyManager with default hotkeys"""
    manager = HotkeyManager(config_path="/non/existent/path.json")
    assert manager.get_hotkey("capture_screenshot") == "f7"
    assert manager.get_hotkey("process_clipboard") == "f8"
    assert manager.get_hotkey("show_overlay") == "f9"
    assert manager.get_hotkey("hide_overlay") == "f10"

def test_hotkey_manager_load(temp_config):
    """Test HotkeyManager loading from file"""
    manager = HotkeyManager(config_path=temp_config)
    assert manager.get_hotkey("capture_screenshot") == "ctrl+f7"
    assert manager.get_hotkey("process_clipboard") == "ctrl+f8"

def test_hotkey_manager_set_and_save(temp_config):
    """Test HotkeyManager setting and saving hotkeys"""
    manager = HotkeyManager(config_path=temp_config)
    manager.set_hotkey("capture_screenshot", "alt+f1")
    assert manager.get_hotkey("capture_screenshot") == "alt+f1"
    
    # Verify file was updated
    with open(temp_config, 'r') as f:
        data = json.load(f)
        assert data["capture_screenshot"] == "alt+f1"

def test_hotkey_manager_invalid_action():
    """Test HotkeyManager with invalid action"""
    manager = HotkeyManager()
    assert manager.get_hotkey("invalid_action") == ""
