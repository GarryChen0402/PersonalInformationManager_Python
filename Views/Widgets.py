"""可复用的 PySide6 通用组件。"""

import csv
from datetime import datetime, date, timedelta
from PySide6.QtWidgets import (
    QWidget, QLineEdit, QDialog, QFormLayout, QDialogButtonBox,
    QMessageBox, QVBoxLayout, QHBoxLayout, QComboBox, QDateEdit,
    QPushButton, QLabel, QGridLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QFrame, QSpinBox, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QDate, QTimer
from PySide6.QtGui import QFont


# ---- SearchBar ----

class SearchBar(QWidget):
    """搜索框组件：输入框 + 300ms 防抖。"""
    search_requested = Signal(str)

    def __init__(self, parent=None, placeholder="输入关键词搜索..."):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setClearButtonEnabled(True)

        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_search)

        self.input.textChanged.connect(self._on_text_changed)
        self.input.returnPressed.connect(self._emit_search)
        layout.addWidget(self.input)

    def _on_text_changed(self, _text: str) -> None:
        self._debounce_timer.start(300)

    def _emit_search(self) -> None:
        self._debounce_timer.stop()
        self.search_requested.emit(self.input.text().strip())

    def get_text(self) -> str:
        return self.input.text().strip()

    def set_text(self, text: str) -> None:
        self.input.setText(text)

    def clear(self) -> None:
        self.input.clear()

    def setFocus(self) -> None:
        self.input.setFocus()


# ---- FormDialog ----

