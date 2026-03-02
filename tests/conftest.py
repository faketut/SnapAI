import pytest
import os
import json
import tempfile
from unittest.mock import MagicMock, patch

@pytest.fixture
def mock_gemini():
    """Mock Google Gemini API"""
    with patch('google.generativeai.GenerativeModel') as mock_model:
        mock_instance = MagicMock()
        mock_model.return_value = mock_instance
        
        # Mock response
        mock_response = MagicMock()
        mock_response.text = "Mocked AI Response"
        mock_instance.generate_content.return_value = mock_response
        
        yield mock_model

@pytest.fixture
def temp_config():
    """Create a temporary hotkeys.json file"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config = {
            "capture_screenshot": "ctrl+f7",
            "process_clipboard": "ctrl+f8",
            "show_overlay": "ctrl+f9",
            "hide_overlay": "ctrl+f10"
        }
        json.dump(config, f)
        temp_path = f.name
    
    yield temp_path
    
    if os.path.exists(temp_path):
        os.remove(temp_path)

@pytest.fixture
def env_setup():
    """Setup basic environment variables for testing"""
    os.environ['GOOGLE_API_KEY'] = 'test-key'
    yield
    if 'GOOGLE_API_KEY' in os.environ:
        del os.environ['GOOGLE_API_KEY']
