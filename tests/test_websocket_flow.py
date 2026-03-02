import pytest
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from src.core.websocket_handler import WebSocketHandler

@pytest.mark.asyncio
async def test_websocket_handler_welcome():
    """Test WebSocketHandler sends welcome message upon connection"""
    handler = WebSocketHandler()
    mock_ws = AsyncMock()
    mock_ws.remote_address = ("127.0.0.1", 12345)
    
    # We need to simulate the async generator for messages
    mock_ws.__aiter__.return_value = []
    
    await handler.handle_client(mock_ws)
    
    # Check if welcome message was sent
    mock_ws.send.assert_called()
    welcome_msg = json.loads(mock_ws.send.call_args_list[0][0][0])
    assert welcome_msg['type'] == 'welcome'

@pytest.mark.asyncio
async def test_websocket_handler_ai_query(mock_gemini, env_setup):
    """Test WebSocketHandler processes ai_query command"""
    handler = WebSocketHandler()
    mock_ws = AsyncMock()
    mock_ws.remote_address = ("127.0.0.1", 12345)
    
    query_msg = json.dumps({
        "command": "ai_query",
        "question": "What's this?",
        "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
    })
    
    # Mock the ai_service to avoid real API calls (already mocked by mock_gemini)
    with patch.object(handler, '_broadcast_to_others', new_callable=AsyncMock) as mock_broadcast:
        await handler._process_message(mock_ws, query_msg)
        
        # Check if response was sent back to client
        mock_ws.send.assert_called()
        response = json.loads(mock_ws.send.call_args[0][0])
        assert response['type'] == 'ai_response'
        assert response['answer'] == "Mocked AI Response"
        
        # Check if response was broadcasted
        mock_broadcast.assert_called_once()

@pytest.mark.asyncio
async def test_websocket_handler_sync_request():
    """Test WebSocketHandler synchronization between clients"""
    handler = WebSocketHandler()
    handler.last_ai_response = {
        'answer': 'Previous response',
        'timestamp': '2023-01-01T00:00:00'
    }
    
    mock_ws = AsyncMock()
    sync_msg = json.dumps({"command": "sync_request"})
    
    await handler._process_message(mock_ws, sync_msg)
    
    # Check if sync response was sent
    mock_ws.send.assert_called()
    response = json.loads(mock_ws.send.call_args[0][0])
    assert response['type'] == 'sync_response'
    assert response['answer'] == 'Previous response'

@pytest.mark.asyncio
async def test_websocket_handler_screenshot_request():
    """Test WebSocketHandler screenshot request broadcasting"""
    handler = WebSocketHandler()
    mock_ws = AsyncMock()
    
    with patch.object(handler, '_broadcast_to_others', new_callable=AsyncMock) as mock_broadcast:
        screenshot_msg = json.dumps({"command": "screenshot_request"})
        await handler._process_message(mock_ws, screenshot_msg)
        
        # Check if screenshot request was broadcasted
        mock_broadcast.assert_called_once()
        broadcast_data = mock_broadcast.call_args[0][1]
        assert broadcast_data['type'] == 'screenshot_request'
