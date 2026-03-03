import os
import logging
from typing import Optional
from flask import Flask, render_template

logger = logging.getLogger(__name__)


class FlaskApp:
    """Flask web application for serving mobile client and receiving remote commands"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8080):
        self.host = host
        self.port = port
        
        # Paths for assets
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, 'templates')
        static_path = os.path.join(current_dir, 'static')
        
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

    def run(self, debug_mode: bool = False, ssl_context: Optional[str] = None) -> None:
        """Run Flask server"""
        protocol = "https" if ssl_context else "http"
        logger.info(f"HTTP server running on {protocol}://{self.host}:{self.port}")
        
        try:
            self.app.run(
                host=self.host, 
                port=self.port, 
                debug=debug_mode, 
                threaded=True,
                use_reloader=False, # Reloader doesn't play well with Threading
                ssl_context=ssl_context
            )
        except Exception as e:
            logger.error(f"Flask server error: {e}")
            raise
