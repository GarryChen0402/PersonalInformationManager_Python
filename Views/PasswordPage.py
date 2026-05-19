"""密码管理页面。"""

import tkinter as tk
from tkinter import ttk, messagebox

from Services.PasswordManager import PasswordManager
from Models.Password import PasswordEntry
from .Widgets import SearchBar, FormDialog, ConfirmDialog


class PasswordPage(tk.Frame):
    """密码管理页面，密码不明文显示在列表中。"""

    def __init__(self, parent: tk.Widget, set_status):
        super().__init__(parent, bg="#ffffff")
        self.manager = PasswordManager()
        self.set_status = set_status

        self._build_toolbar()
        self._build_table()
        self._build_context_menu()
        self._build_stats_bar()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self, bg="#fafafa", pady=8)
        toolbar.pack(fill=tk.X, padx=12, pady=(12, 0))

        self.search_bar = SearchBar(toolbar, on_search=self._on_search)
        self.search_bar.pack(side=tk.LEFT, padx=4)

        add_btn = tk.Button(
            toolbar, text="+ 添加密码", command=self._open_add_dialog,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        add_btn.pack(side=tk.RIGHT, padx=4)

    # ---- 表格 ----

    def _build_table(self) -> None:
        columns = ("platform", "url", "username", "note", "updated")
        self.tree = ttk.Treeview(self, columns=columns, show="headings",
                                 selectmode="browse")

        self.tree.heading("platform", text="平台")
        self.tree.heading("url", text="网址")
        self.tree.heading("username", text="账号")
        self.tree.heading("note", text="备注")
        self.tree.heading("updated", text="更新时间")

        self.tree.column("platform", width=120)
        self.tree.column("url", width=180)
        self.tree.column("username", width=120)
        self.tree.column("note", width=120)
        self.tree.column("updated", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12), pady=8)

    # ---- 右键菜单 ----

    def _build_context_menu(self) -> None:
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="查看密码", command=self._view_password)
        self.context_menu.add_command(label="复制密码", command=self._copy_password)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="编辑", command=self._open_edit_dialog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=self._confirm_delete)

        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    # ---- 底部统计 ----

    def _build_stats_bar(self) -> None:
        self.stats_var = tk.StringVar()
        stats = tk.Label(
            self, textvariable=self.stats_var, bg="#f5f5f5",
            font=("Microsoft YaHei", 9), fg="#666666", pady=6
        )
        stats.pack(fill=tk.X, side=tk.BOTTOM)

    # ---- 添加 ----

    def _open_add_dialog(self) -> None:
        fields = [
            {"name": "platform", "label": "平台", "type": "text", "required": True},
            {"name": "url", "label": "网址", "type": "text"},
            {"name": "username", "label": "账号", "type": "text"},
            {"name": "password", "label": "密码", "type": "text", "show": "*", "required": True},
            {"name": "note", "label": "备注", "type": "text"},
        ]
        FormDialog(self, "添加密码", fields, on_save=self._do_add)

    def _do_add(self, data: dict) -> None:
        try:
            self.manager.add_entry(
                platform=data["platform"], url=data.get("url", ""),
                username=data.get("username", ""),
                password=data["password"],
                note=data.get("note", "")
            )
            self.refresh()
            self.set_status(f"密码「{data['platform']}」已添加")
        except Exception as e:
            messagebox.showerror("添加失败", str(e))

    # ---- 查看密码 ----

    def _view_password(self) -> None:
        entry = self._get_selected()
        if not entry:
            return
        try:
            plain = self.manager.get_decrypted_password(entry.id)
            messagebox.showinfo(
                f"查看密码 - {entry.platform}",
                f"平台：{entry.platform}\n账号：{entry.username}\n密码：{plain}"
            )
        except Exception as e:
            messagebox.showerror("查看失败", str(e))

    # ---- 复制密码 ----

    def _copy_password(self) -> None:
        entry = self._get_selected()
        if not entry:
            return
        try:
            plain = self.manager.get_decrypted_password(entry.id)
            self.clipboard_clear()
            self.clipboard_append(plain)
            self.set_status(f"密码「{entry.platform}」已复制到剪贴板")
        except Exception as e:
            messagebox.showerror("复制失败", str(e))

    # ---- 编辑 ----

    def _open_edit_dialog(self) -> None:
        entry = self._get_selected()
        if not entry:
            return

        fields = [
            {"name": "platform", "label": "平台", "type": "text", "required": True},
            {"name": "url", "label": "网址", "type": "text"},
            {"name": "username", "label": "账号", "type": "text"},
            {"name": "password", "label": "密码（留空不修改）", "type": "text", "show": "*"},
            {"name": "note", "label": "备注", "type": "text"},
        ]
        initial = {
            "platform": entry.platform, "url": entry.url,
            "username": entry.username, "note": entry.note,
        }
        FormDialog(self, "编辑密码", fields,
                   on_save=lambda d: self._do_edit(entry.id, d),
                   initial_data=initial)

    def _do_edit(self, entry_id: str, data: dict) -> None:
        try:
            updates = {
                "platform": data["platform"], "url": data.get("url", ""),
                "username": data.get("username", ""),
                "note": data.get("note", ""),
            }
            if data.get("password"):
                updates["password"] = data["password"]
            self.manager.update_entry(entry_id, **updates)
            self.refresh()
            self.set_status(f"密码「{data['platform']}」已更新")
        except Exception as e:
            messagebox.showerror("编辑失败", str(e))

    # ---- 删除 ----

    def _confirm_delete(self) -> None:
        entry = self._get_selected()
        if not entry:
            return
        if ConfirmDialog.show(self, "确认删除",
                              f"确定要删除「{entry.platform}」的密码记录吗？"):
            self.manager.delete_entry(entry.id)
            self.refresh()
            self.set_status(f"密码「{entry.platform}」已删除")

    # ---- 搜索 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self.refresh()
            return
        results = self.manager.search(keyword)
        self._populate_tree(results)

    # ---- 数据加载 ----

    def refresh(self) -> None:
        entries = self.manager.get_all()
        self._populate_tree(entries)
        self.stats_var.set(f"共 {self.manager.count()} 条密码记录")

    def _populate_tree(self, entries: list[PasswordEntry]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for e in entries:
            self.tree.insert("", tk.END, iid=e.id, values=(
                e.platform, e.url, e.username, e.note,
                e.updated_at[:10] if e.updated_at else e.created_at[:10],
            ))

    def _get_selected(self) -> PasswordEntry | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选中一条记录")
            return None
        return self.manager.get_by_id(selection[0])
