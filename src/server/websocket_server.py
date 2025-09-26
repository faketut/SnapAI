import asyncio
import logging
import threading

import websockets

from ..core.websocket_handler import WebSocketHandler

logger = logging.getLogger(__name__)


class WebSocketServer:
    """WebSocket server for real-time communication"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8765):
        self.host = host
        self.port = port
        self.ws_handler = WebSocketHandler()
        self.loop = None
        self.thread = None
    
    async def run_websocket_server(self) -> None:
        """Run WebSocket server with improved configuration"""
        async with websockets.serve(
            self.ws_handler.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10,
            max_size=10 * 1024 * 1024,
            compression=None,
            close_timeout=5,
            read_limit=2**20,  # 1MB read limit
            write_limit=2**20  # 1MB write limit
        ) as server:
            logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")
            logger.info(f"Max clients: 50, Max message size: 10MB, Ping interval: 20s")
            await server.wait_closed()
    
    def start(self) -> None:
        """Start WebSocket server in a separate thread"""
        try:
            self.loop = asyncio.new_event_loop()
            self.thread = threading.Thread(
                target=self._run_websocket_loop,
                daemon=True,
                name="WebSocketServer"
            )
            self.thread.start()
        except Exception as e:
            logger.error(f"Failed to start WebSocket server: {e}")
            # Try alternative port
            if self.port == 8765:
                self.port = 8766
                logger.info(f"Trying alternative port: {self.port}")
                self.start()
    
    def _run_websocket_loop(self) -> None:
        """Run WebSocket server in event loop"""
        try:
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.run_websocket_server())
        except OSError as e:
            if e.errno == 10048:  # Port already in use
                logger.warning(f"Port {self.port} is already in use, WebSocket server not started")
            else:
                logger.error(f"WebSocket server error: {e}")
        except Exception as e:
            logger.error(f"WebSocket server error: {e}")
        finally:
            if not self.loop.is_closed():
                self.loop.close()
    
    def stop(self) -> None:
        """Stop WebSocket server"""
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
