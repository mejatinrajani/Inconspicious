import os
import re
import html
import ctypes
from ctypes import wintypes
from PyQt5.QtWidgets import (
    QVBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QHBoxLayout, QApplication,
    QLabel, QFrame
)
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QBrush, QFont, QTextCursor, QIcon
import markdown
from pygments import highlight
from pygments.lexers import get_lexer_by_name, TextLexer
from pygments.formatters import HtmlFormatter
import sys
from pygments.util import ClassNotFound
from qframelesswindow import FramelessWindow
from groq import Groq
from dotenv import load_dotenv, find_dotenv


def load_app_env():
    if getattr(sys, "frozen", False):
        # 1. Checks for an external .env next to the .exe (lets you swap keys later without rebuilding)
        exe_env = os.path.join(os.path.dirname(sys.executable), ".env")
        if os.path.exists(exe_env):
            load_dotenv(exe_env, override=True)
            return

        # 2. Falls back to the .env bundled inside the .exe
        bundled_env = os.path.join(sys._MEIPASS, ".env")
        if os.path.exists(bundled_env):
            load_dotenv(bundled_env, override=True)
            return

    # 3. Normal local dev mode
    load_dotenv(find_dotenv(usecwd=True), override=True)

load_app_env()

# =========================================================
# Master System Prompt (Python & JavaScript Specialist)
# =========================================================
SYSTEM_PROMPT = """You are an elite Senior Software Engineer specializing in Python and JavaScript (ES6+, Node.js, React, DOM, async programming, OOP, debugging, and DSA).

Your job is to solve technical and coding doubts with precision, clarity, and clean structure.

### Behavioral Rules
1. **Direct First:** Lead with the core answer, root cause, or fix immediately—no filler or fluff.
2. **Idiomatic & Bug-Free Code:** Write clean, modern, production-ready Python 3 or modern JavaScript (ES6+). Include brief inline comments only where logic is non-obvious.
3. **Debugging:** When given broken code or an error, state **what failed**, **why it happened**, and provide the **corrected code**.
4. **DSA / Performance:** When solving algorithmic or optimization questions, briefly state **Time** and **Space Complexity**.
5. **Context Awareness:** Use the ongoing conversation history to understand follow-up questions, previous code snippets, and iterative refinements without asking the user to repeat themselves.

### Formatting Rules (Strict)
- Always put code snippets inside properly tagged fenced code blocks (```python or ```javascript) so they render in a clean code panel.
- Use inline backticks (e.g., `async/await`, `dict.get()`) for variable names, functions, keywords, and short expressions.
- Structure explanations using short headings (`###`), concise bullet points, and **bold** key terms for fast reading.
- Use Markdown tables when comparing concepts (e.g., `==` vs `===`, `list` vs `tuple`).
- Avoid raw HTML or LaTeX syntax—stick strictly to clean Markdown.
"""


# =========================================================
# Groq Background Worker
# =========================================================
class GroqWorker(QThread):
    response_ready = pyqtSignal(str, int)  # (reply_text, key_index_used)
    error_occurred = pyqtSignal(str)

    def __init__(self, messages, indexed_keys):
        super().__init__()
        self.messages = messages
        self.indexed_keys = indexed_keys  # e.g. [(0, key1), (1, key2)]

    def run(self):
        last_error = "No Groq API keys configured."

        for key_idx, api_key in self.indexed_keys:
            try:
                client = Groq(api_key=api_key)

                chat_completion = client.chat.completions.create(
                    messages=self.messages,
                    model="openai/gpt-oss-120b",
                    temperature=0.3,
                )

                reply = chat_completion.choices[0].message.content
                print(f"Response received using GROQ_API_KEY #{key_idx + 1}")
                self.response_ready.emit(reply, key_idx)
                return  # Success — stop trying other keys

            except Exception as e:
                last_error = str(e)
                print(f"GROQ_API_KEY #{key_idx + 1} failed ({e}). Trying next key...")

        # Only reached if every configured key failed
        self.error_occurred.emit(f"All API keys failed. Last error: {last_error}")


