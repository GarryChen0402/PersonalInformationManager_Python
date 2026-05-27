"""个人信息管理器 (PIM) — 程序入口。"""

import sys
from PySide6.QtWidgets import QApplication
from Core.Config import ensure_directories
from Core.DataMigration import run_migrations
from Views.App import App

if __name__ == "__main__":
    ensure_directories()
    run_migrations()
    app = QApplication(sys.argv)
    app.setApplicationName("PersonalInformationManager")
    app.setApplicationVersion("1.3")
    window = App()
    window.show()
    sys.exit(app.exec())
