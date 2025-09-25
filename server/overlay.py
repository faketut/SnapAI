import sys
import asyncio
import threading
import json
from typing import Optional
import websockets
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, 
    QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QBuffer, QIODevice
from PyQt5.QtGui import QFont
import keyboard

PROMPT_PREFIX = "use code to solve: "

class OverlayWindow(QMainWindow):
    """Floating overlay window for displaying AI responses"""
    
    answer_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._setup_ui()
        self._setup_websocket()
        self._setup_hotkeys()
    
    def _setup_ui(self) -> None:
        """Initialize UI components"""
        # Window properties
        self.setWindowTitle("AI Assistant")
        self.setFixedSize(651, 413)  # 500+151 x 300+113
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.7)
        self.setFocusPolicy(Qt.StrongFocus)

        # 滚动区域和标签
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setGeometry(10, 10, 480 + 151, 280 + 113)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.label = QLabel()
        self.label.setText("Waiting...")
        self.label.setFont(QFont("Times New Roman", 12))
        self.label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 150); border-radius: 10px;")
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.label.setFixedWidth(460 + 151)

        self.scroll_area.setWidget(self.label)

        # 拖动相关
        self.old_pos = None

        # 信号连接
        self.answer_signal.connect(self.update_answer)

    def update_answer(self, text):
        self.label.setText(text)
        # 滚动到顶部
        self.scroll_area.verticalScrollBar().setValue(0)

    # 鼠标拖动
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.old_pos is not None:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.old_pos = None

    # 滚动相关
    def scroll_up(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.value() - 30)

    def scroll_down(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.value() + 30)

    def _setup_websocket(self) -> None:
        """Initialize WebSocket client and start it"""
        self.ws_client = WebSocketClient(self.answer_signal.emit)
        self.ws_client.start()

    def _setup_hotkeys(self) -> None:
        """Setup global hotkeys for overlay controls"""
        keyboard.add_hotkey('f8', self.send_clipboard_to_server)
        keyboard.add_hotkey('f9', self.scroll_up)
        keyboard.add_hotkey('f10', self.scroll_down)
        keyboard.add_hotkey('f11', self.show)
        keyboard.add_hotkey('f12', self.hide)

    def send_clipboard_to_server(self) -> None:
        """Read clipboard text or image and send only that modality to server"""
        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        has_text = mime.hasText()
        has_image = mime.hasImage()

        if has_image and not has_text:
            qimage = clipboard.image()
            if qimage.isNull():
                return
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            qimage.save(buffer, 'PNG')
            image_bytes = bytes(buffer.data())
            import base64
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            payload = {
                "command": "ai_query",
                "question": PROMPT_PREFIX,
                "image_data": image_b64
            }
        else:
            # Default to text-only when text exists or neither clearly present
            text = mime.text() if has_text else ""
            if hasattr(self, 'ws_client') and self.ws_client:
                self.ws_client.send_question(f"{PROMPT_PREFIX}{text}".strip())
            return

        if hasattr(self, 'ws_client') and self.ws_client:
            self.ws_client.send_message(payload)

class WebSocketClient(QObject):
    """WebSocket client for handling server communication"""
    
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
        
    def stop(self):
        self.should_reconnect = False
        if self.ws:
            asyncio.run_coroutine_threadsafe(self.ws.close(), self.loop)

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.listen())

    async def listen(self):
        while self.should_reconnect:
            try:
                async with websockets.connect(
                    self.ws_url,
                    ping_interval=20,
                    ping_timeout=60,
                    close_timeout=10
                ) as ws:
                    self.ws = ws
                    self.connected = True
                    self.reconnect_delay = 1
                    if self.callback:
                        self.callback("Successfully connected to server")
                    
                    while True:
                        try:
                            msg = await ws.recv()
                            data = json.loads(msg)
                            if data.get("type") == "ai_response":
                                answer = data.get("answer", "No answer")
                                if self.callback:
                                    self.callback(answer)
                            elif data.get("type") == "error":
                                if self.callback:
                                    self.callback(f"Server error: {data.get('message', 'Unknown error')}")
                        except websockets.ConnectionClosed:
                            if not self.should_reconnect:
                                return
                            raise
                        except json.JSONDecodeError:
                            if self.callback:
                                self.callback("Received invalid message format")
                        except Exception as e:
                            if self.callback:
                                self.callback(f"Error processing message: {str(e)}")
                            
            except (websockets.ConnectionClosed, ConnectionRefusedError):
                if not self.should_reconnect:
                    return
                self.connected = False
                self.ws = None
                if self.callback:
                    self.callback(f"Connection lost. Retrying in {self.reconnect_delay} seconds...")
                await asyncio.sleep(self.reconnect_delay)
                self.reconnect_delay = min(self.reconnect_delay * 2, self.max_reconnect_delay)
            except Exception as e:
                if not self.should_reconnect:
                    return
                self.connected = False
                self.ws = None
                if self.callback:
                    self.callback(f"Connection error: {str(e)}")
                await asyncio.sleep(self.reconnect_delay)

    def send_message(self, payload: dict) -> None:
        if self.loop and self.ws:
            asyncio.run_coroutine_threadsafe(
                self.ws.send(json.dumps(payload)),
                self.loop
            )

    def send_question(self, question: str) -> None:
        self.send_message({"command": "ai_query_text", "question": question})

def main():
    app = QApplication(sys.argv)
    window = OverlayWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()