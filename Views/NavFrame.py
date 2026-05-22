"""左侧导航栏组件。"""

import tkinter as tk
from typing import Callable


class NavFrame(tk.Frame):
    """左侧导航栏，包含各功能模块的切换按钮。"""

    NAV_ITEMS = [
        ("profile", "个人档案"),
        ("status", "状态管理"),
        ("skill", "技能管理"),
        ("knowledge", "知识管理"),
        ("password", "密码管理"),
        ("backup", "数据管理"),
        ("dashboard", "数据概览"),
    ]

    def __init__(self, parent: tk.Widget, on_select: Callable[[str], None],
                 theme: dict | None = None):
        self._theme = theme or {
            "nav_bg": "#f0f0f0", "nav_active": "#4a90d9",
            "fg": "#333333", "bg": "#f0f0f0",
        }
        super().__init__(parent, width=150, bg=self._theme["nav_bg"])
        self.pack(side=tk.LEFT, fill=tk.Y)
        self.pack_propagate(False)

        self.on_select = on_select
        self.buttons: dict[str, tk.Button] = {}

        self._build()

    def _build(self) -> None:
        t = self._theme
        header = tk.Label(
            self, text="导航菜单", bg=t["nav_bg"],
            font=("Microsoft YaHei", 10, "bold"), pady=10,
            fg=t["fg"]
        )
        header.pack(fill=tk.X)

        for page_name, label in self.NAV_ITEMS:
            btn = tk.Button(
                self, text=label, anchor="w", relief=tk.FLAT,
                bg=t["nav_bg"], fg=t["fg"],
                activebackground="#d0d0d0", activeforeground="#000000",
                font=("Microsoft YaHei", 10), padx=16, pady=8,
                cursor="hand2",
                command=lambda name=page_name: self._on_click(name)
            )
            btn.pack(fill=tk.X)
            self.buttons[page_name] = btn

    def _on_click(self, page_name: str) -> None:
        self.set_active(page_name)
        self.on_select(page_name)

    def set_active(self, page_name: str) -> None:
        """高亮指定导航按钮，取消其他按钮高亮。"""
        t = self._theme
        for name, btn in self.buttons.items():
            if name == page_name:
                btn.configure(bg=t["nav_active"], fg="#ffffff")
            else:
                btn.configure(bg=t["nav_bg"], fg=t["fg"])
