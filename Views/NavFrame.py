"""左侧导航栏组件。"""

import tkinter as tk
from typing import Callable

from .GlobalSearchBar import GlobalSearchBar, SearchResult


class NavFrame(tk.Frame):
    """左侧导航栏，包含全局搜索和各功能模块的切换按钮。"""

    NAV_ITEMS = [
        ("profile", "◉", "◉  个人档案"),
        ("status", "★", "★  状态管理"),
        ("skill", "◆", "◆  技能管理"),
        ("knowledge", "◣", "◣  知识管理"),
        ("todo", "☑", "☑  待办事项"),
        ("habit", "↯", "↯  习惯追踪"),
        ("journal", "☷", "☷  日记"),
        ("password", "⚿", "⚿  密码管理"),
        ("backup", "⚙", "⚙  数据管理"),
        ("dashboard", "▣", "▣  数据概览"),
    ]

    EXPANDED_WIDTH = 150
    COLLAPSED_WIDTH = 50

    def __init__(self, parent: tk.Widget, on_select: Callable[[str], None],
                 theme: dict | None = None,
                 on_search: Callable[[str], list[SearchResult]] | None = None,
                 on_navigate: Callable[[str, str], None] | None = None):
        self._theme = theme or {
            "nav_bg": "#f0f0f0", "nav_active": "#4a90d9",
            "fg": "#333333", "bg": "#f0f0f0",
        }
        super().__init__(parent, width=self.EXPANDED_WIDTH, bg=self._theme["nav_bg"])
        self.pack(side=tk.LEFT, fill=tk.Y)
        self.pack_propagate(False)

        self.on_select = on_select
        self.on_navigate = on_navigate
        self.buttons: dict[str, tk.Button] = {}
        self.collapsed = False

        self._build(on_search)

    def _build(self, on_search) -> None:
        t = self._theme

        # 折叠按钮
        collapse_frame = tk.Frame(self, bg=t["nav_bg"])
        collapse_frame.pack(fill=tk.X)

        self.collapse_btn = tk.Button(
            collapse_frame, text="◀", relief=tk.FLAT,
            bg=t["nav_bg"], fg=t["fg"],
            activebackground="#d0d0d0", activeforeground="#000000",
            font=("Microsoft YaHei", 8), padx=4, pady=2,
            cursor="hand2", command=self.toggle_collapse
        )
        self.collapse_btn.pack(side=tk.RIGHT, padx=2, pady=2)

        # 全局搜索栏
        if on_search and self.on_navigate:
            self.search_bar = GlobalSearchBar(
                self, on_search=on_search, on_navigate=self._on_search_navigate
            )
            self.search_bar.pack(fill=tk.X)
        else:
            self.search_bar = None

        header = tk.Label(
            self, text="导航菜单", bg=t["nav_bg"],
            font=("Microsoft YaHei", 10, "bold"), pady=10,
            fg=t["fg"]
        )
        header.pack(fill=tk.X)

        for page_name, icon, full_label in self.NAV_ITEMS:
            btn = tk.Button(
                self, text=full_label, anchor="w", relief=tk.FLAT,
                bg=t["nav_bg"], fg=t["fg"],
                activebackground="#d0d0d0", activeforeground="#000000",
                font=("Microsoft YaHei", 10), padx=16, pady=8,
                cursor="hand2",
                command=lambda name=page_name: self._on_click(name)
            )
            btn.pack(fill=tk.X)
            btn.icon_text = icon
            btn.full_text = full_label
            self.buttons[page_name] = btn

    def toggle_collapse(self) -> None:
        """折叠/展开导航栏。"""
        if self.collapsed:
            self.config(width=self.EXPANDED_WIDTH)
            self.collapse_btn.configure(text="◀")
            for btn in self.buttons.values():
                btn.configure(text=btn.full_text, anchor="w", padx=16)
        else:
            self.config(width=self.COLLAPSED_WIDTH)
            self.collapse_btn.configure(text="▶")
            for btn in self.buttons.values():
                btn.configure(text=btn.icon_text, anchor="center", padx=4)
        self.collapsed = not self.collapsed

    def _on_click(self, page_name: str) -> None:
        self.set_active(page_name)
        self.on_select(page_name)

    def _on_search_navigate(self, module: str, item_id: str) -> None:
        """全局搜索结果导航。"""
        if self.on_navigate:
            self.on_navigate(module, item_id)

    def set_active(self, page_name: str) -> None:
        """高亮指定导航按钮，取消其他按钮高亮。"""
        t = self._theme
        for name, btn in self.buttons.items():
            if name == page_name:
                btn.configure(bg=t["nav_active"], fg="#ffffff")
            else:
                btn.configure(bg=t["nav_bg"], fg=t["fg"])
