"""状态管理页面。"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta

from Services.StatusManager import StatusManager
from Models.Status import StatusRecord
from .Widgets import SearchBar, FormDialog, ConfirmDialog, DateRangePicker


COLOR_TAGS = {
    "low": ("#fde8e8", "#c0392b"),     # bg, fg for average < 3
    "mid": ("#fef9e7", "#b7950b"),     # bg, fg for 3-3.9
    "high": ("#e8f8f0", "#27ae60"),    # bg, fg for >= 4
}


class StatusPage(tk.Frame):
    """状态管理页面，三段式布局。"""

    def __init__(self, parent: tk.Widget, set_status):
        super().__init__(parent, bg="#ffffff")
        self.manager = StatusManager()
        self.set_status = set_status

        self._build_toolbar()
        self._build_table()
        self._build_context_menu()
        self._build_stats_bar()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self, bg="#fafafa", pady=8)
        toolbar.pack(fill=tk.X, padx=12, pady=(12, 0))

        self.date_picker = DateRangePicker(toolbar, on_query=self._on_date_range)
        self.date_picker.pack(side=tk.LEFT)

        add_btn = tk.Button(
            toolbar, text="+ 添加记录", command=self._open_add_dialog,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        add_btn.pack(side=tk.RIGHT, padx=4)

    # ---- 表格 ----

    def _build_table(self) -> None:
        columns = ("date", "mood", "energy", "focus", "weight", "sleep", "note")
        self.tree = ttk.Treeview(self, columns=columns, show="headings",
                                 selectmode="browse")

        self.tree.heading("date", text="日期")
        self.tree.heading("mood", text="心情")
        self.tree.heading("energy", text="精力")
        self.tree.heading("focus", text="专注度")
        self.tree.heading("weight", text="体重(kg)")
        self.tree.heading("sleep", text="睡眠(h)")
        self.tree.heading("note", text="备注")

        self.tree.column("date", width=100, anchor=tk.CENTER)
        self.tree.column("mood", width=60, anchor=tk.CENTER)
        self.tree.column("energy", width=60, anchor=tk.CENTER)
        self.tree.column("focus", width=60, anchor=tk.CENTER)
        self.tree.column("weight", width=80, anchor=tk.CENTER)
        self.tree.column("sleep", width=70, anchor=tk.CENTER)
        self.tree.column("note", width=150)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12), pady=8)

        # 颜色标签配置
        self.tree.tag_configure("low", background="#fde8e8", foreground="#c0392b")
        self.tree.tag_configure("mid", background="#fef9e7", foreground="#b7950b")
        self.tree.tag_configure("high", background="#e8f8f0", foreground="#27ae60")

        self.tree.bind("<Double-1>", lambda e: self._open_edit_dialog())

    # ---- 右键菜单 ----

    def _build_context_menu(self) -> None:
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="编辑", command=self._open_edit_dialog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=self._confirm_delete)

        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    # ---- 统计栏 ----

    def _build_stats_bar(self) -> None:
        self.stats_var = tk.StringVar()
        stats = tk.Label(
            self, textvariable=self.stats_var, bg="#f5f5f5",
            font=("Microsoft YaHei", 9), fg="#666666", pady=6
        )
        stats.pack(fill=tk.X, side=tk.BOTTOM)

    # ---- 添加 ----

    def _open_add_dialog(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        fields = [
            {"name": "date", "label": "日期", "type": "text", "required": True},
            {"name": "mood", "label": "心情(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"name": "energy", "label": "精力(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"name": "focus", "label": "专注度(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"name": "weight", "label": "体重(kg)", "type": "text"},
            {"name": "sleep_hours", "label": "睡眠(h)", "type": "text"},
            {"name": "note", "label": "备注", "type": "textarea"},
        ]
        initial = {"date": today, "mood": 3, "energy": 3, "focus": 3}
        FormDialog(self, "添加状态记录", fields, on_save=self._do_add,
                   initial_data=initial)

    def _do_add(self, data: dict) -> None:
        try:
            w = float(data["weight"]) if data["weight"] else 0.0
            s = float(data["sleep_hours"]) if data["sleep_hours"] else 0.0
            self.manager.add_record(
                date=data["date"],
                mood=int(data["mood"]),
                energy=int(data["energy"]),
                focus=int(data["focus"]),
                weight=w, sleep_hours=s,
                note=data.get("note", "")
            )
            self.refresh()
            self.set_status(f"状态记录「{data['date']}」已保存")
        except Exception as e:
            messagebox.showerror("添加失败", str(e))

    # ---- 编辑 ----

    def _open_edit_dialog(self) -> None:
        record = self._get_selected()
        if not record:
            return

        fields = [
            {"name": "date", "label": "日期", "type": "text", "required": True},
            {"name": "mood", "label": "心情(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"name": "energy", "label": "精力(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"name": "focus", "label": "专注度(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"name": "weight", "label": "体重(kg)", "type": "text"},
            {"name": "sleep_hours", "label": "睡眠(h)", "type": "text"},
            {"name": "note", "label": "备注", "type": "textarea"},
        ]
        initial = {
            "date": record.date,
            "mood": record.mood, "energy": record.energy, "focus": record.focus,
            "weight": str(record.weight) if record.weight else "",
            "sleep_hours": str(record.sleep_hours) if record.sleep_hours else "",
            "note": record.note,
        }
        FormDialog(self, "编辑状态记录", fields,
                   on_save=lambda d: self._do_edit(record.id, d),
                   initial_data=initial)

    def _do_edit(self, record_id: str, data: dict) -> None:
        try:
            self.manager.update_record(
                record_id,
                date=data["date"],
                mood=int(data["mood"]),
                energy=int(data["energy"]),
                focus=int(data["focus"]),
                weight=float(data["weight"]) if data["weight"] else 0.0,
                sleep_hours=float(data["sleep_hours"]) if data["sleep_hours"] else 0.0,
                note=data.get("note", "")
            )
            self.refresh()
            self.set_status(f"状态记录「{data['date']}」已更新")
        except Exception as e:
            messagebox.showerror("编辑失败", str(e))

    # ---- 删除 ----

    def _confirm_delete(self) -> None:
        record = self._get_selected()
        if not record:
            return
        if ConfirmDialog.show(self, "确认删除",
                              f"确定要删除「{record.date}」的状态记录吗？"):
            self.manager.delete_record(record.id)
            self.refresh()
            self.set_status(f"状态记录「{record.date}」已删除")

    # ---- 日期筛选 ----

    def _on_date_range(self, start: str, end: str) -> None:
        records = self.manager.get_by_date_range(start, end)
        self._populate_tree(records)

    # ---- 数据加载 ----

    def refresh(self) -> None:
        """重新加载状态记录和统计。"""
        records = self.manager.get_latest(30)
        self._populate_tree(records)

        # 设置默认日期范围
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        self.date_picker.set_range(start, end)

        # 统计栏
        stats = self.manager.get_statistics(period="week")
        if stats["count"] > 0:
            self.stats_var.set(
                f"本周({stats['count']}条)  |  "
                f"平均心情: {stats['mood']}/5  |  "
                f"平均精力: {stats['energy']}/5  |  "
                f"平均专注度: {stats['focus']}/5  |  "
                f"平均睡眠: {stats['sleep_hours']}h"
            )
        else:
            self.stats_var.set("本周暂无记录")

    def _populate_tree(self, records: list[StatusRecord]) -> None:
        """用记录列表填充 Treeview。"""
        for item in self.tree.get_children():
            self.tree.delete(item)

        for r in records:
            avg = (r.mood + r.energy + r.focus) / 3
            if avg < 3:
                tag = "low"
            elif avg < 4:
                tag = "mid"
            else:
                tag = "high"

            self.tree.insert("", tk.END, iid=r.id, values=(
                r.date,
                f"{r.mood}/5",
                f"{r.energy}/5",
                f"{r.focus}/5",
                f"{r.weight:.1f}" if r.weight else "-",
                f"{r.sleep_hours:.1f}" if r.sleep_hours else "-",
                r.note,
            ), tags=(tag,))

    def _get_selected(self) -> StatusRecord | None:
        """获取当前选中行的 StatusRecord 对象。"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选中一条记录")
            return None
        return self.manager.get_by_id(selection[0])
