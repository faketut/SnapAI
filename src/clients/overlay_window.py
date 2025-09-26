import base64
from io import BytesIO
from typing import Optional

import keyboard
import numpy as np
from PIL import ImageGrab

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QBuffer, QIODevice
from PyQt5.QtGui import QFont, QImage

from .websocket_client import WebSocketClient

PROMPT_PREFIX = "use code to solve: "


class OverlayWindow(QMainWindow):
    """Floating overlay window for displaying AI responses"""
    
    answer_signal = pyqtSignal(str)
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OverlayWindow, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            super().__init__()
            self._setup_ui()
            self._setup_websocket()
            self._setup_hotkeys()
            OverlayWindow._initialized = True
        else:
            # If already initialized, just show the existing window
            self.show()
            self.raise_()
            self.activateWindow()
    
    def _setup_ui(self) -> None:
        """Initialize UI components"""
        # Window properties
        self.setWindowTitle("AI Assistant")
        self.setFixedSize(651, 413)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.7)
        self.setFocusPolicy(Qt.StrongFocus)

        # Scroll area and label
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setGeometry(10, 10, 631, 393)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background: transparent; border: none;")

        self.label = QLabel()
        self.label.setText("Waiting...")
        self.label.setFont(QFont("Times New Roman", 12))
        self.label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 150); border-radius: 10px;")
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.label.setFixedWidth(611)

        self.scroll_area.setWidget(self.label)

        # Drag handling
        self.old_pos = None

        # Signal connection
        self.answer_signal.connect(self.update_answer)

    def update_answer(self, text: str) -> None:
        """Update the display with new answer text"""
        self.label.setText(text)
        self.scroll_area.verticalScrollBar().setValue(0)

    def mousePressEvent(self, event) -> None:
        """Handle mouse press for dragging"""
        if event.button() == Qt.LeftButton:
            self.old_pos = event.globalPos()

    def mouseMoveEvent(self, event) -> None:
        """Handle mouse move for dragging"""
        if self.old_pos is not None:
            delta = event.globalPos() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPos()

    def mouseReleaseEvent(self, event) -> None:
        """Handle mouse release"""
        self.old_pos = None

    def scroll_up(self) -> None:
        """Scroll content up"""
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.value() - 30)

    def scroll_down(self) -> None:
        """Scroll content down"""
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.value() + 30)

    def _setup_websocket(self) -> None:
        """Initialize WebSocket client and start it"""
        self.ws_client = WebSocketClient(self.answer_signal.emit)
        self.ws_client.start()

    def _setup_hotkeys(self) -> None:
        """Setup global hotkeys for overlay controls"""
        keyboard.add_hotkey('f7', self.capture_and_send_screenshot)
        keyboard.add_hotkey('f8', self.send_clipboard_to_server)
        keyboard.add_hotkey('f9', self.show)
        keyboard.add_hotkey('f10', self.hide)

    def send_clipboard_to_server(self) -> None:
        """Read clipboard text or image and send to server"""
        if not hasattr(self, 'ws_client') or not self.ws_client:
            return

        clipboard = QApplication.clipboard()
        mime = clipboard.mimeData()

        has_text = mime.hasText()
        has_image = mime.hasImage()

        if has_image and not has_text:
            qimage = clipboard.image()
            if qimage.isNull():
                return
            
            # Convert QImage to base64
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            qimage.save(buffer, 'PNG')
            image_bytes = bytes(buffer.data())
            image_b64 = base64.b64encode(image_bytes).decode('utf-8')
            
            payload = {
                "command": "ai_query",
                "question": PROMPT_PREFIX,
                "image_data": image_b64
            }
            self.ws_client.send_message(payload)
        else:
            # Send text query
            text = mime.text() if has_text else ""
            self.ws_client.send_question(f"{PROMPT_PREFIX}{text}".strip())

    def capture_and_send_screenshot(self) -> None:
        """Take a screenshot, copy to clipboard, and send to server"""
        if not hasattr(self, 'ws_client') or not self.ws_client:
            return

        try:
            # Capture screenshot
            screenshot = ImageGrab.grab()
            
            # Convert to base64
            with BytesIO() as buffer:
                screenshot.save(buffer, format='PNG')
                image_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Copy to clipboard
            clipboard = QApplication.clipboard()
            img_array = np.array(screenshot)
            h, w, ch = img_array.shape
            bytes_per_line = ch * w
            qimage = QImage(img_array.data, w, h, bytes_per_line, QImage.Format_RGB888)
            clipboard.setImage(qimage)
            
            # Send to server
            payload = {
                "command": "ai_query",
                "question": "analyze the screenshot and answer: ",
                "image_data": image_b64
            }
            self.ws_client.send_message(payload)
                
        except Exception as e:
            self.ws_client.callback(f"Failed to capture screenshot: {str(e)}")
