import asyncio
import base64
import json
import logging
import os
import threading
from datetime import datetime
from io import BytesIO
from typing import Set, Dict, Any, Optional

from PIL import ImageGrab
import google.generativeai as genai
import websockets
from flask import Flask, render_template, send_from_directory
from dotenv import load_dotenv

# Defaults and configuration constants
DEFAULT_HOST = '0.0.0.0'
DEFAULT_HTTP_PORT = 8080
DEFAULT_WS_PORT = 8765
WS_PING_INTERVAL_SEC = 20
WS_PING_TIMEOUT_SEC = 30

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class AIService:
    """Handles AI-related operations"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY found in environment")
        else:
            genai.configure(api_key=self.api_key)
    
    async def analyze_screenshot(self, image_data: str, question: str) -> str:
        """Analyze screenshot using Gemini API"""
        try:
            if not self.api_key:
                return "Error: Gemini API key not configured"
            
            # Decode base64 image
            img_bytes = base64.b64decode(image_data)
            
            # Create Gemini model and query
            model = genai.GenerativeModel('gemini-1.5-flash')
            prompt = f"Please analyze this screenshot and answer: {question}"
            
            response = model.generate_content([
                prompt,
                {"mime_type": "image/png", "data": img_bytes}
            ])
            return response.text
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return f"Analysis failed: {str(e)}"

    async def analyze_text(self, question: str) -> str:
        """Analyze text using Gemini API (text-only)"""
        try:
            if not self.api_key:
                return "Error: Gemini API key not configured"

            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content(question)
            return response.text
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return f"Analysis failed: {str(e)}"

class ScreenshotService:
    """Handles screenshot operations"""
    
    @staticmethod
    def capture() -> Optional[str]:
        """Capture screen and return base64 encoded PNG"""
        try:
            screenshot = ImageGrab.grab()
            with BytesIO() as buffer:
                screenshot.save(buffer, format='PNG')
                return base64.b64encode(buffer.getvalue()).decode('utf-8')
        except Exception as e:
            logger.error(f"Screenshot failed: {e}")
            return None

class WebSocketHandler:
    """Handles WebSocket connections and messages"""
    
    def __init__(self):
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.ai_service = AIService()
        
    async def handle_client(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Handle individual WebSocket client"""
        self.clients.add(websocket)
        client_id = id(websocket)
        logger.info(f"Client {client_id} connected")
        
        try:
            async for message in websocket:
                await self._process_message(websocket, message)
        except websockets.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            self.clients.remove(websocket)
    
    async def _process_message(self, websocket: websockets.WebSocketServerProtocol, 
                             message: str) -> None:
        """Process incoming WebSocket messages"""
        try:
            data = json.loads(message)
            command = data.get('command')
            
            if command == 'screenshot':
                await self._handle_screenshot(websocket)
            elif command == 'ai_query':
                await self._handle_ai_query(websocket, data)
            elif command == 'ai_query_text':
                await self._handle_ai_query_text(websocket, data)
            elif command == 'ping':
                await websocket.send(json.dumps({
                    'type': 'pong',
                    'timestamp': datetime.now().isoformat()
                }))
                
        except json.JSONDecodeError:
            await self._send_error(websocket, "Invalid JSON format")
        except Exception as e:
            await self._send_error(websocket, f"Error processing message: {str(e)}")
    
    async def _handle_screenshot(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """Handle screenshot capture request"""
        img_data = ScreenshotService.capture()
        if img_data:
            await websocket.send(json.dumps({
                'type': 'screenshot',
                'data': img_data,
                'timestamp': datetime.now().isoformat()
            }))
        else:
            await self._send_error(websocket, "Screenshot failed")
    
    async def _handle_ai_query(self, websocket: websockets.WebSocketServerProtocol, 
                             data: Dict[str, Any]) -> None:
        """Handle AI query request"""
        question = data.get('question', '')
        img_data = data.get('image_data')

        if img_data:
            answer = await self.ai_service.analyze_screenshot(img_data, question)
            await websocket.send(json.dumps({
                'type': 'ai_response',
                'answer': answer,
                'timestamp': datetime.now().isoformat()
            }))
        else:
            await self._send_error(websocket, "No image provided")

    async def _handle_ai_query_text(self, websocket: websockets.WebSocketServerProtocol, 
                                 data: Dict[str, Any]) -> None:
        """Handle text-only AI query request"""
        question = data.get('question', '')
        answer = await self.ai_service.analyze_text(question)
        await websocket.send(json.dumps({
            'type': 'ai_response',
            'answer': answer,
            'timestamp': datetime.now().isoformat()
        }))
    
    @staticmethod
    async def _send_error(websocket: websockets.WebSocketServerProtocol, 
                         message: str) -> None:
        """Send error message to client"""
        await websocket.send(json.dumps({
            'type': 'error',
            'message': message,
            'timestamp': datetime.now().isoformat()
        }))

    #

class Server:
    """Main server class combining Flask and WebSocket servers"""
    
    def __init__(self, host: str = DEFAULT_HOST, 
                 http_port: int = DEFAULT_HTTP_PORT, 
                 ws_port: int = DEFAULT_WS_PORT):
        self.host = host
        self.http_port = http_port
        self.ws_port = ws_port
        
        # Initialize Flask app
        self.app = Flask(__name__,
                        template_folder='templates',
                        static_folder='static')
        self._setup_routes()
        
        # Initialize WebSocket handler
        self.ws_handler = WebSocketHandler()
    
    def _setup_routes(self) -> None:
        """Setup Flask routes"""
        @self.app.route('/')
        def index():
            return render_template('mobile.html')
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            return send_from_directory('static', filename)
    
    async def run_websocket_server(self) -> None:
        """Run WebSocket server"""
        async with websockets.serve(
            self.ws_handler.handle_client,
            self.host,
            self.ws_port,
            ping_interval=WS_PING_INTERVAL_SEC,
            ping_timeout=WS_PING_TIMEOUT_SEC
        ) as server:
            logger.info(f"WebSocket server running on ws://{self.host}:{self.ws_port}")
            await server.wait_closed()
    
    def run(self) -> None:
        """Run both Flask and WebSocket servers"""
        # Ensure directories exist
        os.makedirs('templates', exist_ok=True)
        os.makedirs('static', exist_ok=True)

        # Start WebSocket server in a separate thread
        loop = asyncio.new_event_loop()
        websocket_thread = threading.Thread(
            target=lambda: loop.run_until_complete(self.run_websocket_server()),
            daemon=True
        )
        websocket_thread.start()
        
        # Start Flask server
        logger.info(f"HTTP server running on http://{self.host}:{self.http_port}")
        self.app.run(host=self.host, port=self.http_port, debug=False)

if __name__ == "__main__":
    server = Server()
    server.run()