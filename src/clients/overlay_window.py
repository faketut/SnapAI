import base64
from io import BytesIO
from typing import Optional

import keyboard
import numpy as np
from PIL import ImageGrab

from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QScrollArea, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QBuffer, QIODevice
from PyQt5.QtGui import QFont, QImage, QIcon

from .websocket_client import WebSocketClient
from ..core.hotkey_manager import HotkeyManager
from .hotkey_dialog import HotkeyConfigDialog

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
            self.hotkey_manager = HotkeyManager()
            self._setup_tray()
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
        self.setWindowTitle("SnapAI")
        self.setFixedSize(600, 400)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(0.9)
        self.setFocusPolicy(Qt.StrongFocus)

        # Main background widget
        self.central_widget = QLabel(self)
        self.central_widget.setGeometry(0, 0, 600, 400)
        self.central_widget.setStyleSheet("""
            background-color: rgba(13, 17, 23, 230);
            border: 1px solid #30363d;
            border-radius: 12px;
        """)

        # Scroll area and label
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setGeometry(15, 15, 570, 370)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                border: none;
                background: transparent;
                width: 6px;
                margin: 0px;
            }
            QScrollBar::handle:vertical {
                background: #30363d;
                min-height: 20px;
                border-radius: 3px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)

        self.label = QLabel()
        self.label.setText("INITIALIZING...")
        self.label.setFont(QFont("Arial", 11, QFont.Medium))
        self.label.setStyleSheet("""
            color: #f0f6fc;
            background: transparent;
            padding: 5px;
            line-height: 1.5;
        """)
        self.label.setWordWrap(True)
        self.label.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        # We don't need setFixedWidth here because setWidgetResizable(True) is used

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

    def _setup_tray(self) -> None:
        """Initialize system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use a default icon or a specific one if available
        # For now, we'll try to use the mockup or a fallback
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "snap_ai_minimalist_ui_mockup.png")
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
        else:
            self.tray_icon.setIcon(self.style().standardIcon(self.style().SP_ComputerIcon))
        
        tray_menu = QMenu()
        
        show_action = QAction("Show Overlay", self)
        show_action.triggered.connect(self.show)
        
        hide_action = QAction("Hide Overlay", self)
        hide_action.triggered.connect(self.hide)
        
        config_action = QAction("Configure Hotkeys", self)
        config_action.triggered.connect(self.open_hotkey_config)
        
        quit_action = QAction("Quit SnapAI", self)
        quit_action.triggered.connect(QApplication.instance().quit)
        
        tray_menu.addAction(show_action)
        tray_menu.addAction(hide_action)
        tray_menu.addSeparator()
        tray_menu.addAction(config_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
        # Double click to show/hide
        self.tray_icon.activated.connect(self._on_tray_activated)

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            if self.isVisible():
                self.hide()
            else:
                self.show()

    def open_hotkey_config(self) -> None:
        """Open the hotkey configuration dialog"""
        dialog = HotkeyConfigDialog(self.hotkey_manager, self)
        if dialog.exec_() == HotkeyConfigDialog.Accepted:
            new_hotkeys = dialog.get_configured_hotkeys()
            for action, key in new_hotkeys.items():
                self.hotkey_manager.set_hotkey(action, key)
            
            # Reload hotkeys instantly
            self.reload_hotkeys()

    def reload_hotkeys(self) -> None:
        """Unregister old hotkeys and register new ones"""
        try:
            keyboard.unhook_all()
            self._setup_hotkeys()
            self.update_answer("Hotkeys updated successfully!")
        except Exception as e:
            self.update_answer(f"Failed to reload hotkeys: {str(e)}")

    def _setup_hotkeys(self) -> None:
        """Setup global hotkeys for overlay controls"""
        capture_key = self.hotkey_manager.get_hotkey("capture_screenshot")
        clipboard_key = self.hotkey_manager.get_hotkey("process_clipboard")
        show_key = self.hotkey_manager.get_hotkey("show_overlay")
        hide_key = self.hotkey_manager.get_hotkey("hide_overlay")

        if capture_key:
            keyboard.add_hotkey(capture_key, self.capture_and_send_screenshot)
        if clipboard_key:
            keyboard.add_hotkey(clipboard_key, self.send_clipboard_to_server)
        if show_key:
            keyboard.add_hotkey(show_key, self.show)
        if hide_key:
            keyboard.add_hotkey(hide_key, self.hide)

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
