"""全局搜索栏组件 — PySide6 版本，跨模块搜索 + 下拉结果面板。"""

from dataclasses import dataclass
from typing import Callable

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTreeWidget, QTreeWidgetItem, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont


@dataclass
class SearchResult:
    """跨模块搜索结果。"""
    name: str
    module: str
    item_id: str
    snippet: str = ""


MODULE_LABELS: dict[str, str] = {
    "skill": "技能", "note": "笔记", "ebook": "电子书",
    "todo": "待办", "habit": "习惯", "journal": "日记",
    "password": "密码", "status": "状态",
}


class GlobalSearchBar(QWidget):
    """全局搜索栏，含防抖输入框和下拉结果面板。"""

    def __init__(
        self, parent=None,
        on_search: Callable[[str], list[SearchResult]] = None,
        on_navigate: Callable[[str, str], None] = None,
    ):
        super().__init__(parent)
        self.on_search = on_search
        self.on_navigate = on_navigate
        self._result_map: dict[str, SearchResult] = {}

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 搜索输入框
        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(0)

        self.entry = QLineEdit()
        self.entry.setPlaceholderText("搜索所有模块...")
        self.entry.textChanged.connect(self._on_text_changed)
        self.entry.returnPressed.connect(self._do_search)
        input_row.addWidget(self.entry)

        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self._do_search)
        input_row.addWidget(search_btn)

        layout.addLayout(input_row)

        # 下拉结果树
        self._tree = QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setColumnCount(1)
        self._tree.setSelectionMode(self._tree.SingleSelection)
        self._tree.itemDoubleClicked.connect(self._on_select)
        self._tree.itemActivated.connect(self._on_select)
        self._tree.hide()
        self._tree.setMaximumHeight(300)
        self._tree.setStyleSheet(
            "QTreeWidget { border: 1px solid #ccc; background: #fff; }"
        )
        layout.addWidget(self._tree)

        layout.addStretch()

        # 防抖
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._do_search)

    def _on_text_changed(self, text: str) -> None:
        if not text.strip() or text.strip() == "搜索所有模块...":
            self._hide_results()
            return
        self._debounce_timer.start(300)

    def _do_search(self) -> None:
        keyword = self.entry.text().strip()
        if not keyword:
            self._hide_results()
            return
        if self.on_search is None:
            return
        results = self.on_search(keyword)
        if results:
            self._show_results(results)
        else:
            self._hide_results()

    def _show_results(self, results: list[SearchResult]) -> None:
        self._tree.clear()
        self._result_map.clear()

        groups: dict[str, list[SearchResult]] = {}
        for r in results:
            groups.setdefault(r.module, []).append(r)

        for module, items in groups.items():
            label = MODULE_LABELS.get(module, module)
            parent = QTreeWidgetItem(self._tree)
            parent.setText(0, f"{label} ({len(items)})")
            parent.setData(0, Qt.UserRole, f"__grp_{module}")
            parent.setFont(0, QFont("Microsoft YaHei", 9, QFont.Bold))
            parent.setForeground(0, Qt.GlobalColor.blue)
            parent.setFlags(parent.flags() & ~Qt.ItemIsSelectable)
            parent.setExpanded(True)

            for item in items:
                child = QTreeWidgetItem(parent)
                child.setText(0, f"  {item.name}  — {item.snippet}" if item.snippet else f"  {item.name}")
                child.setData(0, Qt.UserRole, f"{module}_{item.item_id}")
                self._result_map[f"{module}_{item.item_id}"] = item

        self._tree.show()

    def _on_select(self, item: QTreeWidgetItem, _col: int = 0) -> None:
        iid = item.data(0, Qt.UserRole)
        if iid and iid.startswith("__grp_"):
            return
        result = self._result_map.get(iid)
        if result and self.on_navigate:
            self._hide_results()
            self.on_navigate(result.module, result.item_id)

    def _hide_results(self) -> None:
        self._tree.hide()
        self._tree.clear()
        self._result_map.clear()

    # ---- 公开方法 ----

    def focus(self) -> None:
        self.entry.setFocus()
        self.entry.selectAll()
