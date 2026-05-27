"""待办事项管理页面 — PySide6 版本。"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel,
    QTableWidgetItem, QFileDialog, QMessageBox, QMenu, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from Services.TodoManager import TodoManager
from Models.TodoItem import TodoItem
from .BasePage import BasePage
from .Widgets import SearchBar, FormDialog, ConfirmDialog, CSVPreviewDialog

PRIORITY_LABELS = {"high": "高", "mid": "中", "low": "低"}


class TodoPage(BasePage):
    """待办事项管理页面，三段式布局。"""

    def __init__(self, parent=None, set_status=None):
        super().__init__(parent, set_status)
        self.manager = TodoManager()

        self._build_toolbar()
        self._build_table_columns()
        self._build_context_menu()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 4, 0, 4)

        self.search_bar = SearchBar(placeholder="搜索待办...")
        self.search_bar.search_requested.connect(self._on_search)
        toolbar_layout.addWidget(self.search_bar)

        toolbar_layout.addWidget(QLabel("状态："))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["未完成", "已完成", "全部"])
        self.status_filter.currentTextChanged.connect(self._on_filter)
        toolbar_layout.addWidget(self.status_filter)

        toolbar_layout.addWidget(QLabel("优先级："))
        self.priority_filter = QComboBox()
        self.priority_filter.addItems(["全部", "高", "中", "低"])
        self.priority_filter.currentTextChanged.connect(self._on_filter)
        toolbar_layout.addWidget(self.priority_filter)

        toolbar_layout.addWidget(QLabel("类别："))
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self._on_filter)
        toolbar_layout.addWidget(self.category_filter)

        toolbar_layout.addStretch()

        del_done_btn = QPushButton("删除已完成")
        del_done_btn.clicked.connect(self._batch_delete_completed)
        toolbar_layout.addWidget(del_done_btn)

        import_btn = QPushButton("导入CSV")
        import_btn.clicked.connect(self._import_csv)
        toolbar_layout.addWidget(import_btn)

        export_btn = QPushButton("导出CSV")
        export_btn.clicked.connect(self._export_csv)
        toolbar_layout.addWidget(export_btn)

        ical_btn = QPushButton("导出iCal")
        ical_btn.clicked.connect(self._export_icalendar)
        toolbar_layout.addWidget(ical_btn)

        add_btn = QPushButton("+ 添加待办")
        add_btn.clicked.connect(self._open_add_dialog)
        toolbar_layout.addWidget(add_btn)

        self._layout.insertWidget(0, toolbar)

    # ---- 表格 ----

    def _build_table_columns(self) -> None:
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "✓", "标题", "优先级", "类别", "截止日期", "创建时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._toggle_complete)

    # ---- 右键菜单 ----

    def _build_context_menu(self) -> QMenu | None:
        todo_id = self._get_selected_id()
        if not todo_id:
            return None
        menu = QMenu(self)
        menu.addAction("切换完成状态", self._toggle_complete)
        menu.addSeparator()
        menu.addAction("编辑", self._open_edit_dialog)
        menu.addSeparator()
        menu.addAction("删除", self._confirm_delete)
        return menu

    # ---- 添加 ----

    def _open_add_dialog(self) -> None:
        fields = [
            {"key": "title", "label": "标题", "type": "text", "required": True},
            {"key": "priority", "label": "优先级", "type": "combo",
             "options": ["mid", "high", "low"]},
            {"key": "category", "label": "类别", "type": "combo",
             "options": self.manager.VALID_CATEGORIES},
            {"key": "due_date", "label": "截止日期", "type": "text"},
            {"key": "description", "label": "描述", "type": "textarea"},
        ]
        data = FormDialog.get_form_data(self, "添加待办", fields,
                                         initial_data={"priority": "mid"})
        if data:
            self._do_add(data)

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
            self.emit_status(f"待办「{data['title']}」已添加")
        except Exception as e:
            QMessageBox.critical(self, "添加失败", str(e))

    # ---- 切换完成 ----

    def _toggle_complete(self) -> None:
        item = self._get_selected()
        if not item:
            return
        try:
            updated = self.manager.toggle_complete(item.id)
            action = "已完成" if updated.completed else "已取消完成"
            self.refresh()
            self.emit_status(f"待办「{updated.title}」{action}")
        except Exception as e:
            QMessageBox.critical(self, "操作失败", str(e))

    # ---- 编辑 ----

    def _open_edit_dialog(self) -> None:
        item = self._get_selected()
        if not item:
            return

        fields = [
            {"key": "title", "label": "标题", "type": "text", "required": True},
            {"key": "priority", "label": "优先级", "type": "combo",
             "options": self.manager.VALID_PRIORITIES},
            {"key": "category", "label": "类别", "type": "combo",
             "options": self.manager.VALID_CATEGORIES},
            {"key": "due_date", "label": "截止日期", "type": "text"},
            {"key": "description", "label": "描述", "type": "textarea"},
        ]
        initial = {
            "title": item.title,
            "priority": item.priority,
            "category": item.category,
            "due_date": item.due_date,
            "description": item.description,
        }
        data = FormDialog.get_form_data(self, "编辑待办", fields, initial)
        if data:
            self._do_edit(item.id, data)

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
            self.emit_status(f"待办「{data['title']}」已更新")
        except Exception as e:
            QMessageBox.critical(self, "编辑失败", str(e))

    # ---- 删除 ----

    def _confirm_delete(self) -> None:
        item = self._get_selected()
        if not item:
            return
        if ConfirmDialog.show(self, "确认删除",
                              f"确定要删除待办「{item.title}」吗？"):
            self.manager.delete_todo(item.id)
            self.refresh()
            self.emit_status(f"待办「{item.title}」已删除")

    def _batch_delete_completed(self) -> None:
        count = self.manager.batch_delete_completed()
        if count > 0:
            self.refresh()
            self.emit_status(f"已删除 {count} 条已完成的待办")
        else:
            QMessageBox.information(self, "提示", "没有已完成的待办")

    # ---- 搜索和筛选 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self.refresh()
            return
        results = self.manager.search(keyword)
        self._populate_table(results)

    def _on_filter(self) -> None:
        self._refresh_table()

    # ---- 数据加载 ----

    def refresh(self) -> None:
        self._refresh_table()
        self._update_filter_options()
        self._update_stats()

    def _refresh_table(self) -> None:
        status_val = self.status_filter.currentText()
        status = None
        if status_val == "未完成":
            status = "active"
        elif status_val == "已完成":
            status = "completed"

        items = self.manager.get_all(status=status)

        prio_val = self.priority_filter.currentText()
        if prio_val in ("高", "中", "低"):
            prio_map = {"高": "high", "中": "mid", "低": "low"}
            items = [i for i in items if i.priority == prio_map[prio_val]]

        cat_val = self.category_filter.currentText()
        if cat_val and cat_val != "全部":
            items = [i for i in items if i.category == cat_val]

        self._populate_table(items)

    def _populate_table(self, items: list[TodoItem]) -> None:
        self._clear_table()

        for item in items:
            self._add_row([
                "✓" if item.completed else "☐",
                item.title,
                PRIORITY_LABELS.get(item.priority, item.priority),
                item.category or "-",
                item.due_date or "-",
                item.created_at[:10] if item.created_at else "-",
            ], item_id=item.id)

            row = self.table.rowCount() - 1
            for col in range(self.table.columnCount()):
                cell = self.table.item(row, col)
                if not cell:
                    continue
                if item.completed:
                    cell.setForeground(QColor("#999999"))
                elif item.is_overdue():
                    cell.setForeground(QColor("#c0392b"))
                elif item.priority == "high":
                    cell.setBackground(QColor("#fef0e7"))

    def _update_filter_options(self) -> None:
        all_items = self.manager.get_all()
        categories = sorted({i.category for i in all_items if i.category})
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("全部")
        self.category_filter.addItems(categories)
        self.category_filter.setCurrentIndex(0)
        self.category_filter.blockSignals(False)

    def _update_stats(self) -> None:
        stats = self.manager.get_statistics()
        parts = [f"共 {stats['total']} 条"]
        if stats["active"] > 0:
            parts.append(f"待完成: {stats['active']}")
        if stats["completed"] > 0:
            parts.append(f"已完成: {stats['completed']}")
        if stats["overdue"] > 0:
            parts.append(f"逾期: {stats['overdue']}")
        self._set_stats_text("  |  ".join(parts))

    def _get_selected(self) -> TodoItem | None:
        todo_id = self._get_selected_id()
        if not todo_id:
            QMessageBox.information(self, "提示", "请先选中一条记录")
            return None
        return self.manager.get_by_id(todo_id)

    # ---- CSV 导入导出 ----

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "导出待办数据", "todos.csv", "CSV 文件 (*.csv)"
        )
        if path:
            try:
                self.manager.export_csv(path)
                self.emit_status(f"待办数据已导出到 {path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def _export_icalendar(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 iCalendar", "todos.ics", "iCalendar 文件 (*.ics)"
        )
        if path:
            try:
                self.manager.export_icalendar(path)
                self.emit_status(f"待办已导出为 iCalendar 至 {path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def _import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "导入待办数据", "", "CSV 文件 (*.csv)"
        )
        if path:
            dialog = CSVPreviewDialog(self, path, on_confirm=self._do_import_csv)
            dialog.exec()

    def _do_import_csv(self, path: str) -> None:
        try:
            result = self.manager.import_csv(path)
            self.refresh()
            msg = f"导入完成：成功 {result['success']} 条"
            if result.get("failed"):
                msg += f"，失败 {result['failed']} 条"
            self.emit_status(msg)
        except Exception as e:
            QMessageBox.critical(self, "导入失败", str(e))