# =========================================================
# Main Chat Window
# =========================================================
class ChatWindow(FramelessWindow):
    def __init__(self):
        super().__init__()

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('inconspicuous_ai_shoe_app')
        self.setWindowIcon(QIcon('icon.ico'))

        self.setWindowTitle("Inconspicuous AI")
        self.resize(850, 560)
        self.resize_margin = 8

        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setMinimumSize(500, 350)

        self.api_keys = [
            key.strip()
            for key in (
                os.environ.get("GROQ_API_KEY"),
                os.environ.get("GROQ_API_KEY_2"),
            )
            if key and key.strip()
        ]
        self.current_key_index = 0
        self.is_dark_theme = True

        # Conversation Memory Setup (keeps system prompt + last 20 messages)
        self.max_history_messages = 20
        self.messages = []
        self.reset_memory()

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
        header.setSpacing(8)

        title = QLabel("Inconspicuous AI 😈 (Don't Worry, I'm Stealthy)")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))

        self.clear_button = QPushButton("↺")
        self.clear_button.setFixedSize(32, 32)
        self.clear_button.setToolTip("New Chat (Clear Memory)")
        self.clear_button.clicked.connect(self.clear_chat)

        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(32, 32)
        self.close_button.setToolTip("Hide Window")
        self.close_button.clicked.connect(self.hide)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.clear_button)
        header.addWidget(self.close_button)
        layout.addLayout(header)

        #####################################################
        # Chat History
        #####################################################
        self.chat_history = QTextEdit()
        self.chat_history.setReadOnly(True)
        self.chat_history.setPlaceholderText("Hello 👋\n\nWhat Python or JavaScript problem are we solving today?")
        layout.addWidget(self.chat_history)

        #####################################################
        # Input Box
        #####################################################
        bottom = QHBoxLayout()
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Ask anything in Python or JavaScript...")
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
    # Conversation Memory Management
    #########################################################
    def reset_memory(self):
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT}
        ]

    def get_context_payload(self):
        """
        Returns a thread-safe list starting with the system prompt
        followed by a sliding window of recent messages.
        Always guarantees the first conversation turn is a 'user' message.
        """
        system_msg = self.messages[0]
        conversation = self.messages[1:]

        # Keep enough messages for past pairs + the newest user prompt
        window_limit = self.max_history_messages + 1
        if len(conversation) > window_limit:
            recent = conversation[-window_limit:]
            while recent and recent[0]["role"] != "user":
                recent.pop(0)
        else:
            recent = list(conversation)

        return [system_msg] + recent

    def get_ordered_keys(self):
        """
        Returns all keys starting from current_key_index for round-robin rotation,
        followed by the remaining keys as instant fallbacks.
        """
        indexed = list(enumerate(self.api_keys))
        return indexed[self.current_key_index:] + indexed[:self.current_key_index]

    def clear_chat(self):
        self.reset_memory()
        self.chat_history.clear()
        self.input_box.setFocus()

    #########################################################
    # Sending & Receiving Logic
    #########################################################
    def handle_send(self):
        text = self.input_box.text().strip()
        if not text:
            return

        if not self.api_keys:
            self.chat_history.append(
                "<div style='margin-top: 6px;'><b style='color:#FF4A4A;'>Config Error:</b><br>"
                "No GROQ_API_KEY found in your .env file.</div><br>"
            )
            return

        # 1. Save user message to conversation memory
        self.messages.append({"role": "user", "content": text})

        # 2. Render escaped user message in UI
        safe_text = html.escape(text).replace("\n", "<br>")
        self.chat_history.append(
            f"<div style='margin-top: 8px;'><b style='color: #4F8EF7;'>You</b><br>{safe_text}</div>"
        )
        self.input_box.clear()

        # 3. Print loading indicator
        self.chat_history.append("<i>Inconspicuous AI is thinking...</i>")
        self.scroll_to_bottom()

        # 4. Lock inputs while request is in flight
        self.input_box.setEnabled(False)
        self.send_button.setEnabled(False)
        self.clear_button.setEnabled(False)

        # 5. Start background worker with rotated keys + failover order
        payload = self.get_context_payload()
        ordered_keys = self.get_ordered_keys()
        self.worker = GroqWorker(payload, ordered_keys)
        self.worker.response_ready.connect(self.on_response_ready)
        self.worker.error_occurred.connect(self.on_error)
        self.worker.start()

    def remove_thinking_indicator(self):
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.select(QTextCursor.BlockUnderCursor)
        cursor.removeSelectedText()
        cursor.deletePreviousChar()

    def on_response_ready(self, reply, used_key_index):
        self.remove_thinking_indicator()

        # Rotate to the next key for the upcoming query
        self.current_key_index = (used_key_index + 1) % len(self.api_keys)

        # Save assistant response to memory for future turns
        self.messages.append({"role": "assistant", "content": reply})

        formatted_html = self.format_markdown_to_html(reply)
        divider_color = "#3A3B3F" if self.is_dark_theme else "#E2E4E9"

        self.chat_history.append(
            f"<div style='margin-top: 6px;'>"
            f"<b style='color: #34D399;'>Inconspicuous AI</b><br>"
            f"{formatted_html}"
            f"</div>"
            f"<hr style='border: 0; border-top: 1px solid {divider_color}; margin: 12px 0;'><br>"
        )
        self.restore_inputs()

    def on_error(self, error_msg):
        self.remove_thinking_indicator()

        # Roll back the unanswered user message so memory stays valid
        if len(self.messages) > 1 and self.messages[-1]["role"] == "user":
            self.messages.pop()

        safe_err = html.escape(error_msg)
        self.chat_history.append(
            f"<div style='margin-top: 6px;'><b style='color:#FF4A4A;'>API Error:</b><br>{safe_err}</div><br>"
        )
        self.restore_inputs()

    def restore_inputs(self):
        self.input_box.setEnabled(True)
        self.send_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.input_box.setFocus()
        self.scroll_to_bottom()

    def scroll_to_bottom(self):
        cursor = self.chat_history.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_history.setTextCursor(cursor)

    #########################################################
    # Markdown & IDE Code Panel Formatter
    #########################################################
    def format_markdown_to_html(self, md_text):
        code_panels = []

        def extract_code_block(match):
            raw_lang = (match.group(1) or "").strip()
            code = match.group(2).rstrip("\n")
            lang_label = raw_lang.upper() if raw_lang else "CODE"

            try:
                lexer = get_lexer_by_name(raw_lang) if raw_lang else TextLexer()
            except ClassNotFound:
                lexer = TextLexer()

            formatter = HtmlFormatter(noclasses=True, style="monokai", nowrap=True)
            highlighted = highlight(code, lexer, formatter).rstrip("\n")

            panel_html = f"""
            <table width="100%" cellspacing="0" cellpadding="0" style="margin: 10px 0px; border: 1px solid #3c3d37;">
                <tr>
                    <td bgcolor="#1c1d1a" style="padding: 6px 12px; color: #a6e22e; font-family: Consolas, monospace; font-size: 12px; font-weight: bold; border-bottom: 1px solid #3c3d37;">
                        {html.escape(lang_label)}
                    </td>
                </tr>
                <tr>
                    <td bgcolor="#272822" style="padding: 12px 14px;">
                        <pre style="margin: 0; font-family: Consolas, 'Cascadia Code', monospace; font-size: 14px; color: #f8f8f2; white-space: pre-wrap;">{highlighted}</pre>
                    </td>
                </tr>
            </table>
            """
            placeholder = f"@@CODEPANEL_{len(code_panels)}@@"
            code_panels.append(panel_html)
            return f"\n\n{placeholder}\n\n"

        processed_md = re.sub(
            r'```([a-zA-Z0-9_+#.-]*)[ \t]*\r?\n(.*?)```',
            extract_code_block,
            md_text,
            flags=re.DOTALL
        )

        html_body = markdown.markdown(
            processed_md,
            extensions=['tables', 'sane_lists', 'nl2br']
        )

        if self.is_dark_theme:
            heading_color = "#7AB3FF"
            inline_bg = "#3A3C42"
            inline_fg = "#FFCB6B"
            border_color = "#4A4D55"
            quote_bg = "#25262A"
            quote_fg = "#B8BCC6"
            th_bg = "#34363B"
        else:
            heading_color = "#1A56DB"
            inline_bg = "#ECEFF4"
            inline_fg = "#C7254E"
            border_color = "#D0D7DE"
            quote_bg = "#F3F4F6"
            quote_fg = "#4B5563"
            th_bg = "#E5E7EB"

        html_body = html_body.replace('<h1>', f'<h2 style="color: {heading_color}; margin: 14px 0 6px 0; font-size: 19px;">')
        html_body = html_body.replace('</h1>', '</h2>')
        html_body = html_body.replace('<h2>', f'<h3 style="color: {heading_color}; margin: 12px 0 6px 0; font-size: 17px;">')
        html_body = html_body.replace('</h2>', '</h3>')
        html_body = html_body.replace('<h3>', f'<h4 style="color: {heading_color}; margin: 10px 0 4px 0; font-size: 16px;">')
        html_body = html_body.replace('</h3>', '</h4>')

        html_body = html_body.replace('<p>', '<p style="margin: 6px 0px; line-height: 145%;">')
        html_body = html_body.replace('<ul>', '<ul style="margin: 6px 0px 8px 0px;">')
        html_body = html_body.replace('<ol>', '<ol style="margin: 6px 0px 8px 0px;">')
        html_body = html_body.replace('<li>', '<li style="margin-bottom: 4px; line-height: 140%;">')

        html_body = html_body.replace(
            '<code>',
            f'<code style="background-color: {inline_bg}; color: {inline_fg}; font-family: Consolas, monospace; font-size: 14px;">&nbsp;'
        ).replace('</code>', '&nbsp;</code>')

        html_body = html_body.replace(
            '<blockquote>',
            f'<table width="100%" cellspacing="0" cellpadding="8" style="margin: 8px 0px; border-left: 3px solid {heading_color};"><tr><td bgcolor="{quote_bg}" style="color: {quote_fg};">'
        ).replace('</blockquote>', '</td></tr></table>')

        html_body = html_body.replace(
            '<table>',
            f'<table width="100%" cellspacing="0" cellpadding="6" style="margin: 10px 0px; border: 1px solid {border_color};">'
        )
        html_body = html_body.replace(
            '<th>',
            f'<th bgcolor="{th_bg}" align="left" style="border: 1px solid {border_color}; font-weight: bold;">'
        )
        html_body = html_body.replace(
            '<td>',
            f'<td style="border: 1px solid {border_color};">'
        )

        for idx, panel in enumerate(code_panels):
            html_body = re.sub(
                rf'(?:<p[^>]*>)?@@CODEPANEL_{idx}@@(?:</p>)?',
                lambda _, p=panel: p,
                html_body
            )

        return html_body

    #########################################################
    # Native Resizing / UI Overrides
    #########################################################
    def nativeEvent(self, eventType, message):
        msg = ctypes.wintypes.MSG.from_address(message.__int__())

        if msg.message == 0x0084:  # WM_NCHITTEST
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
                    return True, 1  # HTCLIENT
                return True, 2  # HTCAPTION

        return super().nativeEvent(eventType, message)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255, 12)))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), 18, 18)

    def light_theme(self):
        self.is_dark_theme = False
        self.setStyleSheet("""
        QFrame{ background:#F8F8F8; border:1px solid rgba(0,0,0,35); border-radius:18px; }
        QLabel{ background:transparent; color:#222; border:none; }
        QTextEdit{ background:white; color:#222; border:none; border-radius:15px; padding:15px; font-size:16px; }
        QLineEdit{ background:white; color:#222; border:1px solid #DDD; border-radius:14px; padding:12px; font-size:16px; }
        QPushButton{ background:#2D7DFF; color:white; border:none; border-radius:12px; font-size:14px; }
        QPushButton:hover{ background:#4A90FF; }
        QPushButton:disabled{ background:#A0C2FF; }
        QTextEdit QScrollBar:vertical{ width:8px; background:transparent; }
        QTextEdit QScrollBar::handle:vertical{ background:#C5C5C5; border-radius:4px; }
        """)

    def dark_theme(self):
        self.is_dark_theme = True
        self.setStyleSheet("""
        QFrame{ background:#202124; border:1px solid rgba(255,255,255,40); border-radius:18px; }
        QLabel{ background:transparent; color:white; border:none; }
        QTextEdit{ background:#2A2B2E; color:white; border:none; border-radius:15px; padding:15px; font-size:16px; }
        QLineEdit{ background:#2A2B2E; color:white; border:1px solid #444; border-radius:14px; padding:12px; font-size:16px; }
        QPushButton{ background:#4F8EF7; color:white; border:none; border-radius:12px; font-size:14px; }
        QPushButton:hover{ background:#6BA3FF; }
        QPushButton:disabled{ background:#3A4D70; }
        QTextEdit QScrollBar:vertical{ width:8px; background:transparent; }
        QTextEdit QScrollBar::handle:vertical{ background:#555; border-radius:4px; }
        """)