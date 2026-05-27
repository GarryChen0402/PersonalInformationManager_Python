"""状态管理页面 — PySide6 版本。"""

from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidgetItem, QFileDialog, QMessageBox, QMenu, QHeaderView
)
from PySide6.QtCore import Qt

from Services.StatusManager import StatusManager
from Models.Status import StatusRecord
from .BasePage import BasePage
from .Widgets import FormDialog, ConfirmDialog, DateRangePicker
from .ChartWidgets import LineChart, CalendarHeatmap


class StatusPage(BasePage):
    """状态管理页面，三段式布局 + 趋势图 + 热力图。"""

    def __init__(self, parent=None, set_status=None):
        super().__init__(parent, set_status)
        self.manager = StatusManager()
        self._period_days = 7
        self._heatmap_metric = "mood"

        self._build_toolbar()
        self._build_charts()
        self._build_table_columns()
        self._build_context_menu()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 4, 0, 4)

        self.date_picker = DateRangePicker()
        self.date_picker.query_requested.connect(self._on_date_range)
        toolbar_layout.addWidget(self.date_picker)

        toolbar_layout.addStretch()

        add_btn = QPushButton("+ 添加记录")
        add_btn.clicked.connect(self._open_add_dialog)
        toolbar_layout.addWidget(add_btn)

        export_btn = QPushButton("导出CSV")
        export_btn.clicked.connect(self._export_csv)
        toolbar_layout.addWidget(export_btn)

        self._layout.insertWidget(0, toolbar)

    # ---- 表格 ----

    def _build_table_columns(self) -> None:
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "日期", "心情", "精力", "专注度", "体重(kg)", "睡眠(h)", "备注"
        ])
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._open_edit_dialog)

    # ---- 图表 ----

    def _build_charts(self) -> None:
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        charts_layout.setContentsMargins(0, 0, 0, 0)
        charts_layout.setSpacing(4)

        # 周期切换按钮
        period_frame = QWidget()
        period_layout = QHBoxLayout(period_frame)
        period_layout.setContentsMargins(8, 0, 0, 0)
        period_layout.setSpacing(2)

        self._period_btns: dict[str, QPushButton] = {}
        for text, val in [("7天", "7"), ("30天", "30"), ("90天", "90")]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(val == "7")
            btn.clicked.connect(lambda checked, v=val: self._on_period_change(v))
            period_layout.addWidget(btn)
            self._period_btns[val] = btn
        period_layout.addStretch()
        charts_layout.addWidget(period_frame)

        # 趋势图
        self.line_chart = LineChart(title="")
        self.line_chart.setMinimumHeight(200)
        charts_layout.addWidget(self.line_chart)

        # 热力图指标切换
        heatmap_toggle = QWidget()
        heatmap_toggle_layout = QHBoxLayout(heatmap_toggle)
        heatmap_toggle_layout.setContentsMargins(8, 0, 0, 0)
        heatmap_toggle_layout.setSpacing(2)

        self._heatmap_btns: dict[str, QPushButton] = {}
        for text, val in [("心情", "mood"), ("精力", "energy"),
                           ("专注", "focus"), ("睡眠", "sleep")]:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(val == "mood")
            btn.clicked.connect(lambda checked, v=val: self._on_heatmap_metric_change(v))
            heatmap_toggle_layout.addWidget(btn)
            self._heatmap_btns[val] = btn
        heatmap_toggle_layout.addStretch()
        charts_layout.addWidget(heatmap_toggle)

        # 热力图
        self.heatmap = CalendarHeatmap()
        self.heatmap.setMinimumHeight(140)
        charts_layout.addWidget(self.heatmap)

        self._layout.insertWidget(1, charts_widget)

    def _on_heatmap_metric_change(self, metric: str) -> None:
        for v, btn in self._heatmap_btns.items():
            btn.setChecked(v == metric)
        self._heatmap_metric = metric
        self._load_heatmap_data()

    def _on_period_change(self, days: str) -> None:
        for v, btn in self._period_btns.items():
            btn.setChecked(v == days)
        self._period_days = int(days)
        self._load_chart_data()

    def _load_heatmap_data(self) -> None:
        year = datetime.now().year
        start = f"{year}-01-01"
        end = f"{year}-12-31"
        records = self.manager.get_by_date_range(start, end)
        metric = self._heatmap_metric

        data: dict[str, float] = {}
        for r in records:
            if metric == "mood":
                data[r.date] = r.mood
            elif metric == "energy":
                data[r.date] = r.energy
            elif metric == "focus":
                data[r.date] = r.focus
            elif metric == "sleep":
                data[r.date] = r.sleep_hours

        self.heatmap.set_data(data)

    def _load_chart_data(self) -> None:
        end = datetime.now()
        start = end - timedelta(days=self._period_days)
        records = self.manager.get_by_date_range(
            start.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")
        )
        records.sort(key=lambda r: r.date)

        if not records:
            self.line_chart.set_data([], {})
            return

        labels = [r.date[-5:] for r in records]
        series = {
            "心情": [r.mood for r in records],
            "精力": [r.energy for r in records],
            "专注度": [r.focus for r in records],
        }
        if any(r.sleep_hours > 0 for r in records):
            series["睡眠"] = [r.sleep_hours for r in records]

        self.line_chart.set_data(labels, series)

    # ---- 右键菜单 ----

    def _build_context_menu(self) -> QMenu | None:
        record_id = self._get_selected_id()
        if not record_id:
            return None
        menu = QMenu(self)
        menu.addAction("编辑", self._open_edit_dialog)
        menu.addSeparator()
        menu.addAction("删除", self._confirm_delete)
        return menu

    # ---- 添加 ----

    def _open_add_dialog(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        fields = [
            {"key": "date", "label": "日期", "type": "text", "required": True},
            {"key": "mood", "label": "心情(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"key": "energy", "label": "精力(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"key": "focus", "label": "专注度(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"key": "weight", "label": "体重(kg)", "type": "text"},
            {"key": "sleep_hours", "label": "睡眠(h)", "type": "text"},
            {"key": "note", "label": "备注", "type": "textarea"},
        ]
        initial = {"date": today, "mood": 3, "energy": 3, "focus": 3}
        data = FormDialog.get_form_data(self, "添加状态记录", fields, initial)
        if data:
            self._do_add(data)

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
            self.emit_status(f"状态记录「{data['date']}」已保存")
        except Exception as e:
            QMessageBox.critical(self, "添加失败", str(e))

    # ---- 编辑 ----

    def _open_edit_dialog(self) -> None:
        record = self._get_selected()
        if not record:
            return

        fields = [
            {"key": "date", "label": "日期", "type": "text", "required": True},
            {"key": "mood", "label": "心情(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"key": "energy", "label": "精力(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"key": "focus", "label": "专注度(1-5)", "type": "spinbox", "from_": 1, "to": 5},
            {"key": "weight", "label": "体重(kg)", "type": "text"},
            {"key": "sleep_hours", "label": "睡眠(h)", "type": "text"},
            {"key": "note", "label": "备注", "type": "textarea"},
        ]
        initial = {
            "date": record.date,
            "mood": record.mood, "energy": record.energy, "focus": record.focus,
            "weight": str(record.weight) if record.weight else "",
            "sleep_hours": str(record.sleep_hours) if record.sleep_hours else "",
            "note": record.note,
        }
        data = FormDialog.get_form_data(self, "编辑状态记录", fields, initial)
        if data:
            self._do_edit(record.id, data)

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
            self.emit_status(f"状态记录「{data['date']}」已更新")
        except Exception as e:
            QMessageBox.critical(self, "编辑失败", str(e))

    # ---- 删除 ----

    def _confirm_delete(self) -> None:
        record = self._get_selected()
        if not record:
            return
        if ConfirmDialog.show(self, "确认删除",
                              f"确定要删除「{record.date}」的状态记录吗？"):
            self.manager.delete_record(record.id)
            self.refresh()
            self.emit_status(f"状态记录「{record.date}」已删除")

    # ---- 日期筛选 ----

    def _on_date_range(self, start: str, end: str) -> None:
        records = self.manager.get_by_date_range(start, end)
        self._populate_table(records)

    # ---- 数据加载 ----

    def refresh(self) -> None:
        records = self.manager.get_latest(30)
        self._populate_table(records)

        self._load_chart_data()
        self._load_heatmap_data()

        # 设置默认日期范围
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        self.date_picker.set_range(start, end)

        stats = self.manager.get_statistics(period="week")
        if stats["count"] > 0:
            self._set_stats_text(
                f"本周({stats['count']}条)  |  "
                f"平均心情: {stats['mood']}/5  |  "
                f"平均精力: {stats['energy']}/5  |  "
                f"平均专注度: {stats['focus']}/5  |  "
                f"平均睡眠: {stats['sleep_hours']}h"
            )
        else:
            self._set_stats_text("本周暂无记录")

    def _populate_table(self, records: list[StatusRecord]) -> None:
        self._clear_table()
        for r in records:
            avg = (r.mood + r.energy + r.focus) / 3
            if avg < 3:
                color = QTableWidgetItem().background().color()  # 用背景色
                row_color = "#fde8e8"
            elif avg < 4:
                row_color = "#fef9e7"
            else:
                row_color = "#e8f8f0"

            self._add_row([
                r.date,
                f"{r.mood}/5",
                f"{r.energy}/5",
                f"{r.focus}/5",
                f"{r.weight:.1f}" if r.weight else "-",
                f"{r.sleep_hours:.1f}" if r.sleep_hours else "-",
                r.note,
            ], item_id=r.id)

            # 应用行背景色
            row = self.table.rowCount() - 1
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(Qt.GlobalColor.transparent)
            # 使用交替方式实现行颜色
            from PySide6.QtGui import QColor
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    item.setBackground(QColor(row_color))

    def _get_selected(self) -> StatusRecord | None:
        record_id = self._get_selected_id()
        if not record_id:
            QMessageBox.information(self, "提示", "请先选中一条记录")
            return None
        return self.manager.get_by_id(record_id)

    # ---- CSV 导出 ----

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "导出状态记录", "status.csv", "CSV 文件 (*.csv)"
        )
        if path:
            try:
                self.manager.export_csv(path)
                self.emit_status(f"状态记录已导出到 {path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))
