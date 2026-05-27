"""知识管理页面 — PySide6 版本，笔记 + 电子书双 Tab。"""

import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTabWidget,
    QPushButton, QComboBox, QLabel, QTextEdit, QLineEdit,
    QTableWidgetItem, QFileDialog, QMessageBox, QMenu, QHeaderView,
    QDialog, QFormLayout, QDialogButtonBox, QFrame
)
from PySide6.QtCore import Qt

from Services.KnowledgeManager import KnowledgeManager
from Models.Knowledge import KnowledgeItem
from .BasePage import BasePage
from .Widgets import SearchBar, FormDialog, ConfirmDialog, KeywordEntry
from .ChartWidgets import BarChart


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


def _format_keywords(keywords: list) -> str:
    if not keywords:
        return "-"
    return " ".join(keywords[:3]) + ("..." if len(keywords) > 3 else "")


# ============================================================
#  KnowledgePage 主框架
# ============================================================

class KnowledgePage(QWidget):
    """知识管理页面，包含笔记 / 电子书两个 Tab。"""

    def __init__(self, parent=None, set_status=None):
        super().__init__(parent)
        self.manager = KnowledgeManager()
        self._set_status = set_status
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.notebook = QTabWidget()
        self.note_tab = NoteTabView(self.manager, self._set_status)
        self.ebook_tab = EbookTabView(self.manager, self._set_status)
        self.notebook.addTab(self.note_tab, "文本笔记")
        self.notebook.addTab(self.ebook_tab, "PDF电子书")
        layout.addWidget(self.notebook)

    def refresh(self) -> None:
        current = self.notebook.currentWidget()
        if current and hasattr(current, "refresh"):
            current.refresh()

    def highlight_item(self, item_id: str, item_type: str = "note") -> None:
        if item_type == "ebook":
            self.notebook.setCurrentWidget(self.ebook_tab)
            self.ebook_tab.highlight_item(item_id)
        else:
            self.notebook.setCurrentWidget(self.note_tab)
            self.note_tab.highlight_item(item_id)


# ============================================================
#  NoteTabView — 文本笔记
# ============================================================

