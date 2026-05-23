"""习惯追踪页面。"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from Services.HabitManager import HabitManager
from .BasePage import BasePage
from .Widgets import SearchBar, FormDialog, ConfirmDialog
from .ChartWidgets import CalendarHeatmap


class HabitPage(BasePage):
    """习惯追踪页面，左右分栏布局。"""

    def __init__(self, parent: tk.Widget, set_status):
        super().__init__(parent, set_status)
        self.manager = HabitManager()

        # 右栏先创建占位
        self._build_toolbar()
        self._build_body()
        self._build_stats_bar()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self, bg="#fafafa", pady=8)
        toolbar.pack(fill=tk.X, padx=12, pady=(12, 0))

        self.search_bar = SearchBar(toolbar, on_search=self._on_search)
        self.search_bar.pack(side=tk.LEFT, padx=4)

        # 类别筛选
        tk.Label(toolbar, text="类别", font=("Microsoft YaHei", 9),
                 bg=toolbar["bg"]).pack(side=tk.LEFT, padx=(8, 2))
        self.category_var = tk.StringVar(value="全部")
        self.category_combo = ttk.Combobox(
            toolbar, textvariable=self.category_var, state="readonly",
            values=["全部"] + HabitManager.VALID_CATEGORIES, width=8
        )
        self.category_combo.pack(side=tk.LEFT, padx=2)
        self.category_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        # 状态筛选
        tk.Label(toolbar, text="状态", font=("Microsoft YaHei", 9),
                 bg=toolbar["bg"]).pack(side=tk.LEFT, padx=(8, 2))
        self.status_var = tk.StringVar(value="活跃")
        self.status_combo = ttk.Combobox(
            toolbar, textvariable=self.status_var, state="readonly",
            values=["活跃", "已归档"], width=6
        )
        self.status_combo.pack(side=tk.LEFT, padx=2)
        self.status_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh())

        add_btn = tk.Button(
            toolbar, text="+ 添加习惯", command=self._open_add_dialog,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        add_btn.pack(side=tk.RIGHT, padx=4)

    # ---- 主体布局 ----

    def _build_body(self) -> None:
        """左右分栏：习惯列表 + 详情面板。"""
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)

        # 左栏 — 习惯列表
        left = tk.Frame(paned, bg=self["bg"])
        paned.add(left, width=280, minsize=200)

        self._build_table(left)

        # 右栏 — 详情面板
        self.right_frame = tk.Frame(paned, bg=self["bg"])
        paned.add(self.right_frame, width=400, minsize=300)
        self._build_detail_panel()

    # ---- 习惯列表 ----

    def _build_table(self, parent: tk.Frame) -> None:
        columns = ("check", "name", "streak")
        self.tree = ttk.Treeview(parent, columns=columns, show="headings",
                                 selectmode="browse", height=12)

        self.tree.heading("check", text="☑")
        self.tree.heading("name", text="习惯")
        self.tree.heading("streak", text="连续")

        self.tree.column("check", width=30, anchor=tk.CENTER)
        self.tree.column("name", width=160)
        self.tree.column("streak", width=60, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 双击打卡/撤销
        self.tree.bind("<Double-1>", self._on_tree_double_click)
        # 空格键打卡/撤销
        self.tree.bind("<space>", self._on_tree_double_click)
        # 选中查看详情
        self.tree.bind("<<TreeviewSelect>>", self._on_habit_select)

    # ---- 详情面板 ----

    def _build_detail_panel(self) -> None:
        """右栏详情面板。"""
        # 标题
        self.detail_title = tk.Label(
            self.right_frame, text="选择一个习惯",
            font=("Microsoft YaHei", 12, "bold"),
            bg=self["bg"], anchor=tk.W
        )
        self.detail_title.pack(fill=tk.X, padx=16, pady=(16, 4))

        # 统计信息
        self.stats_frame = tk.Frame(self.right_frame, bg=self["bg"])
        self.stats_frame.pack(fill=tk.X, padx=16, pady=8)

        self.stats_labels: dict[str, tk.Label] = {}
        for key, text in [("current", "当前连续"), ("longest", "最长连续"),
                           ("total", "总打卡"), ("rate", "完成率")]:
            row = tk.Frame(self.stats_frame, bg=self["bg"])
            row.pack(fill=tk.X, pady=2)
            tk.Label(row, text=f"{text}：", font=("Microsoft YaHei", 10),
                     bg=self["bg"], fg="#666").pack(side=tk.LEFT)
            val_label = tk.Label(row, text="-", font=("Microsoft YaHei", 10, "bold"),
                                 bg=self["bg"])
            val_label.pack(side=tk.LEFT)
            self.stats_labels[key] = val_label

        # 热力图
        self.heatmap_frame = tk.Frame(self.right_frame, bg=self["bg"])
        self.heatmap_frame.pack(fill=tk.X, padx=16, pady=8)
        self.heatmap = CalendarHeatmap(self.heatmap_frame, height=130)
        self.heatmap.pack(fill=tk.X)

        # 操作按钮
        btn_frame = tk.Frame(self.right_frame, bg=self["bg"])
        btn_frame.pack(fill=tk.X, padx=16, pady=(8, 16))

        self.checkin_btn = tk.Button(
            btn_frame, text="✓ 打卡", command=self._do_check_in,
            font=("Microsoft YaHei", 10), padx=16, cursor="hand2",
            state=tk.DISABLED
        )
        self.checkin_btn.pack(side=tk.LEFT, padx=4)

        self.undo_btn = tk.Button(
            btn_frame, text="↩ 撤销", command=self._do_undo,
            font=("Microsoft YaHei", 10), padx=12, cursor="hand2",
            state=tk.DISABLED
        )
        self.undo_btn.pack(side=tk.LEFT, padx=4)

        edit_btn = tk.Button(
            btn_frame, text="编辑", command=self._open_edit_dialog,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2",
            state=tk.DISABLED
        )
        edit_btn.pack(side=tk.RIGHT, padx=4)
        self.edit_btn = edit_btn

        archive_btn = tk.Button(
            btn_frame, text="归档", command=self._do_archive,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2",
            state=tk.DISABLED
        )
        archive_btn.pack(side=tk.RIGHT, padx=4)
        self.archive_btn = archive_btn

    # ---- 对话框 ----

    def _open_add_dialog(self) -> None:
        fields = [
            {"name": "name", "label": "习惯名称", "type": "text", "required": True},
            {"name": "frequency", "label": "频率", "type": "combobox",
             "options": [("每天", "daily"), ("每周", "weekly"), ("自定义天数", "custom")]},
            {"name": "custom_days", "label": "自定义天数（仅自定义频率时使用）", "type": "spinbox",
             "from_": 1, "to": 30},
            {"name": "target_count", "label": "每日目标次数", "type": "spinbox",
             "from_": 1, "to": 100},
            {"name": "category", "label": "类别", "type": "combobox",
             "options": HabitManager.VALID_CATEGORIES},
            {"name": "description", "label": "描述", "type": "text"},
            {"name": "color", "label": "热力图颜色", "type": "combobox",
             "options": [("蓝色", "#4a90d9"), ("绿色", "#27ae60"), ("橙色", "#e67e22"),
                         ("紫色", "#8e44ad"), ("红色", "#e74c3c")]},
        ]
        FormDialog(self, "添加习惯", fields, on_save=self._do_add)

    def _do_add(self, data: dict) -> None:
        try:
            freq = data.get("frequency", "daily")
            custom_days = int(data.get("custom_days", 1))
            target = int(data.get("target_count", 1))
            habit = self.manager.add_habit(
                name=data["name"], frequency=freq,
                custom_days=custom_days, target_count=target,
                category=data.get("category", ""),
                description=data.get("description", ""),
                color=data.get("color", "#4a90d9"),
            )
            self.refresh()
            self._select_habit(habit.id)
            self.set_status(f"习惯「{habit.name}」已创建")
        except Exception as e:
            messagebox.showerror("添加失败", str(e))

    def _open_edit_dialog(self) -> None:
        habit = self._get_selected_habit()
        if not habit:
            return
        fields = [
            {"name": "name", "label": "习惯名称", "type": "text", "required": True},
            {"name": "frequency", "label": "频率", "type": "combobox",
             "options": [("每天", "daily"), ("每周", "weekly"), ("自定义天数", "custom")]},
            {"name": "target_count", "label": "每日目标次数", "type": "spinbox",
             "from_": 1, "to": 100},
            {"name": "category", "label": "类别", "type": "combobox",
             "options": HabitManager.VALID_CATEGORIES},
            {"name": "description", "label": "描述", "type": "text"},
        ]
        initial = {
            "name": habit.name, "frequency": habit.frequency,
            "target_count": habit.target_count,
            "category": habit.category, "description": habit.description,
        }
        FormDialog(self, "编辑习惯", fields,
                   on_save=lambda d: self._do_edit(habit.id, d),
                   initial_data=initial)

    def _do_edit(self, habit_id: str, data: dict) -> None:
        try:
            freq = data.get("frequency", "daily")
            target = int(data.get("target_count", 1))
            self.manager.update_habit(
                habit_id, name=data["name"], frequency=freq,
                target_count=target, category=data.get("category", ""),
                description=data.get("description", ""),
            )
            self.refresh()
            self._select_habit(habit_id)
            self.set_status(f"习惯「{data['name']}」已更新")
        except Exception as e:
            messagebox.showerror("编辑失败", str(e))

    # ---- 打卡操作 ----

    def _on_tree_double_click(self, event=None) -> None:
        """双击切换打卡状态。"""
        habit = self._get_selected_habit()
        if not habit:
            return
        today = date.today().isoformat()
        if self.manager.is_checked_in(habit.id, today):
            self._do_undo()
        else:
            self._do_check_in()

    def _do_check_in(self) -> None:
        habit = self._get_selected_habit()
        if not habit:
            return
        try:
            self.manager.check_in(habit.id)
            self.refresh()
            self._select_habit(habit.id)
            self.set_status(f"「{habit.name}」打卡成功")
        except Exception as e:
            messagebox.showerror("打卡失败", str(e))

    def _do_undo(self) -> None:
        habit = self._get_selected_habit()
        if not habit:
            return
        today = date.today().isoformat()
        self.manager.undo_check_in(habit.id, today)
        self.refresh()
        self._select_habit(habit.id)
        self.set_status(f"「{habit.name}」打卡已撤销")

    def _do_archive(self) -> None:
        habit = self._get_selected_habit()
        if not habit:
            return
        action = "恢复" if habit.archived else "归档"
        if not ConfirmDialog.show(self, f"确认{action}", f"确定要{action}习惯「{habit.name}」吗？"):
            return
        if habit.archived:
            self.manager.unarchive_habit(habit.id)
        else:
            self.manager.archive_habit(habit.id)
        self.refresh()
        self.set_status(f"习惯「{habit.name}」已{action}")

    # ---- 详情面板更新 ----

    def _on_habit_select(self, event=None) -> None:
        """选中习惯时更新详情面板。"""
        habit = self._get_selected_habit()
        if not habit:
            self.detail_title.configure(text="选择一个习惯")
            for key in self.stats_labels:
                self.stats_labels[key].configure(text="-")
            self.checkin_btn.configure(state=tk.DISABLED)
            self.undo_btn.configure(state=tk.DISABLED)
            self.edit_btn.configure(state=tk.DISABLED)
            self.archive_btn.configure(state=tk.DISABLED)
            return

        self.detail_title.configure(text=habit.name)
        streak = self.manager.get_streak(habit.id)
        total = streak.get("total_checkins", 0)
        rate = streak.get("completion_rate", 0)

        self.stats_labels["current"].configure(text=f"{streak.get('current', 0)} 天")
        self.stats_labels["longest"].configure(text=f"{streak.get('longest', 0)} 天")
        self.stats_labels["total"].configure(text=f"{total} 次")
        self.stats_labels["rate"].configure(text=f"{rate:.0%}")

        # 加载热力图数据
        heatmap_data = self.manager.get_heatmap_data(habit.id)
        self.heatmap.set_data(heatmap_data)
        if habit.color and habit.color != "#4a90d9":
            self.heatmap.set_color_scheme(habit.color)

        today = date.today().isoformat()
        checked = self.manager.is_checked_in(habit.id, today)

        self.checkin_btn.configure(state=tk.NORMAL if not checked else tk.DISABLED)
        self.undo_btn.configure(state=tk.NORMAL if checked else tk.DISABLED)
        self.edit_btn.configure(state=tk.NORMAL)
        self.archive_btn.configure(
            state=tk.NORMAL,
            text="恢复" if habit.archived else "归档"
        )

    # ---- 数据刷新 ----

    def refresh(self) -> None:
        include_archived = self.status_var.get() == "已归档"
        category = self.category_var.get()

        habits = self.manager.get_all(include_archived=include_archived)
        if category != "全部":
            habits = [h for h in habits if h.category == category]

        self._populate_tree(habits)

        # 更新统计栏
        active = self.manager.get_active()
        today_stats = self.manager.get_today_stats()
        self.stats_var.set(
            f"活跃 {today_stats['total_active']} | "
            f"今日打卡 {today_stats['checked_today']}/{today_stats['total_active']}"
        )

        # 刷新详情
        self._on_habit_select()

    def _populate_tree(self, habits: list) -> None:
        self._clear_tree()
        today = date.today().isoformat()
        for h in habits:
            checked = "☑" if self.manager.is_checked_in(h.id, today) else "☐"
            streak = self.manager.get_streak(h.id)
            self.tree.insert("", tk.END, iid=h.id, values=(
                checked, h.name, f"{streak.get('current', 0)}天"
            ))

    # ---- 搜索 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self.refresh()
            return
        results = self.manager.search(keyword)
        self._populate_tree(results)

    # ---- 辅助方法 ----

    def _get_selected_habit(self):
        """获取当前选中的习惯对象。"""
        selection = self.tree.selection()
        if not selection:
            return None
        return self.manager.get_by_id(selection[0])

    def _select_habit(self, habit_id: str) -> None:
        """选中并滚动到指定习惯。"""
        if self.tree.exists(habit_id):
            self.tree.selection_set(habit_id)
            self.tree.focus(habit_id)
            self.tree.see(habit_id)
            self._on_habit_select()

    def highlight_item(self, item_id: str) -> None:
        self._select_habit(item_id)
