"""密码管理页面。"""

import tkinter as tk
from tkinter import ttk, messagebox

from Services.PasswordManager import PasswordManager
from Services.CryptoService import CryptoService
from Models.Password import PasswordEntry
from .BasePage import BasePage
from .Widgets import SearchBar, FormDialog, ConfirmDialog


class PasswordPage(BasePage):
    """密码管理页面，密码不明文显示在列表中。"""

    def __init__(self, parent: tk.Widget, set_status):
        super().__init__(parent, set_status)
        self.manager = PasswordManager()

        self._build_toolbar()
        self._build_table()
        self._build_context_menu([
            ("查看密码", self._view_password),
            ("复制密码", self._copy_password),
            ("---", None),
            ("编辑", self._open_edit_dialog),
            ("---", None),
            ("删除", self._confirm_delete),
        ])
        self._build_stats_bar()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self, bg="#fafafa", pady=8)
        toolbar.pack(fill=tk.X, padx=12, pady=(12, 0))

        self.search_bar = SearchBar(toolbar, on_search=self._on_search)
        self.search_bar.pack(side=tk.LEFT, padx=4)

        # 主密码设置/解锁按钮
        self._update_master_pwd_btn(toolbar)

        add_btn = tk.Button(
            toolbar, text="+ 添加密码", command=self._open_add_dialog,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        add_btn.pack(side=tk.RIGHT, padx=4)

    def _update_master_pwd_btn(self, toolbar: tk.Frame | None = None) -> None:
        """根据主密码状态更新工具栏按钮。"""
        if toolbar is None:
            return
        # 移除旧按钮（如果存在）
        if hasattr(self, "master_pwd_btn"):
            self.master_pwd_btn.destroy()

        if not CryptoService.is_configured():
            text = "设置主密码"
            cmd = self._show_setup_dialog
        elif not CryptoService.is_unlocked():
            text = "解锁主密码"
            cmd = self._show_unlock_dialog
        else:
            text = "已解锁"
            cmd = lambda: messagebox.showinfo("主密码", "主密码已解锁，密码功能可用。")

        self.master_pwd_btn = tk.Button(
            toolbar, text=text, command=cmd,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        self.master_pwd_btn.pack(side=tk.RIGHT, padx=4)

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

    # ---- 主密码管理 ----

    def _ensure_crypto_ready(self) -> bool:
        """确保主密码已设置且已解锁。返回 True 表示可用。"""
        if not CryptoService.is_configured():
            result = messagebox.askyesno(
                "未设置主密码",
                "密码管理功能需要先设置主密码来保护您的数据安全。\n\n"
                "是否现在设置主密码？"
            )
            if result:
                self._show_setup_dialog()
                return CryptoService.is_unlocked()
            return False

        if not CryptoService.is_unlocked():
            result = messagebox.askyesno(
                "主密码已锁定",
                "主密码未解锁，无法操作密码数据。\n\n是否现在解锁？"
            )
            if result:
                self._show_unlock_dialog()
                return CryptoService.is_unlocked()
            return False

        return True

    def _show_setup_dialog(self) -> None:
        """显示主密码设置对话框。"""
        dialog = tk.Toplevel(self)
        dialog.title("设置主密码")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        dialog.geometry("350x200")
        self._center_dialog(dialog)

        frame = tk.Frame(dialog, padx=20, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame, text="请设置主密码（至少 4 位）：",
            font=("Microsoft YaHei", 10)
        ).pack(anchor=tk.W, pady=(0, 10))

        tk.Label(frame, text="主密码：", font=("Microsoft YaHei", 9)).pack(anchor=tk.W)
        pwd_var = tk.StringVar()
        pwd_entry = tk.Entry(frame, textvariable=pwd_var, show="*",
                             font=("Microsoft YaHei", 11))
        pwd_entry.pack(fill=tk.X, pady=(2, 8))
        dialog.after_idle(pwd_entry.focus_set)

        tk.Label(frame, text="确认密码：", font=("Microsoft YaHei", 9)).pack(anchor=tk.W)
        confirm_var = tk.StringVar()
        confirm_entry = tk.Entry(frame, textvariable=confirm_var, show="*",
                                 font=("Microsoft YaHei", 11))
        confirm_entry.pack(fill=tk.X, pady=(2, 8))

        error_var = tk.StringVar()
        error_label = tk.Label(
            frame, textvariable=error_var,
            font=("Microsoft YaHei", 9), fg="red"
        )
        error_label.pack(anchor=tk.W)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        def do_setup():
            pwd = pwd_var.get()
            confirm = confirm_var.get()
            try:
                CryptoService.setup_master_password(pwd, confirm)
                dialog.destroy()
                self._update_master_pwd_btn()
                self.set_status("主密码已设置，密码数据已加密保护")
                # 检查是否有待迁移的旧密码
                pending = self.manager.migrate_from_base64()
                if pending > 0:
                    self.set_status(f"主密码已设置，{pending} 条旧密码已升级加密")
            except ValueError as e:
                error_var.set(str(e))

        cancel_btn = tk.Button(
            btn_frame, text="取消", command=dialog.destroy,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT)

        save_btn = tk.Button(
            btn_frame, text="设置", command=do_setup,
            font=("Microsoft YaHei", 9), padx=16, cursor="hand2"
        )
        save_btn.pack(side=tk.RIGHT)

        confirm_entry.bind("<Return>", lambda e: do_setup())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        self.wait_window(dialog)

    def _show_unlock_dialog(self) -> None:
        """显示主密码解锁对话框。"""
        dialog = tk.Toplevel(self)
        dialog.title("解锁主密码")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        dialog.geometry("320x140")
        self._center_dialog(dialog)

        frame = tk.Frame(dialog, padx=20, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame, text="请输入主密码：",
            font=("Microsoft YaHei", 10)
        ).pack(anchor=tk.W, pady=(0, 10))

        pwd_var = tk.StringVar()
        pwd_entry = tk.Entry(frame, textvariable=pwd_var, show="*",
                             font=("Microsoft YaHei", 11), width=30)
        pwd_entry.pack(fill=tk.X, pady=(0, 12))
        dialog.after_idle(pwd_entry.focus_set)

        error_var = tk.StringVar()
        error_label = tk.Label(
            frame, textvariable=error_var,
            font=("Microsoft YaHei", 9), fg="red"
        )
        error_label.pack(anchor=tk.W)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        def do_unlock():
            pwd = pwd_var.get()
            if CryptoService.unlock(pwd):
                dialog.destroy()
                self._update_master_pwd_btn()
                self.set_status("主密码已解锁")
            else:
                error_var.set("主密码错误，请重试")
                pwd_var.set("")

        cancel_btn = tk.Button(
            btn_frame, text="取消", command=dialog.destroy,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT)

        unlock_btn = tk.Button(
            btn_frame, text="解锁", command=do_unlock,
            font=("Microsoft YaHei", 9), padx=16, cursor="hand2"
        )
        unlock_btn.pack(side=tk.RIGHT)

        pwd_entry.bind("<Return>", lambda e: do_unlock())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        self.wait_window(dialog)

    def _center_dialog(self, dialog: tk.Toplevel) -> None:
        """将对话框居中于父窗口。"""
        dialog.update_idletasks()
        pw = dialog.winfo_width()
        ph = dialog.winfo_height()
        parent = self.winfo_toplevel()
        x = parent.winfo_x() + (parent.winfo_width() - pw) // 2
        y = parent.winfo_y() + (parent.winfo_height() - ph) // 2
        dialog.geometry(f"+{x}+{y}")

    # ---- 添加 ----

    def _open_add_dialog(self) -> None:
        if not self._ensure_crypto_ready():
            return
        fields = [
            {"name": "platform", "label": "平台", "type": "text", "required": True},
            {"name": "url", "label": "网址", "type": "text"},
            {"name": "username", "label": "账号", "type": "text"},
            {"name": "password", "label": "密码", "type": "text", "show": "*", "required": True},
            {"name": "note", "label": "备注", "type": "text"},
        ]
        FormDialog(self, "添加密码", fields, on_save=self._do_add)

    def _do_add(self, data: dict) -> None:
        if not self._ensure_crypto_ready():
            return
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
        if not self._ensure_crypto_ready():
            return
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
        if not self._ensure_crypto_ready():
            return
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
        if not self._ensure_crypto_ready():
            return
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
        if not self._ensure_crypto_ready():
            return
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
        self._update_master_pwd_btn()

    def _populate_tree(self, entries: list[PasswordEntry]) -> None:
        self._clear_tree()
        for e in entries:
            self.tree.insert("", tk.END, iid=e.id, values=(
                e.platform, e.url, e.username, e.note,
                e.updated_at[:10] if e.updated_at else e.created_at[:10],
            ))

    def _get_selected(self) -> PasswordEntry | None:
        entry_id = self._get_selected_id()
        if not entry_id:
            return None
        return self.manager.get_by_id(entry_id)