class NoteTabView(QWidget):
    """文本笔记子视图，左右分栏布局。"""

    def __init__(self, manager: KnowledgeManager, set_status, parent=None):
        super().__init__(parent)
        self.manager = manager
        self._set_status = set_status
        self.current_note: KnowledgeItem | None = None

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # 工具栏
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(8, 6, 8, 6)

        self.search_bar = SearchBar(placeholder="搜索笔记...")
        self.search_bar.search_requested.connect(self._on_search)
        toolbar_layout.addWidget(self.search_bar)

        toolbar_layout.addWidget(QLabel("类别："))
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self._on_filter)
        toolbar_layout.addWidget(self.category_filter)

        toolbar_layout.addStretch()

        export_btn = QPushButton("导出CSV")
        export_btn.clicked.connect(self._export_csv)
        toolbar_layout.addWidget(export_btn)

        add_btn = QPushButton("+ 新建笔记")
        add_btn.clicked.connect(self._open_create_dialog)
        toolbar_layout.addWidget(add_btn)
        layout.addWidget(toolbar)

        # 左右分栏
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：笔记列表
        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(4, 0, 0, 0)

        self.note_table = self._build_list_table()
        left_layout.addWidget(self.note_table)
        splitter.addWidget(left)

        # 右侧：详情编辑面板
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 4, 0)

        self._build_detail_panel(right_layout)
        splitter.addWidget(right)

        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        layout.addWidget(splitter)

        # 类别分布图
        self.note_bar_chart = BarChart(title="")
        self.note_bar_chart.setMinimumHeight(150)
        layout.addWidget(self.note_bar_chart)

        # 底部统计
        self.stats_label = QLabel()
        self.stats_label.setProperty("statsLabel", True)
        layout.addWidget(self.stats_label)

    def _build_list_table(self) -> QWidget:
        """构建笔记列表表格。"""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        self.tree = self.note_table = self._make_table()
        self.tree.setColumnCount(4)
        self.tree.setHorizontalHeaderLabels(["标题", "类别", "关键词", "更新时间"])
        self.tree.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.tree.itemSelectionChanged.connect(self._on_select_note)
        layout.addWidget(self.tree)
        return container

    def _make_table(self):
        from PySide6.QtWidgets import QTableWidget
        t = QTableWidget()
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.setSelectionMode(QTableWidget.SingleSelection)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setStretchLastSection(True)
        t.setSortingEnabled(True)
        return t

    def _build_detail_panel(self, layout: QVBoxLayout) -> None:
        form = QWidget()
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(8, 8, 8, 8)
        form_layout.setSpacing(8)

        # 标题
        form_layout.addWidget(QLabel("标题："))
        self.title_entry = QLineEdit()
        form_layout.addWidget(self.title_entry)

        # 类别
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("类别："))
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.manager.VALID_CATEGORIES)
        row1.addWidget(self.category_combo)
        row1.addStretch()
        form_layout.addLayout(row1)

        # 关键词
        form_layout.addWidget(QLabel("关键词："))
        self.keyword_entry = KeywordEntry()
        form_layout.addWidget(self.keyword_entry)

        # 内容
        form_layout.addWidget(QLabel("内容："))
        self.content_text = QTextEdit()
        form_layout.addWidget(self.content_text)

        # 操作按钮
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("保存修改")
        self.save_btn.clicked.connect(self._save_current_note)
        btn_row.addWidget(self.save_btn)

        self.delete_btn = QPushButton("删除笔记")
        self.delete_btn.clicked.connect(self._confirm_delete)
        btn_row.addWidget(self.delete_btn)
        btn_row.addStretch()
        form_layout.addLayout(btn_row)

        layout.addWidget(form)

        self._toggle_detail_editing(False)

    def _toggle_detail_editing(self, enabled: bool) -> None:
        self.title_entry.setEnabled(enabled)
        self.category_combo.setEnabled(enabled)
        self.content_text.setEnabled(enabled)
        self.keyword_entry.entry.setEnabled(enabled)
        self.save_btn.setEnabled(enabled)
        self.delete_btn.setEnabled(enabled)

    # ---- 选择笔记 ----

    def _on_select_note(self) -> None:
        row = self.tree.currentRow()
        if row < 0:
            return
        item = self.tree.item(row, 0)
        if not item:
            return
        note_id = item.data(Qt.UserRole)
        note = self.manager.get_by_id(note_id)
        if note:
            self._display_note(note)

    def _display_note(self, note: KnowledgeItem) -> None:
        self.current_note = note
        self._toggle_detail_editing(True)

        self.title_entry.setText(note.title)
        if note.category in self.manager.VALID_CATEGORIES:
            self.category_combo.setCurrentText(note.category)
        else:
            self.category_combo.setCurrentIndex(-1)
        self.keyword_entry.set_keywords(note.keywords)
        self.content_text.setPlainText(note.content)

    # ---- 新建 ----

    def _open_create_dialog(self) -> None:
        fields = [
            {"key": "title", "label": "标题", "type": "text", "required": True},
            {"key": "category", "label": "类别", "type": "combo",
             "options": self.manager.VALID_CATEGORIES},
            {"key": "content", "label": "内容", "type": "textarea"},
        ]
        data = FormDialog.get_form_data(self, "新建笔记", fields)
        if data:
            self._do_create(data)

    def _do_create(self, data: dict) -> None:
        try:
            note = self.manager.create_note(
                title=data["title"],
                category=data.get("category", ""),
                keywords=[],
                content=data.get("content", "")
            )
            self.refresh()
            self._emit_status(f"笔记「{note.title}」已创建")
        except Exception as e:
            QMessageBox.critical(self, "创建失败", str(e))

    # ---- 保存 ----

    def _save_current_note(self) -> None:
        if not self.current_note:
            return
        try:
            self.manager.update_note(
                self.current_note.id,
                title=self.title_entry.text().strip(),
                category=self.category_combo.currentText(),
                keywords=self.keyword_entry.get_keywords(),
                content=self.content_text.toPlainText().strip()
            )
            self.current_note = self.manager.get_by_id(self.current_note.id)
            self._emit_status(f"笔记「{self.current_note.title}」已保存")
            self._refresh_note_list()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    # ---- 删除 ----

    def _confirm_delete(self) -> None:
        if not self.current_note:
            return
        if ConfirmDialog.show(self, "确认删除",
                              f"确定要删除笔记「{self.current_note.title}」吗？"):
            self.manager.delete_item(self.current_note.id)
            self.current_note = None
            self._clear_detail()
            self.refresh()
            self._emit_status("笔记已删除")

    def _clear_detail(self) -> None:
        self._toggle_detail_editing(False)
        self.title_entry.clear()
        self.content_text.clear()
        self.keyword_entry.set_keywords([])

    # ---- 搜索和筛选 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self._refresh_note_list()
            return
        results = self.manager.search(keyword)
        results = [r for r in results if r.item_type == "note"]
        self._populate_note_table(results)

    def _on_filter(self, category: str) -> None:
        if not category or category == "全部":
            self._refresh_note_list()
            return
        results = self.manager.get_by_category(category, item_type="note")
        self._populate_note_table(results)

    # ---- 数据刷新 ----

    def refresh(self) -> None:
        self._refresh_note_list()
        self._update_stats()

    def highlight_item(self, item_id: str) -> None:
        for row in range(self.tree.rowCount()):
            item = self.tree.item(row, 0)
            if item and item.data(Qt.UserRole) == item_id:
                self.tree.selectRow(row)
                self.tree.scrollToItem(item)
                return

    def _refresh_note_list(self) -> None:
        notes = self.manager.get_all(item_type="note")
        self._populate_note_table(notes)

        categories = self.manager.get_all_categories(item_type="note")
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("全部")
        self.category_filter.addItems(categories)
        self.category_filter.setCurrentIndex(0)
        self.category_filter.blockSignals(False)

    def _populate_note_table(self, notes: list[KnowledgeItem]) -> None:
        self.tree.setRowCount(0)
        for n in notes:
            row = self.tree.rowCount()
            self.tree.insertRow(row)
            for col, text in enumerate([
                n.title,
                n.category,
                _format_keywords(n.keywords),
                n.updated_at[:10] if n.updated_at else n.created_at[:10],
            ]):
                item = QTableWidgetItem(text)
                if col == 0:
                    item.setData(Qt.UserRole, n.id)
                self.tree.setItem(row, col, item)

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "导出笔记数据", "notes.csv", "CSV 文件 (*.csv)"
        )
        if path:
            try:
                self.manager.export_notes_csv(path)
                self._emit_status(f"笔记数据已导出到 {path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def _update_stats(self) -> None:
        stats = self.manager.get_statistics()
        cats = ", ".join(f"{k}:{v}" for k, v in stats["by_category"].items())
        text = f"共 {stats['total_notes']} 篇笔记"
        if cats:
            text += f"  |  {cats}"
        self.stats_label.setText(text)

        # 更新类别柱状图
        notes = self.manager.get_all(item_type="note")
        by_cat: dict[str, int] = {}
        for n in notes:
            cat = n.category or "其他"
            by_cat[cat] = by_cat.get(cat, 0) + 1
        if by_cat:
            sorted_cats = sorted(by_cat.keys())
            self.note_bar_chart.set_data(sorted_cats, [by_cat[c] for c in sorted_cats])
        else:
            self.note_bar_chart.set_data([], [])

    def _emit_status(self, text: str) -> None:
        if self._set_status:
            self._set_status(text)


# ============================================================
#  EbookTabView — PDF 电子书
# ============================================================

class EbookTabView(BasePage):
    """PDF 电子书子视图。"""

    def __init__(self, manager: KnowledgeManager, set_status, parent=None):
        super().__init__(parent, set_status)
        self.manager = manager

        self._build_toolbar()
        self._build_table_columns()

    def _build_toolbar(self) -> None:
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 4, 0, 4)

        self.search_bar = SearchBar(placeholder="搜索电子书...")
        self.search_bar.search_requested.connect(self._on_search)
        toolbar_layout.addWidget(self.search_bar)

        toolbar_layout.addWidget(QLabel("类别："))
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self._on_filter)
        toolbar_layout.addWidget(self.category_filter)

        toolbar_layout.addStretch()

        import_btn = QPushButton("+ 导入电子书")
        import_btn.clicked.connect(self._open_import_dialog)
        toolbar_layout.addWidget(import_btn)

        self._layout.insertWidget(0, toolbar)

    def _build_table_columns(self) -> None:
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "书名", "类别", "关键词", "大小", "导入时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._open_ebook)

    # ---- 右键菜单 ----

    def _build_context_menu(self) -> QMenu | None:
        ebook_id = self._get_selected_id()
        if not ebook_id:
            return None
        menu = QMenu(self)
        menu.addAction("打开阅读", self._open_ebook)
        menu.addSeparator()
        menu.addAction("编辑信息", self._open_edit_dialog)
        menu.addSeparator()
        menu.addAction("删除", self._confirm_delete)
        return menu

    # ---- 导入 ----

    def _open_import_dialog(self) -> None:
        dialog = EbookImportDialog(self.manager, self.refresh, self)
        dialog.exec()

    # ---- 打开 ----

    def _open_ebook(self) -> None:
        item = self._get_selected()
        if not item:
            return
        try:
            self.manager.open_ebook(item.id)
            self.emit_status(f"正在打开「{item.title}」...")
        except Exception as e:
            QMessageBox.critical(self, "打开失败", str(e))

    # ---- 编辑信息 ----

    def _open_edit_dialog(self) -> None:
        item = self._get_selected()
        if not item:
            return
        categories = self.manager.get_all_categories(item_type="ebook") or self.manager.VALID_CATEGORIES
        dialog = EbookEditDialog(item, categories, lambda d: self._do_edit(item.id, d), self)
        dialog.exec()

    def _do_edit(self, ebook_id: str, data: dict) -> None:
        try:
            self.manager.update_ebook_info(
                ebook_id, title=data["title"],
                category=data["category"], keywords=data["keywords"]
            )
            self.refresh()
            self.emit_status(f"电子书「{data['title']}」信息已更新")
        except Exception as e:
            QMessageBox.critical(self, "编辑失败", str(e))

    # ---- 删除 ----

    def _confirm_delete(self) -> None:
        item = self._get_selected()
        if not item:
            return

        from PySide6.QtWidgets import QMessageBox as QMB
        result = QMB.question(
            self, "确认删除",
            f"确定要删除电子书「{item.title}」吗？\n\n"
            f"选「Yes」同时删除 PDF 文件\n"
            f"选「No」仅删除记录，保留文件",
            QMB.Yes | QMB.No | QMB.Cancel, QMB.Cancel
        )
        if result == QMB.Cancel:
            return
        delete_file = result == QMB.Yes
        self.manager.delete_item(item.id, delete_file=delete_file)
        self.refresh()
        self.emit_status(f"电子书「{item.title}」已删除")

    # ---- 搜索筛选 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self.refresh()
            return
        results = self.manager.search(keyword)
        results = [r for r in results if r.item_type == "ebook"]
        self._populate_table(results)

    def _on_filter(self, category: str) -> None:
        if not category or category == "全部":
            self.refresh()
            return
        results = self.manager.get_by_category(category, item_type="ebook")
        self._populate_table(results)

    # ---- 数据刷新 ----

    def refresh(self) -> None:
        ebooks = self.manager.get_all(item_type="ebook")
        self._populate_table(ebooks)

        categories = self.manager.get_all_categories(item_type="ebook")
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("全部")
        self.category_filter.addItems(categories)
        self.category_filter.setCurrentIndex(0)
        self.category_filter.blockSignals(False)

        stats = self.manager.get_statistics()
        self._set_stats_text(f"共 {stats['total_ebooks']} 本电子书")

    def _populate_table(self, ebooks: list[KnowledgeItem]) -> None:
        self._clear_table()
        for eb in ebooks:
            self._add_row([
                eb.title,
                eb.category,
                _format_keywords(eb.keywords),
                _format_size(eb.file_size),
                eb.created_at[:10] if eb.created_at else "-",
            ], item_id=eb.id)

    def _get_selected(self) -> KnowledgeItem | None:
        ebook_id = self._get_selected_id()
        if not ebook_id:
            QMessageBox.information(self, "提示", "请先选中一本电子书")
            return None
        return self.manager.get_by_id(ebook_id)


