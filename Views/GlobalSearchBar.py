"""全局搜索栏组件 — 跨模块搜索 + 下拉结果面板。"""

import tkinter as tk
from tkinter import ttk
from dataclasses import dataclass, field
from typing import Callable


@dataclass
class SearchResult:
    """跨模块搜索结果。"""
    name: str           # 显示名称
    module: str         # skill/note/ebook/todo/password/status
    item_id: str        # 条目 ID（用于跳转和高亮）
    snippet: str = ""   # 辅助信息（类别、优先级等）


MODULE_LABELS: dict[str, str] = {
    "skill": "技能", "note": "笔记", "ebook": "电子书",
    "todo": "待办", "password": "密码", "status": "状态",
}


class GlobalSearchBar(tk.Frame):
    """全局搜索栏，含防抖输入框和下拉结果面板。"""

    def __init__(self, parent: tk.Widget,
                 on_search: Callable[[str], list[SearchResult]],
                 on_navigate: Callable[[str, str], None]):
        super().__init__(parent, bg="#f0f0f0")
        self.on_search = on_search
        self.on_navigate = on_navigate
        self._debounce_id: str | None = None
        self._dropdown: tk.Toplevel | None = None
        self._result_map: dict[str, SearchResult] = {}

        self._build()

    def _build(self) -> None:
        self.entry = tk.Entry(
            self, font=("Microsoft YaHei", 9), width=16, relief=tk.FLAT
        )
        self.entry.pack(fill=tk.X, padx=8, pady=(8, 4))
        self._set_placeholder()
        self.entry.bind("<FocusIn>", self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<KeyRelease>", self._on_key)
        self.entry.bind("<Escape>", lambda e: self._hide_dropdown())

    def _set_placeholder(self) -> None:
        self.entry.delete(0, tk.END)
        self.entry.insert(0, "搜索所有模块...")
        self.entry.configure(fg="#999999")

    def _on_focus_in(self, event) -> None:
        if self.entry.get() == "搜索所有模块...":
            self.entry.delete(0, tk.END)
            self.entry.configure(fg="#333333")

    def _on_focus_out(self, event) -> None:
        if not self.entry.get().strip():
            self._set_placeholder()

    def _on_key(self, event) -> None:
        if event.keysym in ("Escape", "Up", "Down", "Return"):
            return
        if self._debounce_id:
            self.after_cancel(self._debounce_id)
        self._debounce_id = self.after(300, self._do_search)

    def _do_search(self) -> None:
        keyword = self.entry.get().strip()
        if keyword == "搜索所有模块..." or not keyword:
            self._hide_dropdown()
            return
        results = self.on_search(keyword)
        if results:
            self._show_dropdown(results)
        else:
            self._hide_dropdown()

    # ---- 下拉面板 ----

    def _show_dropdown(self, results: list[SearchResult]) -> None:
        self._hide_dropdown()

        dd = tk.Toplevel(self)
        dd.overrideredirect(True)
        dd.configure(bg="#ffffff")
        dd.bind("<FocusOut>", lambda e: self._hide_dropdown())

        # 定位在搜索框下方，向右扩展
        self.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height()
        w = max(360, self.winfo_width())
        dd.geometry(f"{w}x320+{x}+{y}")

        # 外边框
        border = tk.Frame(dd, bg="#cccccc", padx=1, pady=1)
        border.pack(fill=tk.BOTH, expand=True)

        # Treeview
        tree = ttk.Treeview(border, show="tree", selectmode="browse",
                           columns=("snippet",), height=14)
        tree.heading("#0", text="")
        tree.column("#0", width=240)
        tree.column("snippet", width=100, anchor=tk.E)

        scrollbar = ttk.Scrollbar(border, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(fill=tk.BOTH, expand=True)

        # 按模块分组
        groups: dict[str, list[SearchResult]] = {}
        for r in results:
            groups.setdefault(r.module, []).append(r)

        self._result_map.clear()
        for module, items in groups.items():
            label = MODULE_LABELS.get(module, module)
            parent_iid = f"__grp_{module}"
            tree.insert("", tk.END, iid=parent_iid,
                       text=f"  {label} ({len(items)})",
                       open=True, tags=("header",))
            for item in items:
                child_iid = f"{module}_{item.item_id}"
                tree.insert(parent_iid, tk.END, iid=child_iid,
                           text=f"    {item.name}",
                           values=(item.snippet,), tags=("result",))
                self._result_map[child_iid] = item

        tree.tag_configure("header", font=("Microsoft YaHei", 9, "bold"),
                          foreground="#4a90d9")
        tree.tag_configure("result", font=("Microsoft YaHei", 9))

        tree.bind("<Double-1>", lambda e: self._on_select(tree))
        tree.bind("<Return>", lambda e: self._on_select(tree))
        tree.bind("<Escape>", lambda e: self._hide_dropdown())

        # 点击外层关闭
        dd.bind("<Button-1>", lambda e: self._hide_dropdown())

        self._dropdown = dd
        self._dropdown_tree = tree

        # 短暂捕获焦点
        dd.after(50, lambda: tree.focus_set())

    def _on_select(self, tree: ttk.Treeview) -> None:
        selection = tree.selection()
        if not selection:
            return
        iid = selection[0]
        if iid.startswith("__grp_"):
            return  # 点击的是分组头
        result = self._result_map.get(iid)
        if result:
            self._hide_dropdown()
            self.on_navigate(result.module, result.item_id)

    def _hide_dropdown(self, event=None) -> None:
        if self._dropdown:
            try:
                self._dropdown.destroy()
            except tk.TclError:
                pass
            self._dropdown = None
        self._result_map.clear()

    # ---- 公开方法 ----

    def focus(self) -> None:
        """聚焦到搜索框并全选文本。"""
        self.entry.focus_set()
        if self.entry.get() != "搜索所有模块...":
            self.entry.select_range(0, tk.END)
