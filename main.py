"""个人信息管理器 (PIM) — 程序入口。"""

from Core.Config import ensure_directories
from Views.App import App

if __name__ == "__main__":
    ensure_directories()
    app = App()
    app.run()
