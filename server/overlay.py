import sys
import asyncio
import threading
import json
import websockets
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QInputDialog, QScrollArea, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, pyqtSignal, QObject
from PyQt5.QtGui import QFont
import keyboard  # 全局热键支持

class OverlayWindow(QMainWindow):
    answer_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        # 固定窗口属性
        self.setWindowTitle("AI回答窗口")
        # 增加宽4cm（约151px），高3cm（约113px）
        self.setFixedSize(500 + 151, 300 + 113)
        self.setWindowOpacity(0.7)
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
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
        print(text)
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

    def send_question_to_server(self, question="use code to solve:"):
        if hasattr(self, 'ws_client') and self.ws_client:
            self.ws_client.send_question(question)

    # 滚动相关
    def scroll_up(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.value() - 30)

    def scroll_down(self):
        bar = self.scroll_area.verticalScrollBar()
        bar.setValue(bar.value() + 30)

class WebSocketClient(QObject):
    def __init__(self, overlay_window, ws_url="ws://localhost:8765"):
        super().__init__()
        self.overlay_window = overlay_window
        self.ws_url = ws_url
        self.loop = None
        self.ws = None

    def start(self):
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.listen())

    async def listen(self):
        try:
            async with websockets.connect(self.ws_url) as ws:
                self.ws = ws
                while True:
                    msg = await ws.recv()
                    data = json.loads(msg)
                    if data.get("type") == "ai_response":
                        answer = data.get("answer", "无回答")
                        self.overlay_window.answer_signal.emit(answer)
        except Exception as e:
            self.overlay_window.answer_signal.emit(f"WebSocket连接失败: {e}")

    def send_question(self, question):
        if self.loop and self.ws:
            asyncio.run_coroutine_threadsafe(
                self.ws.send(json.dumps({"command": "ai_query", "question": question})),
                self.loop
            )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = OverlayWindow()
    window.show()

    ws_client = WebSocketClient(window)
    window.ws_client = ws_client
    ws_client.start()

    def show_window():
        window.show()
        window.activateWindow()
        window.raise_()

    def hide_window():
        window.hide()

    def ask_ai():
        window.send_question_to_server()

    def scroll_up():
        window.scroll_up()

    def scroll_down():
        window.scroll_down()

    keyboard.add_hotkey('f11', show_window)
    keyboard.add_hotkey('f12', hide_window)
    keyboard.add_hotkey('f9', scroll_up)
    keyboard.add_hotkey('f10', scroll_down)
    keyboard.add_hotkey('f8', ask_ai)

    sys.exit(app.exec_())