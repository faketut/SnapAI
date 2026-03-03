import asyncio
import json
import threading
from typing import Optional

import websockets

from PyQt5.QtCore import QObject, pyqtSignal


class WebSocketClient(QObject):
    """WebSocket client for handling server communication"""
    screenshot_signal = pyqtSignal()
    
    def __init__(self, callback, ws_url: str = "ws://localhost:8765"):
        super().__init__()
        self.callback = callback
        self.ws_url = ws_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.connected = False
        self.should_reconnect = True
        self.reconnect_delay = 1
        self.max_reconnect_delay = 30
        self._shutdown = False
        self._thread = None
        
    def stop(self):
        """Stop the WebSocket client gracefully"""
        self._shutdown = True
        self.should_reconnect = False
        if self.ws and self.loop:
            try:
                asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)
            except Exception as e:
                print(f"Error closing WebSocket: {e}")
        if self.loop and not self.loop.is_closed():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)

    def start(self):
        """Start the WebSocket client in a separate thread"""
        if self._thread and self._thread.is_alive():
            return
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self):
        """Run the asyncio event loop"""
        try:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self.listen())
        except Exception as e:
            print(f"WebSocket client error: {e}")
        finally:
            if self.loop and not self.loop.is_closed():
                self.loop.close()

    async def listen(self):
        """Main WebSocket listening loop"""
        while self.should_reconnect and not self._shutdown:
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=5,
                    max_size=10 * 1024 * 1024,
                    compression=None
                ) as ws:
                    self.ws = ws
                    self.connected = True
                    self.reconnect_delay = 1
                    if self.callback:
                        self.callback("Successfully connected to server")
                    
                    while self.should_reconnect and not self._shutdown:
                        try:
                            msg = await asyncio.wait_for(ws.recv(), timeout=60.0)
                            data = json.loads(msg)
                            
                            if data.get("type") == "ai_response":
                                answer = data.get("answer", "No answer")
                                if self.callback:
                                    self.callback(answer)
                            elif data.get("type") == "screenshot_request":
                                self.screenshot_signal.emit()
                            elif data.get("type") == "error":
                                if self.callback:
                                    self.callback(f"Server error: {data.get('message', 'Unknown error')}")
                                    
                        except asyncio.TimeoutError:
                            try:
                                await ws.ping()
                            except:
                                break
                        except websockets.ConnectionClosed:
                            if not self.should_reconnect or self._shutdown:
                                return
                            raise
                        except json.JSONDecodeError:
                            if self.callback:
                                self.callback("Received invalid message format")
                        except Exception as e:
                            if self.callback:
                                self.callback(f"Error processing message: {str(e)}")
                            
            except (websockets.ConnectionClosed, ConnectionRefusedError):
                if not self.should_reconnect or self._shutdown:
                    return
                self.connected = False
                self.ws = None
                if self.callback:
                    self.callback(f"Connection lost. Retrying in {self.reconnect_delay} seconds...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
            except Exception as e:
                if not self.should_reconnect or self._shutdown:
                    return
                self.connected = False
                self.ws = None
                if self.callback:
                    self.callback(f"Connection error: {str(e)}")
                await asyncio.sleep(self.reconnect_delay)

    def send_message(self, payload: dict) -> None:
        """Send message to server"""
        if not self.connected or not self.loop or not self.ws:
            if self.callback:
                self.callback("Not connected to server")
            return
            
        try:
            asyncio.run_coroutine_threadsafe(
                self.ws.send(json.dumps(payload)),
                self.loop
            )
        except Exception as e:
            if self.callback:
                self.callback(f"Failed to send message: {str(e)}")

    def send_question(self, question: str) -> None:
        """Send text question to server"""
        self.send_message({"command": "ai_query_text", "question": question})
