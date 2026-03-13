import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any

import websockets

from .ai_service import AIService

logger = logging.getLogger(__name__)


class WebSocketHandler:
    """Handles WebSocket connections and messages"""
    
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.ai_service = AIService()
        # All websocket handlers run on the websocket server's event loop thread,
        # so an asyncio.Lock is the safest way to prevent concurrent mutation.
        self._clients_lock = asyncio.Lock()
        self.last_ai_response = None  # Store last AI response for sync
        
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Handle individual WebSocket client with improved error handling"""
        # Never await while holding a cross-coroutine lock.
        should_reject = False
        async with self._clients_lock:
            if len(self.clients) >= 50:  # MAX_CLIENTS
                should_reject = True
            else:
                self.clients.add(websocket)
        if should_reject:
            logger.warning("Max clients (50) reached, rejecting connection")
            try:
                await websocket.close(code=1013, reason="Server overloaded")
            except Exception:
                pass
            return
        
        client_id = id(websocket)
        try:
            client_ip = websocket.remote_address[0] if websocket.remote_address else "unknown"
        except Exception:
            client_ip = "unknown"
        logger.info(f"Client {client_id} connected from {client_ip} (total: {len(self.clients)})")
        
        try:
            # Send welcome message
            try:
                await websocket.send(json.dumps({
                    'type': 'welcome',
                    'message': 'Connected to SnapAI server',
                    'timestamp': datetime.now().isoformat()
                }))
            except websockets.ConnectionClosed:
                return
            
            async for message in websocket:
                try:
                    await self._process_message(websocket, message)
                except Exception as e:
                    logger.error(f"Error processing message from client {client_id}: {e}")
                    await self._send_error(websocket, f"Message processing error: {str(e)}")
                    
        except websockets.ConnectionClosed as e:
            logger.info(f"Client {client_id} disconnected: {e.code} - {e.reason}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            async with self._clients_lock:
                self.clients.discard(websocket)
            logger.info(f"Client {client_id} removed (total: {len(self.clients)})")
    
    async def _process_message(self, websocket: websockets.WebSocketServerProtocol, 
                             message: str) -> None:
        """Process incoming WebSocket messages"""
        try:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'ai_query':
                await self._handle_ai_query(websocket, data)
            elif command == 'ai_query_text':
                await self._handle_ai_query_text(websocket, data)
            elif command == 'sync_request':
                await self._handle_sync_request(websocket, data)
            elif command == 'screenshot_request':
                await self._handle_screenshot_request(websocket)
            elif command == 'ping':
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
            else:
                await self._send_error(websocket, f"Unknown command: {command}")
                
        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON format")
        except Exception as e:
            await self._send_error(websocket, f"Error processing message: {str(e)}")
    
    async def _handle_ai_query(self, websocket: websockets.WebSocketServerProtocol, 
                             data: Dict[str, Any]) -> None:
        """Handle AI query request with image data"""
        question = data.get('question', '')
        img_data = data.get('image_data')

        if not img_data:
            await self._send_error(websocket, "No image provided")
            return

        answer = await self.ai_service.analyze_screenshot(img_data, question)
        response = {
            'type': 'ai_response',
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store the response for sync purposes (before sending)
        self.last_ai_response = response
        logger.info(f"Stored AI response for sync: {response['answer'][:50]}...")
        
        # Send to requesting client and broadcast to others
        await websocket.send(json.dumps(response))
        await self._broadcast_to_others(websocket, response)

    async def _handle_ai_query_text(self, websocket: websockets.WebSocketServerProtocol, 
                                 data: Dict[str, Any]) -> None:
        """Handle text-only AI query request"""
        question = data.get('question', '')
        answer = await self.ai_service.analyze_text(question)
        response = {
            'type': 'ai_response',
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        }
        
        # Store the response for sync purposes (before sending)
        self.last_ai_response = response
        logger.info(f"Stored AI response for sync: {response['answer'][:50]}...")
        
        # Send to requesting client and broadcast to others
        await websocket.send(json.dumps(response))
        await self._broadcast_to_others(websocket, response)
    
    async def _handle_sync_request(self, websocket: websockets.WebSocketServerProtocol, 
                                 data: Dict[str, Any]) -> None:
        """Handle sync request from mobile client"""
        logger.info(f"Sync request from client {id(websocket)}, last response: {self.last_ai_response is not None}")
        
        if self.last_ai_response and self.last_ai_response.get('answer'):
            # Send the last AI response as a sync response
            sync_response = {
                'type': 'sync_response',
                'answer': self.last_ai_response['answer'],
                'timestamp': self.last_ai_response['timestamp']
            }
            await websocket.send(json.dumps(sync_response))
            logger.info(f"Sent sync response to client {id(websocket)}: {self.last_ai_response['answer'][:50]}...")
        else:
            # No previous response available
            sync_response = {
                'type': 'sync_response',
                'answer': '',
                'timestamp': datetime.now().isoformat()
            }
            await websocket.send(json.dumps(sync_response))
            logger.info(f"No previous response to sync for client {id(websocket)}")

    async def _handle_screenshot_request(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Handle request from mobile to trigger screenshot on desktop"""
        logger.info(f"Screenshot request from client {id(websocket)}")
        # Broadcast the request so the desktop overlay receives it
        await self._broadcast_to_others(websocket, {
            'type': 'screenshot_request',
            'timestamp': datetime.now().isoformat()
        })
    
    async def _broadcast_to_others(self, sender: websockets.WebSocketServerProtocol, 
                                  message: dict) -> None:
        """Broadcast message to all clients except sender"""
        async with self._clients_lock:
            if not self.clients:
                return
            clients_to_broadcast = [c for c in self.clients if c != sender]
        
        if not clients_to_broadcast:
            return
        
        message_json = json.dumps(message)
        disconnected = set()
        
        # Concurrent broadcasting
        async def send_to_client(client):
            try:
                await client.send(message_json)
                return None
            except websockets.ConnectionClosed:
                return client
            except Exception as e:
                logger.error(f"Broadcast error to client {id(client)}: {e}")
                return client
        
        # Send to all clients concurrently
        results = await asyncio.gather(*[send_to_client(client) for client in clients_to_broadcast], 
                                     return_exceptions=True)
        
        # Collect disconnected clients
        for result in results:
            if result and not isinstance(result, Exception):
                disconnected.add(result)
        
        # Remove disconnected clients
        if disconnected:
            async with self._clients_lock:
                self.clients -= disconnected

    @staticmethod
    async def _send_error(websocket: websockets.WebSocketServerProtocol, 
                         message: str) -> None:
        """Send error message to client"""
        try:
            await websocket.send(json.dumps({
                'type': 'error',
                'message': message,
                'timestamp': datetime.now().isoformat()
            }))
        except websockets.ConnectionClosed:
            return
        except Exception:
            return
