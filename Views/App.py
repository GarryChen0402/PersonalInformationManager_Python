"""应用程序主窗口。"""

import tkinter as tk

from .NavFrame import NavFrame


class App:
    """个人信息管理器主应用程序。"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("个人信息管理器 (PIM)")
        self.root.geometry("960x640")
        self.root.minsize(800, 500)
        self.root.configure(bg="#ffffff")

        # 底部状态栏（状态文本 + 版本号）
        bottom_frame = tk.Frame(self.root, bd=1, relief=tk.SUNKEN)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = tk.Label(
            bottom_frame, textvariable=self.status_var,
            anchor=tk.W, padx=8, font=("Microsoft YaHei", 9)
        )
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        version_label = tk.Label(
            bottom_frame, text="v1.0  ",
            anchor=tk.E, padx=8, font=("Microsoft YaHei", 9)
        )
        version_label.pack(side=tk.RIGHT)

        # 左侧导航栏
        self.nav = NavFrame(self.root, on_select=self._switch_page)

        # 右侧内容区
        self.content = tk.Frame(self.root, bg="#ffffff")
        self.content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 初始化页面
        self.pages: dict[str, tk.Frame] = {}
        self._init_pages()

        # 默认显示个人档案
        self._switch_page("profile")
        self.nav.set_active("profile")

    def _init_pages(self) -> None:
        """初始化所有功能页面占位。"""
        placeholders = [
            "profile", "status", "skill", "knowledge",
            "password", "backup", "dashboard"
        ]
        for name in placeholders:
            frame = tk.Frame(self.content, bg="#ffffff")
            label = tk.Label(
                frame, text=f"「{name}」模块开发中...",
                font=("Microsoft YaHei", 14), fg="#999999", bg="#ffffff"
            )
            label.pack(expand=True)
            self.pages[name] = frame

    def _switch_page(self, page_name: str) -> None:
        """切换内容区显示的页面。"""
        for page in self.pages.values():
            page.pack_forget()
        page = self.pages.get(page_name)
        if page:
            page.pack(fill=tk.BOTH, expand=True)

    def set_status(self, message: str) -> None:
        """更新状态栏消息。"""
        self.status_var.set(message)

    def run(self) -> None:
        """启动主事件循环。"""
        self.root.mainloop()
