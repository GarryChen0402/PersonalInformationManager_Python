"""左侧导航栏组件 — PySide6 版本。"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QListWidget, QListWidgetItem, QPushButton
from PySide6.QtCore import Qt, Signal


class NavFrame(QWidget):
    """左侧导航栏，包含全局搜索（预留）和功能模块切换列表。"""

    navigated = Signal(str)

    NAV_ITEMS = [
        ("dashboard",  "▣  数据概览", "▣"),
        ("profile",    "◉  个人档案", "◉"),
        ("status",     "★  状态管理", "★"),
        ("skill",      "◆  技能管理", "◆"),
        ("knowledge",  "◣  知识管理", "◣"),
        ("todo",       "☑  待办事项", "☑"),
        ("habit",      "↯  习惯追踪", "↯"),
        ("journal",    "☷  日记",     "☷"),
        ("password",   "⚿  密码管理", "⚿"),
        ("backup",     "⚙  数据管理", "⚙"),
    ]

    def __init__(self, parent=None, on_navigate=None, on_search=None):
        super().__init__(parent)
        self.setMinimumWidth(150)
        self.setMaximumWidth(300)

        self._on_navigate = on_navigate
        self._collapsed = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # 折叠按钮
        self.collapse_btn = QPushButton("◀")
        self.collapse_btn.setFixedWidth(28)
        self.collapse_btn.setFixedHeight(24)
        self.collapse_btn.setToolTip("折叠/展开导航栏")
        self.collapse_btn.clicked.connect(self.toggle_collapse)
        layout.addWidget(self.collapse_btn, alignment=Qt.AlignRight)

        # 导航列表
        self.nav_list = QListWidget()
        self.nav_list.setSpacing(2)
        for key, full_text, _icon in self.NAV_ITEMS:
            item = QListWidgetItem(full_text)
            item.setData(Qt.UserRole, key)
            item.setData(Qt.UserRole + 1, full_text)
            item.setData(Qt.UserRole + 2, _icon)
            self.nav_list.addItem(item)
        self.nav_list.currentRowChanged.connect(self._on_item_clicked)
        layout.addWidget(self.nav_list)

        # 默认选中第一项
        self.nav_list.setCurrentRow(0)

    def _on_item_clicked(self, row: int) -> None:
        if row < 0:
            return
        key = self.nav_list.item(row).data(Qt.UserRole)
        self.navigated.emit(key)
        if self._on_navigate:
            self._on_navigate(key)

    def set_active(self, page_name: str) -> None:
        """设置当前选中项（不触发导航信号）。"""
        for i in range(self.nav_list.count()):
            if self.nav_list.item(i).data(Qt.UserRole) == page_name:
                self.nav_list.blockSignals(True)
                self.nav_list.setCurrentRow(i)
                self.nav_list.blockSignals(False)
                return

    def toggle_collapse(self) -> None:
        """折叠/展开导航栏。"""
        if self._collapsed:
            for i in range(self.nav_list.count()):
                item = self.nav_list.item(i)
                item.setText(item.data(Qt.UserRole + 1))  # 完整文本
            self.setMinimumWidth(150)
            self.collapse_btn.setText("◀")
        else:
            for i in range(self.nav_list.count()):
                item = self.nav_list.item(i)
                item.setText(item.data(Qt.UserRole + 2))  # 仅图标
            self.setMinimumWidth(50)
            self.collapse_btn.setText("▶")
        self._collapsed = not self._collapsed

    def focus_search(self) -> None:
        """聚焦搜索框（阶段六实现）。"""
        pass

    def set_theme(self, _theme: dict) -> None:
        """主题切换兼容接口（Qt Stylesheet 管理主题，此方法预留）。"""
        pass
