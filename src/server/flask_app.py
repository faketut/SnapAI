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
        # We need to go up 2 levels to get to the project root
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        
        template_path = os.path.join(project_root, 'templates')
        static_path = os.path.join(project_root, 'static')
        
        logger.info(f"Project root: {project_root}")
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
    
    def run(self, debug_mode: bool = False) -> None:
        """Run Flask server with improved configuration"""
        logger.info(f"HTTP server running on http://{self.host}:{self.port}")
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
