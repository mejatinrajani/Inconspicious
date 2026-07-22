import sys
import os
import ctypes
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from chat_window import ChatWindow
from stealth import make_stealth
from tray import TrayIcon
from PyQt5.QtCore import Qt

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    
    # 1. CHANGE THIS STRING to break the Windows icon cache!
    # I changed 'v1' to 'v2'. This forces Windows to treat it as a brand new app.
    myappid = 'inconspicuous_ai_shoe_app_v2'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    
    # 2. Get the exact path to the icon
    icon_path = resource_path(os.path.join('assets', 'icon.ico'))
    
    # 3. Apply the icon to the Application base
    app_icon = QIcon(icon_path)
    app.setWindowIcon(app_icon)
    
    chat_window = ChatWindow()
    
    # 4. FORCE apply the icon directly to the FramelessWindow widget
    chat_window.setWindowIcon(app_icon)
    
    make_stealth(chat_window)

    tray = TrayIcon(app, chat_window)  
    sys.exit(app.exec_())