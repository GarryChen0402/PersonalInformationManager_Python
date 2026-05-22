"""待办事项管理页面。"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime

from Services.TodoManager import TodoManager
from Models.TodoItem import TodoItem
from .Widgets import SearchBar, FormDialog, ConfirmDialog, CSVPreviewDialog

PRIORITY_LABELS = {"high": "高", "mid": "中", "low": "低"}


class TodoPage(tk.Frame):
    """待办事项管理页面，三段式布局。"""

    def __init__(self, parent: tk.Widget, set_status):
        super().__init__(parent, bg="#ffffff")
        self.manager = TodoManager()
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

        tk.Label(toolbar, text="状态：", bg="#fafafa",
                 font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(8, 2))
        self.status_filter = ttk.Combobox(
            toolbar, values=["全部", "未完成", "已完成"],
            state="readonly", width=8, font=("Microsoft YaHei", 9)
        )
        self.status_filter.pack(side=tk.LEFT, padx=4)
        self.status_filter.set("未完成")
        self.status_filter.bind("<<ComboboxSelected>>", lambda e: self._on_filter())

        tk.Label(toolbar, text="优先级：", bg="#fafafa",
                 font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(8, 2))
        self.priority_filter = ttk.Combobox(
            toolbar, values=["全部", "高", "中", "低"],
            state="readonly", width=6, font=("Microsoft YaHei", 9)
        )
        self.priority_filter.pack(side=tk.LEFT, padx=4)
        self.priority_filter.set("全部")
        self.priority_filter.bind("<<ComboboxSelected>>", lambda e: self._on_filter())

        tk.Label(toolbar, text="类别：", bg="#fafafa",
                 font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(8, 2))
        self.category_filter = ttk.Combobox(
            toolbar, state="readonly", width=8, font=("Microsoft YaHei", 9)
        )
        self.category_filter.pack(side=tk.LEFT, padx=4)
        self.category_filter.bind("<<ComboboxSelected>>", lambda e: self._on_filter())

        del_done_btn = tk.Button(
            toolbar, text="删除已完成", command=self._batch_delete_completed,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        del_done_btn.pack(side=tk.RIGHT, padx=4)

        import_btn = tk.Button(
            toolbar, text="导入CSV", command=self._import_csv,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        import_btn.pack(side=tk.RIGHT, padx=4)

        export_btn = tk.Button(
            toolbar, text="导出CSV", command=self._export_csv,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        export_btn.pack(side=tk.RIGHT, padx=4)

        add_btn = tk.Button(
            toolbar, text="+ 添加待办", command=self._open_add_dialog,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        add_btn.pack(side=tk.RIGHT, padx=4)

    # ---- 表格 ----

    def _build_table(self) -> None:
        columns = ("completed", "title", "priority", "category", "due_date", "created")
        self.tree = ttk.Treeview(self, columns=columns, show="headings",
                                 selectmode="browse")

        self.tree.heading("completed", text="✓")
        self.tree.heading("title", text="标题")
        self.tree.heading("priority", text="优先级")
        self.tree.heading("category", text="类别")
        self.tree.heading("due_date", text="截止日期")
        self.tree.heading("created", text="创建时间")

        self.tree.column("completed", width=30, anchor=tk.CENTER)
        self.tree.column("title", width=200)
        self.tree.column("priority", width=60, anchor=tk.CENTER)
        self.tree.column("category", width=80, anchor=tk.CENTER)
        self.tree.column("due_date", width=90, anchor=tk.CENTER)
        self.tree.column("created", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12), pady=8)

        # 颜色标签
        self.tree.tag_configure("overdue", foreground="#c0392b")
        self.tree.tag_configure("high_priority", background="#fef0e7")
        self.tree.tag_configure("completed", foreground="#999999")

        self.tree.bind("<Double-1>", lambda e: self._toggle_complete())

    # ---- 右键菜单 ----

    def _build_context_menu(self) -> None:
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="切换完成状态", command=self._toggle_complete)
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
        today = datetime.now().strftime("%Y-%m-%d")
        fields = [
            {"name": "title", "label": "标题", "type": "text", "required": True},
            {"name": "priority", "label": "优先级", "type": "combobox",
             "options": ["mid", "high", "low"]},
            {"name": "category", "label": "类别", "type": "combobox",
             "options": self.manager.VALID_CATEGORIES},
            {"name": "due_date", "label": "截止日期", "type": "text"},
            {"name": "description", "label": "描述", "type": "textarea"},
        ]
        FormDialog(self, "添加待办", fields, on_save=self._do_add,
                   initial_data={"priority": "mid", "due_date": ""})

    def _do_add(self, data: dict) -> None:
        try:
            self.manager.add_todo(
                title=data["title"],
                description=data.get("description", ""),
                priority=data.get("priority", "mid"),
                due_date=data.get("due_date", ""),
                category=data.get("category", ""),
            )
            self.refresh()
            self.set_status(f"待办「{data['title']}」已添加")
        except Exception as e:
            messagebox.showerror("添加失败", str(e))

    # ---- 切换完成 ----

    def _toggle_complete(self) -> None:
        item = self._get_selected()
        if not item:
            return
        try:
            updated = self.manager.toggle_complete(item.id)
            action = "已完成" if updated.completed else "已取消完成"
            self.refresh()
            self.set_status(f"待办「{updated.title}」{action}")
        except Exception as e:
            messagebox.showerror("操作失败", str(e))

    # ---- 编辑 ----

    def _open_edit_dialog(self) -> None:
        item = self._get_selected()
        if not item:
            return

        fields = [
            {"name": "title", "label": "标题", "type": "text", "required": True},
            {"name": "priority", "label": "优先级", "type": "combobox",
             "options": self.manager.VALID_PRIORITIES},
            {"name": "category", "label": "类别", "type": "combobox",
             "options": self.manager.VALID_CATEGORIES},
            {"name": "due_date", "label": "截止日期", "type": "text"},
            {"name": "description", "label": "描述", "type": "textarea"},
        ]
        initial = {
            "title": item.title,
            "priority": item.priority,
            "category": item.category,
            "due_date": item.due_date,
            "description": item.description,
        }
        FormDialog(self, "编辑待办", fields,
                   on_save=lambda d: self._do_edit(item.id, d),
                   initial_data=initial)

    def _do_edit(self, todo_id: str, data: dict) -> None:
        try:
            self.manager.update_todo(
                todo_id,
                title=data["title"],
                description=data.get("description", ""),
                priority=data.get("priority", "mid"),
                due_date=data.get("due_date", ""),
                category=data.get("category", ""),
            )
            self.refresh()
            self.set_status(f"待办「{data['title']}」已更新")
        except Exception as e:
            messagebox.showerror("编辑失败", str(e))

    # ---- 删除 ----

    def _confirm_delete(self) -> None:
        item = self._get_selected()
        if not item:
            return
        if ConfirmDialog.show(self, "确认删除",
                              f"确定要删除待办「{item.title}」吗？"):
            self.manager.delete_todo(item.id)
            self.refresh()
            self.set_status(f"待办「{item.title}」已删除")

    def _batch_delete_completed(self) -> None:
        count = self.manager.batch_delete_completed()
        if count > 0:
            self.refresh()
            self.set_status(f"已删除 {count} 条已完成的待办")
        else:
            messagebox.showinfo("提示", "没有已完成的待办")

    # ---- 搜索和筛选 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self.refresh()
            return
        results = self.manager.search(keyword)
        self._populate_tree(results)

    def _on_filter(self) -> None:
        self._refresh_tree()

    # ---- 数据加载 ----

    def refresh(self) -> None:
        self._refresh_tree()
        self._update_filter_options()
        self._update_stats()

    def _refresh_tree(self) -> None:
        status_val = self.status_filter.get()
        status = None
        if status_val == "未完成":
            status = "active"
        elif status_val == "已完成":
            status = "completed"

        items = self.manager.get_all(status=status)

        # 优先级筛选
        prio_val = self.priority_filter.get()
        if prio_val in ("高", "中", "低"):
            prio_map = {"高": "high", "中": "mid", "低": "low"}
            items = [i for i in items if i.priority == prio_map[prio_val]]

        # 类别筛选
        cat_val = self.category_filter.get()
        if cat_val and cat_val != "全部":
            items = [i for i in items if i.category == cat_val]

        self._populate_tree(items)

    def _populate_tree(self, items: list[TodoItem]) -> None:
        for row in self.tree.get_children():
            self.tree.delete(row)

        for item in items:
            tags = []
            if item.completed:
                tags.append("completed")
            elif item.is_overdue():
                tags.append("overdue")
            elif item.priority == "high":
                tags.append("high_priority")

            self.tree.insert("", tk.END, iid=item.id, values=(
                "✓" if item.completed else "☐",
                item.title,
                PRIORITY_LABELS.get(item.priority, item.priority),
                item.category or "-",
                item.due_date or "-",
                item.created_at[:10] if item.created_at else "-",
            ), tags=tuple(tags))

    def _update_filter_options(self) -> None:
        all_items = self.manager.get_all()
        categories = sorted({i.category for i in all_items if i.category})
        self.category_filter["values"] = ["全部"] + categories
        if not self.category_filter.get():
            self.category_filter.set("全部")

    def _update_stats(self) -> None:
        stats = self.manager.get_statistics()
        parts = [f"共 {stats['total']} 条"]
        if stats["active"] > 0:
            parts.append(f"待完成: {stats['active']}")
        if stats["completed"] > 0:
            parts.append(f"已完成: {stats['completed']}")
        if stats["overdue"] > 0:
            parts.append(f"逾期: {stats['overdue']}")
        self.stats_var.set("  |  ".join(parts))

    def _get_selected(self) -> TodoItem | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选中一条记录")
            return None
        return self.manager.get_by_id(selection[0])

    def highlight_item(self, item_id: str) -> None:
        """定位并高亮指定条目。"""
        if not self.tree.exists(item_id):
            return
        self.tree.selection_set(item_id)
        self.tree.see(item_id)
        self.tree.focus(item_id)

    # ---- CSV 导入导出 ----

    def _export_csv(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV 文件", "*.csv")],
            initialfile="todos.csv"
        )
        if path:
            try:
                self.manager.export_csv(path)
                self.set_status(f"待办数据已导出到 {path}")
            except Exception as e:
                messagebox.showerror("导出失败", str(e))

    def _import_csv(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("CSV 文件", "*.csv")]
        )
        if path:
            CSVPreviewDialog(self, path, on_confirm=self._do_import_csv)

    def _do_import_csv(self, path: str) -> None:
        try:
            result = self.manager.import_csv(path)
            self.refresh()
            msg = f"导入完成：成功 {result['success']} 条"
            if result["failed"]:
                msg += f"，失败 {result['failed']} 条"
            self.set_status(msg)
        except Exception as e:
            messagebox.showerror("导入失败", str(e))
