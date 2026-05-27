"""页面基类 — QWidget 版本，提供表格、排序、右键菜单等通用功能。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QMenu, QMessageBox, QLabel, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction


class BasePage(QWidget):
    """所有表格式页面的基类，减少重复代码。"""

    status_message = Signal(str)

    def __init__(self, parent=None, set_status=None):
        super().__init__(parent)
        self._set_status = set_status
        self._sort_state: dict[str, str] = {}

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # 表格
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._on_context_menu)
        self._layout.addWidget(self.table)

        # 统计栏容器
        self.stats_frame = QFrame()
        self.stats_frame.setFrameStyle(QFrame.StyledPanel)
        self.stats_layout = QHBoxLayout(self.stats_frame)
        self.stats_layout.setContentsMargins(8, 4, 8, 4)
        self._layout.addWidget(self.stats_frame)

    # ---- 选中 ID ----

    def _get_selected_id(self) -> str | None:
        """获取当前选中行的 ID（存储在首列 UserRole 中）。"""
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        if item:
            return item.data(Qt.UserRole)
        return None

    def _get_all_ids(self) -> list[str]:
        """获取所有行的 ID。"""
        ids = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item:
                ids.append(item.data(Qt.UserRole))
        return ids

    # ---- 清空 / 填充辅助 ----

    def _clear_table(self) -> None:
        """清空表格所有行。"""
        self.table.setRowCount(0)

    def _add_row(self, row_data: list[str], item_id: str = "") -> None:
        """添加一行数据，可选的 item_id 存储在首列 UserRole 中。"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col, text in enumerate(row_data):
            item = QTableWidgetItem(str(text))
            if col == 0 and item_id:
                item.setData(Qt.UserRole, item_id)
            self.table.setItem(row, col, item)

    # ---- 右键菜单 ----

    def _on_context_menu(self, pos) -> None:
        """右键菜单入口。"""
        menu = self._build_context_menu()
        if menu:
            menu.exec(self.table.viewport().mapToGlobal(pos))

    def _build_context_menu(self) -> QMenu | None:
        """子类重写以构建自定义右键菜单。返回 None 则无菜单。"""
        return None

    # ---- 高亮 ----

    def highlight_item(self, item_id: str) -> None:
        """定位并高亮指定条目。"""
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.data(Qt.UserRole) == item_id:
                self.table.selectRow(row)
                self.table.scrollToItem(item)
                return

    # ---- 状态栏 ----

    def emit_status(self, text: str) -> None:
        """发送状态栏消息。"""
        if self._set_status:
            self._set_status(text)
        self.status_message.emit(text)

    # ---- 统计栏 ----

    def _set_stats_text(self, text: str) -> None:
        """设置统计栏文本。"""
        # 清除旧标签
        for i in reversed(range(self.stats_layout.count())):
            w = self.stats_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        label = QLabel(text)
        label.setProperty("statsLabel", True)
        self.stats_layout.addWidget(label)

    # ---- 确认对话框 ----

    @staticmethod
    def _confirm(title: str, message: str) -> bool:
        return QMessageBox.question(
            None, title, message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        ) == QMessageBox.Yes

    @staticmethod
    def _info(title: str, message: str) -> None:
        QMessageBox.information(None, title, message)

    @staticmethod
    def _warning(title: str, message: str) -> None:
        QMessageBox.warning(None, title, message)
