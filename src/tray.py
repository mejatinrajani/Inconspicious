from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction
from PyQt5.QtGui import QIcon

class TrayIcon(QSystemTrayIcon):
    def __init__(self, app, chat_window):
        super().__init__(QIcon("../assets/icon.ico"), app)

        self.app = app
        self.chat_window = chat_window

        # Context menu
        menu = QMenu()
        open_action = QAction("Open Chat")
        open_action.triggered.connect(self.chat_window.show)
        menu.addAction(open_action)

        exit_action = QAction("Exit")
        exit_action.triggered.connect(self.app.quit)
        menu.addAction(exit_action)

        self.setContextMenu(menu)

        # Show tray icon
        self.setVisible(True)
        self.show()

        # Connect left-click (activation)
        self.activated.connect(self.on_click)

    def on_click(self, reason):
        if reason == QSystemTrayIcon.Trigger:  # Trigger = left-click
            self.chat_window.show()