class FormDialog(QDialog):
    """通用表单对话框。
    fields: [{"key": "title", "label": "标题", "type": "text", "required": True}, ...]
    支持 type: text, combo (需 options), textarea, spinbox (需 from_/to_), date
    """

    def __init__(self, parent=None, title="", fields=None, initial_data=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.fields = fields or []
        self.initial_data = initial_data or {}
        self.widgets: dict = {}
        self.result_data: dict | None = None

        self._build()

    def _build(self) -> None:
        layout = QFormLayout(self)
        layout.setSpacing(8)

        for field in self.fields:
            key = field.get("key", field.get("name", ""))
            label_text = field.get("label", key)
            kind = field.get("type", "text")

            if kind == "combo":
                widget = QComboBox()
                widget.addItems(field.get("options", []))
                default = self.initial_data.get(key, "")
                if default:
                    widget.setCurrentText(str(default))
            elif kind == "textarea":
                widget = QTextEdit()
                widget.setMaximumHeight(80)
                default = self.initial_data.get(key, "")
                if default:
                    widget.setPlainText(str(default))
            elif kind == "spinbox":
                widget = QSpinBox()
                widget.setRange(field.get("from_", 0), field.get("to", 100))
                default = self.initial_data.get(key, 0)
                if default:
                    widget.setValue(int(default))
            elif kind == "date":
                widget = QDateEdit()
                widget.setCalendarPopup(True)
                widget.setDate(QDate.currentDate())
                default = self.initial_data.get(key, "")
                if default:
                    widget.setDate(QDate.fromString(default, "yyyy-MM-dd"))
            else:
                widget = QLineEdit()
                show = field.get("show", "")
                if show:
                    widget.setEchoMode(QLineEdit.Password)
                default = self.initial_data.get(key, "")
                if default:
                    widget.setText(str(default))

            self.widgets[key] = widget
            layout.addRow(label_text + "：", widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._collect_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        # 回车键提交
        for w in self.widgets.values():
            if isinstance(w, QLineEdit):
                w.returnPressed.connect(self._collect_and_accept)

    def _collect_and_accept(self) -> None:
        data = {}
        for field in self.fields:
            key = field.get("key", field.get("name", ""))
            kind = field.get("type", "text")
            widget = self.widgets[key]

            if kind == "combo":
                value = widget.currentText()
            elif kind == "textarea":
                value = widget.toPlainText().strip()
            elif kind == "spinbox":
                value = widget.value()
            elif kind == "date":
                value = widget.date().toString("yyyy-MM-dd")
            else:
                value = widget.text().strip()

            if field.get("required") and not value:
                QMessageBox.warning(self, "输入校验", f"请填写「{field.get('label', key)}」")
                return

            data[key] = value

        self.result_data = data
        self.accept()

    def get_data(self) -> dict | None:
        return self.result_data

    @staticmethod
    def get_form_data(parent=None, title="", fields=None, initial_data=None) -> dict | None:
        """静态方法：显示对话框并返回数据。"""
        dialog = FormDialog(parent, title, fields, initial_data)
        if dialog.exec() == QDialog.Accepted:
            return dialog.get_data()
        return None


# ---- ConfirmDialog ----

class ConfirmDialog:
    """确认弹窗封装。"""

    @staticmethod
    def show(parent=None, title="", message="") -> bool:
        return QMessageBox.question(
            parent, title, message,
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        ) == QMessageBox.Yes


# ---- DateRangePicker ----

class DateRangePicker(QWidget):
    """日期范围选择组件。"""
    query_requested = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        layout.addWidget(QLabel("从："))
        self.start_edit = QDateEdit()
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDate(QDate.currentDate().addDays(-7))
        layout.addWidget(self.start_edit)

        layout.addWidget(QLabel("到："))
        self.end_edit = QDateEdit()
        self.end_edit.setCalendarPopup(True)
        self.end_edit.setDate(QDate.currentDate())
        layout.addWidget(self.end_edit)

        query_btn = QPushButton("查询")
        query_btn.clicked.connect(self._do_query)
        layout.addWidget(query_btn)

        week_btn = QPushButton("最近7天")
        week_btn.clicked.connect(self._set_last_week)
        layout.addWidget(week_btn)

        month_btn = QPushButton("最近30天")
        month_btn.clicked.connect(self._set_last_month)
        layout.addWidget(month_btn)

    def _do_query(self) -> None:
        start = self.start_edit.date().toString("yyyy-MM-dd")
        end = self.end_edit.date().toString("yyyy-MM-dd")
        self.query_requested.emit(start, end)

    def _set_last_week(self) -> None:
        self.end_edit.setDate(QDate.currentDate())
        self.start_edit.setDate(QDate.currentDate().addDays(-7))
        self._do_query()

    def _set_last_month(self) -> None:
        self.end_edit.setDate(QDate.currentDate())
        self.start_edit.setDate(QDate.currentDate().addDays(-30))
        self._do_query()

    def set_range(self, start: str, end: str) -> None:
        self.start_edit.setDate(QDate.fromString(start, "yyyy-MM-dd"))
        self.end_edit.setDate(QDate.fromString(end, "yyyy-MM-dd"))

    def get_start(self) -> str:
        return self.start_edit.date().toString("yyyy-MM-dd")

    def get_end(self) -> str:
        return self.end_edit.date().toString("yyyy-MM-dd")


# ---- StatsBar ----

class StatsBar(QWidget):
    """统计栏组件。"""

    def __init__(self, parent=None, items=None):
        super().__init__(parent)
        self.setProperty("statsLabel", True)
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(8, 4, 8, 4)
        self._labels: list[QLabel] = []

        if items:
            self.update(items)

    def update(self, items: list[tuple[str, str]]) -> None:
        for lbl in self._labels:
            lbl.deleteLater()
        self._labels.clear()
        for name, value in items:
            lbl = QLabel(f"{name}: {value}")
            lbl.setProperty("statsLabel", True)
            self._layout.addWidget(lbl)
            self._labels.append(lbl)


# ---- KeywordEntry ----

class KeywordEntry(QWidget):
    """关键词标签式输入组件（芯片风格）。"""
    keywords_changed = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._keywords: list[str] = []

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(4)

        input_row = QHBoxLayout()
        self.entry = QLineEdit()
        self.entry.setPlaceholderText("输入关键词，回车添加")
        self.entry.returnPressed.connect(self._add_keyword)
        input_row.addWidget(self.entry)

        add_btn = QPushButton("+")
        add_btn.setFixedWidth(30)
        add_btn.clicked.connect(self._add_keyword)
        input_row.addWidget(add_btn)
        main_layout.addLayout(input_row)

        self.chip_layout = QHBoxLayout()
        self.chip_layout.setSpacing(4)
        self.chip_layout.addStretch()
        main_layout.addLayout(self.chip_layout)

    def _add_keyword(self) -> None:
        kw = self.entry.text().strip()
        if kw and kw not in self._keywords:
            self._keywords.append(kw)
            self._add_chip(kw)
            self.keywords_changed.emit(self._keywords)
        self.entry.clear()

    def _add_chip(self, kw: str) -> None:
        chip = QFrame()
        chip.setStyleSheet(
            "QFrame { background-color: #e0e8f0; border-radius: 8px; padding: 2px 6px; }"
        )
        chip_layout = QHBoxLayout(chip)
        chip_layout.setContentsMargins(6, 2, 4, 2)
        chip_layout.setSpacing(2)

        label = QLabel(kw)
        label.setStyleSheet("QLabel { font-size: 11px; }")
        chip_layout.addWidget(label)

        close_btn = QPushButton("×")
        close_btn.setFlat(True)
        close_btn.setFixedSize(16, 16)
        close_btn.setStyleSheet(
            "QPushButton { font-size: 12px; color: #999; border: none; }"
            "QPushButton:hover { color: #333; }"
        )
        close_btn.clicked.connect(lambda: self._remove_keyword(kw, chip))
        chip_layout.addWidget(close_btn)

        # 插入到 stretch 之前
        self.chip_layout.insertWidget(self.chip_layout.count() - 1, chip)

    def _remove_keyword(self, kw: str, chip: QFrame) -> None:
        if kw in self._keywords:
            self._keywords.remove(kw)
        chip.deleteLater()
        self.keywords_changed.emit(self._keywords)

    def get_keywords(self) -> list[str]:
        return list(self._keywords)

    def set_keywords(self, keywords: list[str]) -> None:
        self._keywords = []
        # 清除旧芯片
        for i in reversed(range(self.chip_layout.count())):
            item = self.chip_layout.itemAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self.chip_layout.addStretch()
        for kw in keywords:
            self._keywords.append(kw)
            self._add_chip(kw)


# ---- CalendarNav ----

class CalendarNav(QWidget):
    """月历导航组件。"""
    date_selected = Signal(str)

    WEEKDAY_HEADERS = ["一", "二", "三", "四", "五", "六", "日"]

    def __init__(self, parent=None, marked_dates=None):
        super().__init__(parent)
        self.marked_dates = marked_dates or set()
        self.selected_date: str | None = None
        self._current_year = 0
        self._current_month = 0
        self._day_buttons: list[QPushButton] = []

        self._build()

        now = datetime.now()
        self.goto_date(now.year, now.month)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 月份切换
        header = QHBoxLayout()
        self._prev_btn = QPushButton("◀")
        self._prev_btn.setFlat(True)
        self._prev_btn.setFixedWidth(28)
        self._prev_btn.clicked.connect(self._prev_month)
        header.addWidget(self._prev_btn)

        self._month_label = QLabel()
        self._month_label.setAlignment(Qt.AlignCenter)
        self._month_label.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
        header.addWidget(self._month_label)

        self._next_btn = QPushButton("▶")
        self._next_btn.setFlat(True)
        self._next_btn.setFixedWidth(28)
        self._next_btn.clicked.connect(self._next_month)
        header.addWidget(self._next_btn)
        layout.addLayout(header)

        # 星期标题
        week_header = QHBoxLayout()
        week_header.setSpacing(0)
        for d in self.WEEKDAY_HEADERS:
            lbl = QLabel(d)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setFixedWidth(52)
            lbl.setStyleSheet("color: #888; font-size: 10px;")
            week_header.addWidget(lbl)
        layout.addLayout(week_header)

        # 日期网格
        self._grid = QGridLayout()
        self._grid.setSpacing(2)
        layout.addLayout(self._grid)

    def _render_grid(self) -> None:
        for btn in self._day_buttons:
            btn.deleteLater()
        self._day_buttons.clear()

        first_day = date(self._current_year, self._current_month, 1)
        start_weekday = first_day.weekday()  # Mon=0, Sun=6

        if self._current_month == 12:
            next_month = date(self._current_year + 1, 1, 1)
        else:
            next_month = date(self._current_year, self._current_month + 1, 1)
        days_in_month = (next_month - first_day).days

        today = date.today()

        for row in range(6):
            for col in range(7):
                i = row * 7 + col
                day_num = i - start_weekday + 1

                if 1 <= day_num <= days_in_month:
                    cell_date = date(self._current_year, self._current_month, day_num)
                    date_str = cell_date.isoformat()
                    text = str(day_num)

                    is_today = cell_date == today
                    is_marked = date_str in self.marked_dates
                    is_selected = date_str == self.selected_date

                    btn = QPushButton(text)
                    btn.setFixedSize(52, 40)
                    btn.setFlat(True)
                    btn.clicked.connect(lambda checked, d=date_str: self.select_date(d))

                    if is_selected:
                        btn.setStyleSheet(
                            "QPushButton { background-color: #4a90d9; color: white; "
                            "border-radius: 4px; font-weight: bold; }"
                        )
                    elif is_today:
                        btn.setStyleSheet(
                            "QPushButton { background-color: #e8f4fd; color: #4a90d9; "
                            "border-radius: 4px; font-weight: bold; }"
                        )
                    elif is_marked:
                        btn.setStyleSheet(
                            "QPushButton { background-color: #e0f0e0; color: #333; "
                            "border-radius: 4px; font-weight: bold; }"
                            "QPushButton:hover { background-color: #c8e6c8; }"
                        )
                    else:
                        btn.setStyleSheet(
                            "QPushButton { color: #333; border-radius: 4px; }"
                            "QPushButton:hover { background-color: #e8e8e8; }"
                        )

                    self._grid.addWidget(btn, row, col)
                    self._day_buttons.append(btn)
                else:
                    spacer = QLabel()
                    spacer.setFixedSize(52, 40)
                    self._grid.addWidget(spacer, row, col)

    def select_date(self, date_str: str) -> None:
        self.selected_date = date_str
        self._render_grid()
        self.date_selected.emit(date_str)

    def set_marked_dates(self, dates: set[str]) -> None:
        self.marked_dates = dates
        self._render_grid()

    def goto_date(self, year: int, month: int) -> None:
        self._current_year = year
        self._current_month = month
        self._month_label.setText(f"{year}年 {month}月")
        self._render_grid()

    def _prev_month(self) -> None:
        if self._current_month == 1:
            self.goto_date(self._current_year - 1, 12)
        else:
            self.goto_date(self._current_year, self._current_month - 1)

    def _next_month(self) -> None:
        if self._current_month == 12:
            self.goto_date(self._current_year + 1, 1)
        else:
            self.goto_date(self._current_year, self._current_month + 1)

    def get_current_date(self) -> str | None:
        return self.selected_date


# ---- CSVPreviewDialog ----

class CSVPreviewDialog(QDialog):
    """CSV 导入预览对话框。"""

    def __init__(self, parent=None, file_path="", on_confirm=None):
        super().__init__(parent)
        self.setWindowTitle("CSV 导入预览")
        self.resize(500, 350)
        self.setModal(True)
        self.file_path = file_path
        self.on_confirm = on_confirm

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel(f"文件：{self.file_path}"))

        # 预览表格
        columns = []
        preview_rows = []
        try:
            with open(self.file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                header = next(reader)
                columns = [h.strip() for h in header]
                for _ in range(5):
                    try:
                        preview_rows.append(next(reader))
                    except StopIteration:
                        break
        except (StopIteration, OSError):
            columns = ["(无法读取)"]

        table = QTableWidget()
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
        table.setRowCount(len(preview_rows))
        table.horizontalHeader().setStretchLastSection(True)
        for r, row in enumerate(preview_rows):
            for c, val in enumerate(row):
                if c < len(columns):
                    table.setItem(r, c, QTableWidgetItem(val))
        layout.addWidget(table)

        total = sum(1 for _ in open(self.file_path, "r", encoding="utf-8-sig")) - 1
        layout.addWidget(QLabel(f"共 {total} 行数据（预览前 {min(5, total)} 行）"))

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("确认导入")
        buttons.accepted.connect(self._do_confirm)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _do_confirm(self) -> None:
        if self.on_confirm:
            self.on_confirm(self.file_path)
        self.accept()
