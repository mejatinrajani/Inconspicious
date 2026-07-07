import os
import ctypes
from ctypes import wintypes
from PyQt5.QtWidgets import (
    QVBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QHBoxLayout, QApplication,
    QLabel, QFrame
)
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal
from qframelesswindow import FramelessWindow
from PyQt5.QtGui import QColor, QPainter, QBrush, QFont, QCursor, QTextCursor
from groq import Groq
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
# =========================================================
# Groq Background Worker
# =========================================================
class GroqWorker(QThread):
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, user_message, api_key):
        super().__init__()
        self.user_message = user_message
        self.api_key = api_key

    def run(self):
        try:
            print("Background thread started...") 
            client = Groq(api_key=self.api_key)
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are an AI tool which help users in coding and technical doubts."},
                    {"role": "user", "content": self.user_message}
                ],
                # -----------------------------------------------------
                # CHANGE THIS LINE BELOW:
                # -----------------------------------------------------
                model="llama-3.3-70b-versatile", 
            )
            
            reply = chat_completion.choices[0].message.content
            print("Response received from Groq!") 
            self.response_ready.emit(reply)
            
        except Exception as e:
            print(f"Groq API Error: {e}") 
            self.error_occurred.emit(str(e))


# =========================================================
# Main Chat Window
# =========================================================
class ChatWindow(FramelessWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Inconspicious AI")
        self.resize(850, 560)
        self.resize_margin = 8

        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(500, 350)

        self.groq_api_key = os.environ.get("GROQ_API_KEY")

        #####################################################
        # Layout Setup
        #####################################################
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)

        self.container = QFrame()
        main_layout.addWidget(self.container)

        layout = QVBoxLayout(self.container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        #####################################################
        # Header
        #####################################################
        header = QHBoxLayout()
        title = QLabel("Inconspicious AI 😈 (Don't Worry, I'm Stealthy)")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))

        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(32, 32)
        self.close_button.clicked.connect(self.hide)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.close_button)
        layout.addLayout(header)

        #####################################################
        # Chat History
        #####################################################
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("Hello 👋\n\nWhat would you like to work on today?")
        layout.addWidget(self.chat_history)

        #####################################################
        # Input Box
        #####################################################
        bottom = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask this AI anything...")
        self.input_box.returnPressed.connect(self.handle_send)

        self.send_button = QPushButton("➜")
        self.send_button.setFixedSize(48, 48)
        self.send_button.clicked.connect(self.handle_send)

        bottom.addWidget(self.input_box)
        bottom.addWidget(self.send_button)
        layout.addLayout(bottom)

        #####################################################
        # Theme Init
        #####################################################
        palette = QApplication.palette()
        if palette.color(palette.Window).lightness() > 128:
            self.light_theme()
        else:
            self.dark_theme()

    #########################################################
    # Sending Logic
    #########################################################
    def handle_send(self):
        text = self.input_box.text().strip()
        if not text:
            return

        print(f"Sending message: {text}") # Debug print

        # 1. Print user message
        self.chat_history.append(f"<b>You</b><br>{text}<br>")
        self.input_box.clear()
        
        # 2. Print loading state
        self.chat_history.append("<i>Inconspicious AI is thinking...</i><br>")
        self.scroll_to_bottom()

        # 3. Disable inputs
        self.input_box.setEnabled(False)
        self.send_button.setEnabled(False)

        # 4. Start Thread
        self.worker = GroqWorker(text, self.groq_api_key)
        self.worker.response_ready.connect(self.on_response_ready)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()

    def on_response_ready(self, reply):
        # Remove the "thinking..." line by undoing the last block
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.select(QTextCursor.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar() # Remove the extra newline

        formatted_reply = reply.replace('\n', '<br>')
        self.chat_history.append(f"<b>Inconspicious AI</b><br>{formatted_reply}<br><br>")
        self.restore_inputs()

    def on_error(self, error_msg):
        self.chat_history.append(f"<b style='color:#FF4A4A;'>API Error:</b><br>{error_msg}<br><br>")
        self.restore_inputs()

    def restore_inputs(self):
        self.input_box.setEnabled(True)
        self.send_button.setEnabled(True)
        self.input_box.setFocus()
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        cursor = self.chat_history.textCursor()
        cursor.movePosition(cursor.End)
        self.chat_history.setTextCursor(cursor)

    #########################################################
    # Native Resizing / UI Overrides
    #########################################################
    def nativeEvent(self, eventType, message):
        msg = ctypes.wintypes.MSG.from_address(message.__int__())

        if msg.message == 0x0084: # WM_NCHITTEST
            x = msg.lParam & 0xffff
            y = (msg.lParam >> 16) & 0xffff
            
            if x >= 32768: x -= 65536
            if y >= 32768: y -= 65536

            pos = self.mapFromGlobal(QPoint(x, y))
            w, h = self.width(), self.height()
            margin = self.resize_margin

            left = pos.x() < margin
            right = pos.x() > w - margin
            top = pos.y() < margin
            bottom = pos.y() > h - margin

            if top and left: return True, 13
            if top and right: return True, 14
            if bottom and left: return True, 16
            if bottom and right: return True, 17
            if left: return True, 10
            if right: return True, 11
            if top: return True, 12
            if bottom: return True, 15

            if pos.y() < 60:
                widget_under_mouse = self.childAt(pos)
                if isinstance(widget_under_mouse, QPushButton):
                    return True, 1 # HTCLIENT
                return True, 2 # HTCAPTION

        return super().nativeEvent(eventType, message)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255,255,255,12)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(),18,18)

    def light_theme(self):
        self.setStyleSheet("""
        QFrame{ background:#F8F8F8; border:1px solid rgba(0,0,0,35); border-radius:18px; }
        QLabel{ background:transparent; color:#222; border:none; }
        QTextEdit{ background:white; color:#222; border:none; border-radius:15px; padding:15px; font-size:16px; }
        QLineEdit{ background:white; color:#222; border:1px solid #DDD; border-radius:14px; padding:12px; font-size:16px; }
        QPushButton{ background:#2D7DFF; color:white; border:none; border-radius:12px; font-size:14px; }
        QPushButton:hover{ background:#4A90FF; }
        QTextEdit QScrollBar:vertical{ width:8px; background:transparent; }
        QTextEdit QScrollBar::handle:vertical{ background:#C5C5C5; border-radius:4px; }
        """)

    def dark_theme(self):
        self.setStyleSheet("""
        QFrame{ background:#202124; border:1px solid rgba(255,255,255,40); border-radius:18px; }
        QLabel{ background:transparent; color:white; border:none; }
        QTextEdit{ background:#2A2B2E; color:white; border:none; border-radius:15px; padding:15px; font-size:16px; }
        QLineEdit{ background:#2A2B2E; color:white; border:1px solid #444; border-radius:14px; padding:12px; font-size:16px; }
        QPushButton{ background:#4F8EF7; color:white; border:none; border-radius:12px; font-size:14px; }
        QPushButton:hover{ background:#6BA3FF; }
        QTextEdit QScrollBar:vertical{ width:8px; background:transparent; }
        QTextEdit QScrollBar::handle:vertical{ background:#555; border-radius:4px; }
        """)