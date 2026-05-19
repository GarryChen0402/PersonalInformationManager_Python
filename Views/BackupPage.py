"""数据备份与恢复页面。"""

import tkinter as tk
from tkinter import ttk, messagebox

from Services.BackupManager import BackupManager
from .Widgets import ConfirmDialog


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


class BackupPage(tk.Frame):
    """数据管理页面，备份列表 + 操作按钮。"""

    def __init__(self, parent: tk.Widget, set_status):
        super().__init__(parent, bg="#ffffff")
        self.manager = BackupManager()
        self.set_status = set_status

        self._build_header()
        self._build_table()
        self._build_actions()

    # ---- 头部 ----

    def _build_header(self) -> None:
        header = tk.Frame(self, bg="#fafafa", pady=10)
        header.pack(fill=tk.X, padx=12, pady=(12, 0))

        tk.Label(header, text="数据管理", bg="#fafafa",
                 font=("Microsoft YaHei", 16, "bold")).pack(side=tk.LEFT)

        create_btn = tk.Button(
            header, text="+ 创建备份", command=self._create_backup,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        create_btn.pack(side=tk.RIGHT)

    # ---- 表格 ----

    def _build_table(self) -> None:
        columns = ("name", "created_at", "size")
        self.tree = ttk.Treeview(self, columns=columns, show="headings",
                                 selectmode="browse")

        self.tree.heading("name", text="文件名")
        self.tree.heading("created_at", text="创建时间")
        self.tree.heading("size", text="大小")

        self.tree.column("name", width=280)
        self.tree.column("created_at", width=150, anchor=tk.CENTER)
        self.tree.column("size", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12), pady=8)

    # ---- 操作按钮 ----

    def _build_actions(self) -> None:
        actions = tk.Frame(self, bg="#f5f5f5", pady=8)
        actions.pack(fill=tk.X, side=tk.BOTTOM)

        btn_configs = [
            ("查看详情", self._show_detail),
            ("恢复全部", self._restore_all),
            ("恢复选择...", self._restore_selected),
            ("删除备份", self._delete_backup),
        ]

        for text, cmd in btn_configs:
            btn = tk.Button(
                actions, text=text, command=cmd,
                font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
            )
            btn.pack(side=tk.LEFT, padx=4)

    # ---- 操作 ----

    def _create_backup(self) -> None:
        try:
            path = self.manager.create_backup()
            self.refresh()
            self.set_status(f"备份已创建: {path}")
        except Exception as e:
            messagebox.showerror("备份失败", str(e))

    def _show_detail(self) -> None:
        backup = self._get_selected()
        if not backup:
            return
        info = self.manager.get_backup_info(backup["path"])
        if not info:
            messagebox.showerror("错误", "无法读取备份文件")
            return

        lines = [f"备份文件: {backup['name']}\n"]
        for module, detail in info.items():
            if isinstance(detail, int):
                lines.append(f"  {module}: {detail} 条记录")
            else:
                lines.append(f"  {module}: {detail}")
        messagebox.showinfo("备份详情", "\n".join(lines))

    def _restore_all(self) -> None:
        backup = self._get_selected()
        if not backup:
            return
        if not ConfirmDialog.show(
            self, "确认恢复",
            f"确定要从「{backup['name']}」恢复全部数据吗？\n此操作将覆盖当前数据。"
        ):
            return

        try:
            result = self.manager.restore_backup(backup["path"])
            msg = f"成功恢复: {', '.join(result['success'])}"
            if result["failed"]:
                msg += f"\n失败: {', '.join(result['failed'])}"
            messagebox.showinfo("恢复完成", msg + "\n\n建议重启程序以刷新所有页面。")
            self.set_status("数据已恢复，建议重启程序")
        except Exception as e:
            messagebox.showerror("恢复失败", str(e))

    def _restore_selected(self) -> None:
        backup = self._get_selected()
        if not backup:
            return

        info = self.manager.get_backup_info(backup["path"])
        if not info:
            messagebox.showerror("错误", "无法读取备份文件")
            return

        # 弹出模块选择对话框
        dialog = tk.Toplevel(self)
        dialog.title("选择恢复模块")
        dialog.resizable(False, False)
        dialog.transient(self)
        dialog.grab_set()

        tk.Label(dialog, text="请选择要恢复的模块：",
                 font=("Microsoft YaHei", 10), pady=8).pack()

        vars_dict = {}
        module_names = {"profile": "个人档案", "skills": "技能", "status": "状态",
                        "knowledge": "知识", "passwords": "密码"}

        for mod_key, mod_label in module_names.items():
            if mod_key in info:
                var = tk.BooleanVar(value=True)
                vars_dict[mod_key] = var
                detail = info[mod_key]
                detail_text = f"{detail} 条记录" if isinstance(detail, int) else detail
                cb = tk.Checkbutton(
                    dialog, text=f"{mod_label} ({detail_text})",
                    variable=var, font=("Microsoft YaHei", 9)
                )
                cb.pack(anchor=tk.W, padx=20, pady=2)

        btn_frame = tk.Frame(dialog, pady=10)
        btn_frame.pack()

        def do_restore():
            selected = [k for k, v in vars_dict.items() if v.get()]
            if not selected:
                messagebox.showwarning("提示", "请至少选择一个模块")
                return
            try:
                result = self.manager.restore_backup(backup["path"], modules=selected)
                msg = f"成功恢复: {', '.join(result['success'])}"
                if result["failed"]:
                    msg += f"\n失败: {', '.join(result['failed'])}"
                messagebox.showinfo("恢复完成", msg)
                self.set_status("部分数据已恢复")
            except Exception as e:
                messagebox.showerror("恢复失败", str(e))
            dialog.destroy()

        cancel_btn = tk.Button(btn_frame, text="取消", command=dialog.destroy,
                               font=("Microsoft YaHei", 9), padx=12, cursor="hand2")
        cancel_btn.pack(side=tk.LEFT, padx=8)

        restore_btn = tk.Button(btn_frame, text="恢复", command=do_restore,
                                font=("Microsoft YaHei", 9), padx=12, cursor="hand2")
        restore_btn.pack(side=tk.LEFT)

    def _delete_backup(self) -> None:
        backup = self._get_selected()
        if not backup:
            return
        if ConfirmDialog.show(self, "确认删除",
                              f"确定要删除备份「{backup['name']}」吗？"):
            self.manager.delete_backup(backup["path"])
            self.refresh()
            self.set_status(f"备份「{backup['name']}」已删除")

    # ---- 数据加载 ----

    def refresh(self) -> None:
        backups = self.manager.list_backups()
        for item in self.tree.get_children():
            self.tree.delete(item)
        for b in backups:
            self.tree.insert("", tk.END, values=(
                b["name"], b["created_at"], _format_size(b["size"])
            ), iid=b["path"])

    def _get_selected(self) -> dict | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选中一个备份文件")
            return None
        for b in self.manager.list_backups():
            if b["path"] == selection[0]:
                return b
        return None
