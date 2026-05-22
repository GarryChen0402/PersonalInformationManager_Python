"""个人信息管理器 (PIM) — 程序入口。"""

from Core.Config import ensure_directories
from Core.DataMigration import run_migrations
from Views.App import App

if __name__ == "__main__":
    ensure_directories()
    run_migrations()
    app = App()
    app.run()
