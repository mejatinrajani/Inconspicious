import sys
from PyQt5.QtWidgets import QApplication
from chat_window import ChatWindow
from stealth import make_stealth
from tray import TrayIcon

if __name__ == "__main__":
    app = QApplication(sys.argv)
    chat_window = ChatWindow()
    make_stealth(chat_window)

    tray = TrayIcon(app, chat_window)  
    sys.exit(app.exec_())
