"""页面基类 — 提供统计栏、右键菜单、条目标亮等通用功能。"""

import tkinter as tk
from tkinter import messagebox


class BasePage(tk.Frame):
    """所有表格式页面的基类，减少重复代码。"""

    def __init__(self, parent: tk.Widget, set_status):
        super().__init__(parent, bg="#ffffff")
        self.set_status = set_status

    # ---- 统计栏 ----

    def _build_stats_bar(self, pady: int = 6) -> None:
        self.stats_var = tk.StringVar()
        stats = tk.Label(
            self, textvariable=self.stats_var, bg="#f5f5f5",
            font=("Microsoft YaHei", 9), fg="#666666", pady=pady
        )
        stats.pack(fill=tk.X, side=tk.BOTTOM)

    # ---- 右键菜单 ----

    def _build_context_menu(self, items: list[tuple[str, object]]) -> None:
        """items: [(label, command), ("---", None) 表示分隔线]"""
        self.context_menu = tk.Menu(self, tearoff=0)
        for label, cmd in items:
            if label == "---":
                self.context_menu.add_separator()
            else:
                self.context_menu.add_command(label=label, command=cmd)
        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event) -> None:
        tree = event.widget
        item = tree.identify_row(event.y)
        if item:
            tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    # ---- 选中 / 高亮 ----

    def _get_selected_id(self, prompt: str = "请先选中一条记录") -> str | None:
        """获取当前选中行的 ID。"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", prompt)
            return None
        return selection[0]

    def highlight_item(self, item_id: str) -> None:
        """定位并高亮指定条目。"""
        if not self.tree.exists(item_id):
            return
        self.tree.selection_set(item_id)
        self.tree.see(item_id)
        self.tree.focus(item_id)

    # ---- 辅助 ----

    def _clear_tree(self) -> None:
        """清空 Treeview 所有行。"""
        for item in self.tree.get_children():
            self.tree.delete(item)
