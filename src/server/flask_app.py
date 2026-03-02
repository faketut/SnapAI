import os
import logging
from flask import Flask, render_template

logger = logging.getLogger(__name__)


class FlaskApp:
    """Flask web application for serving mobile client"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        
        # Get the project root directory
        # This file is in src/server/flask_app.py
        # Web assets are now siblings in this directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        template_path = os.path.join(current_dir, 'templates')
        static_path = os.path.join(current_dir, 'static')
        
        logger.info(f"Server directory: {current_dir}")
        logger.info(f"Template path: {template_path}")
        logger.info(f"Template exists: {os.path.exists(template_path)}")
        
        # Initialize Flask app
        self.app = Flask(__name__,
                        template_folder=template_path,
                        static_folder=static_path)
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Setup Flask routes"""
        @self.app.route('/')
        def index():
            try:
                return render_template('mobile.html')
            except Exception as e:
                logger.error(f"Error rendering template: {e}")
                return f"Template error: {str(e)}", 500
        
        @self.app.route('/health')
        def health():
            return {'status': 'ok', 'service': 'SnapAI Mobile Client'}, 200
        
        @self.app.route('/network')
        def network_info():
            """Network information endpoint for debugging"""
            try:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                    s.connect(("8.8.8.8", 80))
                    local_ip = s.getsockname()[0]
                
                return {
                    'local_ip': local_ip,
                    'server_host': self.host,
                    'server_port': self.port,
                    'websocket_url': f'ws://{local_ip}:8765',
                    'http_url': f'http://{local_ip}:{self.port}',
                    'status': 'ok'
                }
            except Exception as e:
                return {'error': str(e), 'status': 'error'}, 500
    
    def run(self, debug_mode: bool = False) -> None:
        """Run Flask server with improved configuration"""
        logger.info(f"HTTP server running on http://{self.host}:{self.port}")
        
        # Get local IP for external access
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("8.8.8.8", 80))
                local_ip = s.getsockname()[0]
            logger.info(f"External access: http://{local_ip}:{self.port}")
        except Exception:
            logger.warning("Could not determine external IP address")
        
        try:
            self.app.run(
                host=self.host, 
                port=self.port, 
                debug=debug_mode, 
                threaded=True,
                use_reloader=debug_mode
            )
        except Exception as e:
            logger.error(f"Flask server error: {e}")
            raise
