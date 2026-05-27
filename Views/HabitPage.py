"""习惯追踪页面 — PySide6 版本。"""

from datetime import date

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton,
    QComboBox, QLabel, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt

from Services.HabitManager import HabitManager
from .BasePage import BasePage
from .Widgets import SearchBar, FormDialog, ConfirmDialog
from .ChartWidgets import CalendarHeatmap


class HabitPage(BasePage):
    """习惯追踪页面，左右分栏布局。"""

    def __init__(self, parent=None, set_status=None):
        super().__init__(parent, set_status)
        self.manager = HabitManager()

        self._build_toolbar()
        self._build_body()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 4, 0, 4)

        self.search_bar = SearchBar(placeholder="搜索习惯...")
        self.search_bar.search_requested.connect(self._on_search)
        toolbar_layout.addWidget(self.search_bar)

        toolbar_layout.addWidget(QLabel("类别"))
        self.category_filter = QComboBox()
        self.category_filter.addItems(["全部"] + HabitManager.VALID_CATEGORIES)
        self.category_filter.currentTextChanged.connect(lambda: self.refresh())
        toolbar_layout.addWidget(self.category_filter)

        toolbar_layout.addWidget(QLabel("状态"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["活跃", "已归档"])
        self.status_filter.currentTextChanged.connect(lambda: self.refresh())
        toolbar_layout.addWidget(self.status_filter)

        toolbar_layout.addStretch()

        add_btn = QPushButton("+ 添加习惯")
        add_btn.clicked.connect(self._open_add_dialog)
        toolbar_layout.addWidget(add_btn)

        self._layout.insertWidget(0, toolbar)

    # ---- 主体布局 ----

    def _build_body(self) -> None:
        body_widget = QWidget()
        body_layout = QHBoxLayout(body_widget)
        body_layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)

        # 左栏 — 习惯列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(0, 0, 0, 0)

        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["☑", "习惯", "连续"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._on_table_double_click)
        self.table.itemSelectionChanged.connect(self._on_habit_select)
        # 移除旧表格，用新的包裹
        from PySide6.QtWidgets import QHeaderView
        left_layout.addWidget(self.table)
        splitter.addWidget(left)

        # 右栏 — 详情面板
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(8)

        self._build_detail_panel(right_layout)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        body_layout.addWidget(splitter)
        # 替换原有表格位置
        self._layout.removeWidget(self.table)
        self._layout.removeWidget(self.stats_frame)
        self._layout.insertWidget(1, body_widget)
        self._layout.addWidget(self.stats_frame)

    def _build_detail_panel(self, layout: QVBoxLayout) -> None:
        self.detail_title = QLabel("选择一个习惯")
        self.detail_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.detail_title)

        # 统计信息
        stats_grid = QHBoxLayout()
        self.stats_labels: dict[str, QLabel] = {}
        for key in ["current", "longest", "total", "rate"]:
            pair_layout = QVBoxLayout()
            name_label = QLabel(
                {"current": "当前连续", "longest": "最长连续",
                 "total": "总打卡", "rate": "完成率"}[key]
            )
            name_label.setStyleSheet("color: #666; font-size: 10px;")
            pair_layout.addWidget(name_label)
            val_label = QLabel("-")
            val_label.setStyleSheet("font-size: 12px; font-weight: bold;")
            pair_layout.addWidget(val_label)
            self.stats_labels[key] = val_label
            stats_grid.addLayout(pair_layout)
        stats_grid.addStretch()
        layout.addLayout(stats_grid)

        # 热力图
        self.heatmap = CalendarHeatmap()
        self.heatmap.setMinimumHeight(130)
        layout.addWidget(self.heatmap)

        # 操作按钮
        btn_row = QHBoxLayout()
        self.checkin_btn = QPushButton("✓ 打卡")
        self.checkin_btn.clicked.connect(self._do_check_in)
        self.checkin_btn.setEnabled(False)
        btn_row.addWidget(self.checkin_btn)

        self.undo_btn = QPushButton("↩ 撤销")
        self.undo_btn.clicked.connect(self._do_undo)
        self.undo_btn.setEnabled(False)
        btn_row.addWidget(self.undo_btn)

        btn_row.addStretch()

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._open_edit_dialog)
        self.edit_btn.setEnabled(False)
        btn_row.addWidget(self.edit_btn)

        self.archive_btn = QPushButton("归档")
        self.archive_btn.clicked.connect(self._do_archive)
        self.archive_btn.setEnabled(False)
        btn_row.addWidget(self.archive_btn)

        layout.addLayout(btn_row)
        layout.addStretch()

    # ---- 对话框 ----

    def _open_add_dialog(self) -> None:
        fields = [
            {"key": "name", "label": "习惯名称", "type": "text", "required": True},
            {"key": "frequency", "label": "频率", "type": "combo",
             "options": ["daily", "weekly", "custom"]},
            {"key": "custom_days", "label": "自定义天数", "type": "spinbox",
             "from_": 1, "to": 30},
            {"key": "target_count", "label": "每日目标次数", "type": "spinbox",
             "from_": 1, "to": 100},
            {"key": "category", "label": "类别", "type": "combo",
             "options": HabitManager.VALID_CATEGORIES},
            {"key": "description", "label": "描述", "type": "text"},
            {"key": "color", "label": "热力图颜色", "type": "combo",
             "options": ["#4a90d9", "#27ae60", "#e67e22", "#8e44ad", "#e74c3c"]},
        ]
        data = FormDialog.get_form_data(self, "添加习惯", fields)
        if data:
            self._do_add(data)

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
            self.emit_status(f"习惯「{habit.name}」已创建")
        except Exception as e:
            QMessageBox.critical(self, "添加失败", str(e))

    def _open_edit_dialog(self) -> None:
        habit = self._get_selected_habit()
        if not habit:
            return
        fields = [
            {"key": "name", "label": "习惯名称", "type": "text", "required": True},
            {"key": "frequency", "label": "频率", "type": "combo",
             "options": ["daily", "weekly", "custom"]},
            {"key": "target_count", "label": "每日目标次数", "type": "spinbox",
             "from_": 1, "to": 100},
            {"key": "category", "label": "类别", "type": "combo",
             "options": HabitManager.VALID_CATEGORIES},
            {"key": "description", "label": "描述", "type": "text"},
        ]
        initial = {
            "name": habit.name, "frequency": habit.frequency,
            "target_count": habit.target_count,
            "category": habit.category, "description": habit.description,
        }
        data = FormDialog.get_form_data(self, "编辑习惯", fields, initial)
        if data:
            self._do_edit(habit.id, data)

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
            self.emit_status(f"习惯「{data['name']}」已更新")
        except Exception as e:
            QMessageBox.critical(self, "编辑失败", str(e))

    # ---- 打卡操作 ----

    def _on_table_double_click(self) -> None:
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
            self.emit_status(f"「{habit.name}」打卡成功")
        except Exception as e:
            QMessageBox.critical(self, "打卡失败", str(e))

    def _do_undo(self) -> None:
        habit = self._get_selected_habit()
        if not habit:
            return
        today = date.today().isoformat()
        self.manager.undo_check_in(habit.id, today)
        self.refresh()
        self._select_habit(habit.id)
        self.emit_status(f"「{habit.name}」打卡已撤销")

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
        self.emit_status(f"习惯「{habit.name}」已{action}")

    # ---- 详情面板更新 ----

    def _on_habit_select(self) -> None:
        habit = self._get_selected_habit()
        if not habit:
            self.detail_title.setText("选择一个习惯")
            for key in self.stats_labels:
                self.stats_labels[key].setText("-")
            self.checkin_btn.setEnabled(False)
            self.undo_btn.setEnabled(False)
            self.edit_btn.setEnabled(False)
            self.archive_btn.setEnabled(False)
            return

        self.detail_title.setText(habit.name)
        streak = self.manager.get_streak(habit.id)
        total = streak.get("total_checkins", 0)
        rate = streak.get("completion_rate", 0)

        self.stats_labels["current"].setText(f"{streak.get('current', 0)} 天")
        self.stats_labels["longest"].setText(f"{streak.get('longest', 0)} 天")
        self.stats_labels["total"].setText(f"{total} 次")
        self.stats_labels["rate"].setText(f"{rate:.0%}")

        heatmap_data = self.manager.get_heatmap_data(habit.id)
        self.heatmap.set_data(heatmap_data)
        if habit.color and habit.color != "#4a90d9":
            self.heatmap.set_color_scheme(habit.color)

        today = date.today().isoformat()
        checked = self.manager.is_checked_in(habit.id, today)

        self.checkin_btn.setEnabled(not checked)
        self.undo_btn.setEnabled(checked)
        self.edit_btn.setEnabled(True)
        self.archive_btn.setEnabled(True)
        self.archive_btn.setText("恢复" if habit.archived else "归档")

    # ---- 数据刷新 ----

    def refresh(self) -> None:
        include_archived = self.status_filter.currentText() == "已归档"
        category = self.category_filter.currentText()

        habits = self.manager.get_all(include_archived=include_archived)
        if category != "全部":
            habits = [h for h in habits if h.category == category]

        self._populate_table(habits)

        active = self.manager.get_active()
        today_stats = self.manager.get_today_stats()
        self._set_stats_text(
            f"活跃 {today_stats['total_active']} | "
            f"今日打卡 {today_stats['checked_today']}/{today_stats['total_active']}"
        )

        self._on_habit_select()

    def _populate_table(self, habits: list) -> None:
        self._clear_table()
        today = date.today().isoformat()
        for h in habits:
            checked = "☑" if self.manager.is_checked_in(h.id, today) else "☐"
            streak = self.manager.get_streak(h.id)
            self._add_row([
                checked, h.name, f"{streak.get('current', 0)}天"
            ], item_id=h.id)

    # ---- 搜索 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self.refresh()
            return
        results = self.manager.search(keyword)
        self._populate_table(
            [h for h in self.manager.get_all(include_archived=True)
             if h.id in {r.id for r in results}]
        )

    # ---- 辅助方法 ----

    def _get_selected_habit(self):
        habit_id = self._get_selected_id()
        if not habit_id:
            return None
        return self.manager.get_by_id(habit_id)

    def _select_habit(self, habit_id: str) -> None:
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == habit_id:
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                self._on_habit_select()
                return

    def highlight_item(self, item_id: str) -> None:
        self._select_habit(item_id)
