import os
import logging
import threading

from .flask_app import FlaskApp
from .websocket_server import WebSocketServer
from ..utils.file_watcher import HotReloadManager

logger = logging.getLogger(__name__)


class MainServer:
    """Main server combining Flask and WebSocket servers"""
    
    def __init__(self, host: str = '0.0.0.0', 
                 http_port: int = 8080, 
                 ws_port: int = 8765,
                 debug_mode: bool = False):
        self.host = host
        self.http_port = http_port
        self.ws_port = ws_port
        self.debug_mode = debug_mode
        
        # Initialize servers
        self.flask_app = FlaskApp(host, http_port)
        self.ws_server = WebSocketServer(host, ws_port)
        
        # Initialize hot reload manager
        self.hot_reload = HotReloadManager(self)
    
    def run(self) -> None:
        """Run both Flask and WebSocket servers"""
        # Ensure directories exist
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static', exist_ok=True)

        # Start hot reload manager
        self.hot_reload.start()

        # Start WebSocket server
        self.ws_server.start()
        
        # Start Flask server (blocking)
        self.flask_app.run(debug_mode=self.debug_mode)
    
    def stop(self) -> None:
        """Stop all servers"""
        self.hot_reload.stop()
        self.ws_server.stop()
