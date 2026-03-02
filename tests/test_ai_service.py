import pytest
from unittest.mock import MagicMock, patch
from src.core.ai_service import AIService

@pytest.mark.asyncio
async def test_ai_service_analyze_text(mock_gemini, env_setup):
    """Test AIService text analysis"""
    service = AIService()
    answer = await service.analyze_text("Test question")
    assert answer == "Mocked AI Response"
    mock_gemini.return_value.generate_content.assert_called_once_with("Test question")

@pytest.mark.asyncio
async def test_ai_service_analyze_screenshot(mock_gemini, env_setup):
    """Test AIService screenshot analysis"""
    service = AIService()
    # Mock raw base64 image data (no prefix)
    img_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    answer = await service.analyze_screenshot(img_data, "What's on this screen?")
    assert answer == "Mocked AI Response"
    # Ensure generate_content was called with image data
    args, kwargs = mock_gemini.return_value.generate_content.call_args
    assert isinstance(args[0], list)
    assert any(isinstance(item, dict) and 'mime_type' in item for item in args[0])

@pytest.mark.asyncio
async def test_ai_service_error_handling(mock_gemini, env_setup):
    """Test AIService error handling during analysis"""
    mock_gemini.return_value.generate_content.side_effect = Exception("API error")
    service = AIService()
    answer = await service.analyze_text("Test question")
    assert "Analysis failed" in answer
