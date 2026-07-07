import sys
from PyQt5.QtWidgets import QApplication
from chat_window import ChatWindow
from stealth import make_stealth
from tray import TrayIcon
from PyQt5.QtCore import Qt

if __name__ == "__main__":

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    chat_window = ChatWindow()
    make_stealth(chat_window)

    tray = TrayIcon(app, chat_window)  
    sys.exit(app.exec_())