# ============================================================
#  EbookImportDialog — 导入电子书
# ============================================================

class EbookImportDialog(QDialog):
    """PDF 电子书导入对话框。"""

    def __init__(self, manager: KnowledgeManager, on_done, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导入 PDF 电子书")
        self.setModal(True)
        self.manager = manager
        self.on_done = on_done
        self.source_path = ""
        self.setMinimumWidth(420)

        self._build()

    def _build(self) -> None:
        layout = QFormLayout(self)
        layout.setSpacing(8)

        # PDF 文件选择
        file_row = QHBoxLayout()
        self.file_label = QLabel("未选择文件")
        self.file_label.setStyleSheet("color: #999999;")
        file_row.addWidget(self.file_label)

        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_file)
        file_row.addWidget(browse_btn)
        layout.addRow("PDF 文件：", file_row)

        # 文件大小
        self.size_label = QLabel("")
        self.size_label.setStyleSheet("color: #666666;")
        layout.addRow("", self.size_label)

        # 书名
        self.title_entry = QLineEdit()
        layout.addRow("书名：", self.title_entry)

        # 类别
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.manager.VALID_CATEGORIES)
        self.category_combo.setCurrentText("技术")
        layout.addRow("类别：", self.category_combo)

        # 关键词
        self.keyword_entry = KeywordEntry()
        layout.addRow("关键词：", self.keyword_entry)

        # 按钮
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("导入")
        buttons.accepted.connect(self._do_import)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _browse_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "选择 PDF 文件", "", "PDF 文件 (*.pdf);;所有文件 (*.*)"
        )
        if path:
            self.source_path = path
            basename = os.path.basename(path)
            self.file_label.setText(basename if len(basename) < 50 else basename[:47] + "...")

            size = os.path.getsize(path)
            self.size_label.setText(f"文件大小：{_format_size(size)}")

            name = os.path.splitext(basename)[0]
            self.title_entry.setText(name)

    def _do_import(self) -> None:
        if not self.source_path:
            QMessageBox.warning(self, "提示", "请先选择 PDF 文件")
            return
        try:
            self.manager.import_ebook(
                source_path=self.source_path,
                title=self.title_entry.text().strip(),
                category=self.category_combo.currentText(),
                keywords=self.keyword_entry.get_keywords()
            )
            self.on_done()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "导入失败", str(e))


# ============================================================
#  EbookEditDialog — 编辑电子书信息
# ============================================================

class EbookEditDialog(QDialog):
    """编辑电子书元数据对话框。"""

    def __init__(self, item: KnowledgeItem, categories: list[str], on_save, parent=None):
        super().__init__(parent)
        self.setWindowTitle("编辑电子书信息")
        self.setModal(True)
        self.setMinimumWidth(380)

        layout = QFormLayout(self)
        layout.setSpacing(8)

        self.title_entry = QLineEdit(item.title)
        layout.addRow("书名：", self.title_entry)

        self.cat_combo = QComboBox()
        self.cat_combo.addItems(categories)
        self.cat_combo.setCurrentText(item.category)
        layout.addRow("类别：", self.cat_combo)

        self.kw_entry = KeywordEntry()
        self.kw_entry.set_keywords(item.keywords)
        layout.addRow("关键词：", self.kw_entry)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("保存")
        buttons.accepted.connect(lambda: self._save(on_save))
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _save(self, on_save) -> None:
        on_save({
            "title": self.title_entry.text().strip(),
            "category": self.cat_combo.currentText(),
            "keywords": self.kw_entry.get_keywords(),
        })
        self.accept()
