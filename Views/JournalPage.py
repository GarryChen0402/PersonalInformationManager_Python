"""日记页面 — PySide6 版本。"""

from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QPushButton,
    QLabel, QLineEdit, QTextEdit, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from Services.JournalManager import JournalManager
from Services.StatusManager import StatusManager
from Services.ConfigManager import ConfigManager
from .Widgets import CalendarNav, SearchBar


class JournalPage(QWidget):
    """日记页面：左侧日历导航 + 右侧编辑器。"""

    def __init__(self, parent=None, set_status=None):
        super().__init__(parent)
        self.manager = JournalManager()
        self.status_manager = StatusManager()
        self.config_manager = ConfigManager()
        self._current_date: str | None = None
        self._set_status = set_status

        self._build()

        today = datetime.now().strftime("%Y-%m-%d")
        self.calendar.select_date(today)

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 工具栏
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)

        self.search_bar = SearchBar(placeholder="搜索日记...")
        self.search_bar.search_requested.connect(self._on_search)
        toolbar_layout.addWidget(self.search_bar)

        today_btn = QPushButton("今天")
        today_btn.clicked.connect(self._go_today)
        toolbar_layout.addWidget(today_btn)

        stats_btn = QPushButton("统计")
        stats_btn.clicked.connect(self._show_statistics)
        toolbar_layout.addWidget(stats_btn)

        export_btn = QPushButton("导出 Markdown")
        export_btn.clicked.connect(self._export_markdown)
        toolbar_layout.addWidget(export_btn)

        toolbar_layout.addStretch()
        layout.addWidget(toolbar)

        # 主体：左右分栏
        splitter = QSplitter(Qt.Horizontal)

        # 左栏：日历
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(4, 4, 4, 4)

        self.calendar = CalendarNav()
        self.calendar.date_selected.connect(self._on_date_select)
        left_layout.addWidget(self.calendar)
        splitter.addWidget(left)

        # 右栏：编辑器
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 8, 8, 8)
        right_layout.setSpacing(4)

        # 标题
        title_row = QHBoxLayout()
        title_row.addWidget(QLabel("标题："))
        self.title_entry = QLineEdit()
        self.title_entry.textChanged.connect(self._on_content_change)
        title_row.addWidget(self.title_entry)
        right_layout.addLayout(title_row)

        # 情绪关联
        self.mood_label = QLabel()
        self.mood_label.setStyleSheet("color: #888; font-size: 11px; padding: 2px 0;")
        right_layout.addWidget(self.mood_label)

        # 正文
        self.text_edit = QTextEdit()
        self.text_edit.textChanged.connect(self._on_content_change)
        right_layout.addWidget(self.text_edit)

        # 底部操作栏
        bottom = QHBoxLayout()

        self.word_count_label = QLabel("字数：0")
        self.word_count_label.setStyleSheet("color: #888; font-size: 11px;")
        bottom.addWidget(self.word_count_label)

        bottom.addStretch()

        del_btn = QPushButton("删除")
        del_btn.setStyleSheet("QPushButton { color: #cc0000; }")
        del_btn.clicked.connect(self._delete_current)
        bottom.addWidget(del_btn)

        save_btn = QPushButton("保存 (Ctrl+S)")
        save_btn.clicked.connect(self._save_current)
        bottom.addWidget(save_btn)

        right_layout.addLayout(bottom)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        layout.addWidget(splitter)

        # 统计栏
        self.stats_label = QLabel()
        self.stats_label.setProperty("statsLabel", True)
        layout.addWidget(self.stats_label)

    # ---- 事件 ----

    def _on_date_select(self, date_str: str) -> None:
        self._auto_save()
        self._current_date = date_str
        self._load_entry(date_str)
        self._update_mood_display(date_str)

    def _load_entry(self, date_str: str) -> None:
        entry = self.manager.get_entry(date_str)
        self.title_entry.blockSignals(True)
        self.text_edit.blockSignals(True)
        if entry:
            self.title_entry.setText(entry.title)
            self.text_edit.setPlainText(entry.content)
            self.word_count_label.setText(f"字数：{entry.word_count}")
        else:
            self.title_entry.clear()
            self.text_edit.clear()
            self.word_count_label.setText("字数：0")
        self.title_entry.blockSignals(False)
        self.text_edit.blockSignals(False)

    def _on_content_change(self) -> None:
        content = self.text_edit.toPlainText().strip()
        word_count = len(content.replace("\n", " ").split()) if content else 0
        self.word_count_label.setText(f"字数：{word_count}")

    def _update_mood_display(self, date_str: str) -> None:
        record = self.status_manager.get_by_date(date_str)
        if record:
            self.mood_label.setText(
                f"心情：{self._mood_emoji(record.mood)} {record.mood}/5  "
                f"精力：{record.energy}/5  "
                f"专注：{record.focus}/5  "
                f"睡眠：{record.sleep_hours}h"
            )
        else:
            self.mood_label.setText("")

    @staticmethod
    def _mood_emoji(score: int) -> str:
        if score >= 5:
            return "😄"
        elif score >= 4:
            return "🙂"
        elif score >= 3:
            return "😐"
        elif score >= 2:
            return "😕"
        else:
            return "😞"

    # ---- 保存 ----

    def _save_current(self) -> None:
        if not self._current_date:
            return
        title = self.title_entry.text().strip()
        content = self.text_edit.toPlainText().strip()
        self.manager.save_entry(self._current_date, title, content)
        self._emit_status(f"日记已保存 ({self._current_date})")
        self._on_content_change()
        self._update_calendar_marks()

    def _auto_save(self) -> None:
        if not self._current_date:
            return
        title = self.title_entry.text().strip()
        content = self.text_edit.toPlainText().strip()
        existing = self.manager.get_entry(self._current_date)
        if existing:
            if existing.title != title or existing.content.strip() != content:
                self._save_current()
        elif title or content:
            self._save_current()

    # ---- 删除 ----

    def _delete_current(self) -> None:
        if not self._current_date:
            return
        result = QMessageBox.question(
            self, "确认删除",
            f"确定要删除 {self._current_date} 的日记吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if result != QMessageBox.Yes:
            return
        self.manager.delete_entry(self._current_date)
        self.title_entry.clear()
        self.text_edit.clear()
        self.word_count_label.setText("字数：0")
        self.mood_label.setText("")
        self._emit_status(f"已删除 {self._current_date} 的日记")
        self._update_calendar_marks()

    # ---- 搜索 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self._emit_status("请输入搜索关键词")
            return
        results = self.manager.search(keyword)
        if results:
            entry = results[0]
            self._emit_status(f"找到 {len(results)} 条结果，跳转到第一条：{entry.date}")
            self._auto_save()
            self.calendar.select_date(entry.date)
            self.calendar.goto_date(int(entry.date[:4]), int(entry.date[5:7]))
        else:
            self._emit_status("未找到匹配的日记")

    # ---- 统计 ----

    def _show_statistics(self) -> None:
        stats = self.manager.get_statistics()
        msg = (
            f"日记总数：{stats['total_entries']} 篇\n"
            f"总字数：{stats['total_words']}\n"
            f"平均字数：{stats['avg_words']}\n"
            f"连续天数：{stats['current_streak']} 天"
        )
        QMessageBox.information(self, "日记统计", msg)

    # ---- 导出 ----

    def _export_markdown(self) -> None:
        if not self._current_date:
            QMessageBox.information(self, "提示", "请先选择一个日期")
            return
        entry = self.manager.get_entry(self._current_date)
        if not entry:
            QMessageBox.information(self, "提示", f"{self._current_date} 没有日记内容")
            return

        default_name = f"journal_{self._current_date}.md"
        path, _ = QFileDialog.getSaveFileName(
            self, "导出 Markdown", default_name, "Markdown 文件 (*.md)"
        )
        if path:
            try:
                self.manager.export_single(self._current_date, path)
                self._emit_status(f"日记已导出至：{path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    # ---- 辅助 ----

    def _go_today(self) -> None:
        today = datetime.now().strftime("%Y-%m-%d")
        self._auto_save()
        self.calendar.select_date(today)
        now = datetime.now()
        self.calendar.goto_date(now.year, now.month)

    def _update_calendar_marks(self) -> None:
        dates = self.manager.get_dates_with_entries()
        self.calendar.set_marked_dates(dates)

    def refresh(self) -> None:
        self._update_calendar_marks()
        if self._current_date:
            self._load_entry(self._current_date)
            self._update_mood_display(self._current_date)
        self._update_stats()

    def _update_stats(self) -> None:
        stats = self.manager.get_statistics()
        self.stats_label.setText(
            f"共 {stats['total_entries']} 篇日记  "
            f"总字数 {stats['total_words']}  "
            f"连续 {stats['current_streak']} 天"
        )

    def highlight_item(self, item_id: str) -> None:
        entry = self.manager.get_by_id(item_id)
        if entry:
            self._auto_save()
            self.calendar.select_date(entry.date)
            dt = datetime.strptime(entry.date, "%Y-%m-%d")
            self.calendar.goto_date(dt.year, dt.month)

    def _emit_status(self, text: str) -> None:
        if self._set_status:
            self._set_status(text)
