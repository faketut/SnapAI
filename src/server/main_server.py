import logging

from .websocket_server import WebSocketServer
from .flask_app import FlaskApp

logger = logging.getLogger(__name__)


class MainServer:
    """Main server combining WebSocket and Flask for local/mobile usage"""
    
    def __init__(self, host: str = '0.0.0.0', 
                 ws_port: int = 8765,
                 http_port: int = 8080,
                 use_https: bool = False):
        self.host = host
        self.ws_port = ws_port
        self.http_port = http_port
        self.use_https = use_https
        
        # Initialize servers
        self.ws_server = WebSocketServer(host, ws_port)
        self.flask_app = FlaskApp(host, http_port)
    
    def run(self) -> None:
        """Run both servers"""
        # Start WebSocket server (non-blocking thread)
        logger.info("Starting WebSocket server...")
        self.ws_server.start()
        
        # Start Flask server (blocking)
        logger.info("Starting Flask server...")
        ssl_context = 'adhoc' if self.use_https else None
        self.flask_app.run(ssl_context=ssl_context)
    
    def stop(self) -> None:
        """Stop the server"""
        self.ws_server.stop()
