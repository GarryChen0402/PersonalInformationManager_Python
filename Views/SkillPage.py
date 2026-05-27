"""技能管理页面 — PySide6 版本。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel,
    QTableWidgetItem, QFileDialog, QMessageBox, QMenu, QHeaderView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from Services.SkillManager import SkillManager
from Models.Skill import Skill
from .BasePage import BasePage
from .Widgets import SearchBar, FormDialog, ConfirmDialog, CSVPreviewDialog
from .ChartWidgets import RadarChart, BarChart


class SkillPage(BasePage):
    """技能管理页面，三段式布局。"""

    def __init__(self, parent=None, set_status=None):
        super().__init__(parent, set_status)
        self.manager = SkillManager()

        self._build_toolbar()
        self._build_charts()
        self._build_table_columns()
        self._build_context_menu()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 4, 0, 4)

        self.search_bar = SearchBar(placeholder="搜索技能...")
        self.search_bar.search_requested.connect(self._on_search)
        toolbar_layout.addWidget(self.search_bar)

        toolbar_layout.addWidget(QLabel("类别："))
        self.category_filter = QComboBox()
        self.category_filter.currentTextChanged.connect(self._on_filter)
        toolbar_layout.addWidget(self.category_filter)

        toolbar_layout.addStretch()

        add_btn = QPushButton("+ 添加技能")
        add_btn.clicked.connect(self._open_add_dialog)
        toolbar_layout.addWidget(add_btn)

        export_btn = QPushButton("导出CSV")
        export_btn.clicked.connect(self._export_csv)
        toolbar_layout.addWidget(export_btn)

        import_btn = QPushButton("导入CSV")
        import_btn.clicked.connect(self._import_csv)
        toolbar_layout.addWidget(import_btn)

        self._layout.insertWidget(0, toolbar)

    # ---- 表格 ----

    def _build_table_columns(self) -> None:
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["技能名称", "类别", "熟练度", "学习时长(h)", "描述"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self._open_edit_dialog)

    # ---- 图表 ----

    def _build_charts(self) -> None:
        charts_widget = QWidget()
        charts_layout = QHBoxLayout(charts_widget)
        charts_layout.setContentsMargins(0, 0, 0, 0)

        self.radar_chart = RadarChart(title="技能分布")
        charts_layout.addWidget(self.radar_chart)

        self.bar_chart = BarChart(title="类别分布")
        charts_layout.addWidget(self.bar_chart)

        self._layout.insertWidget(1, charts_widget)

    def _load_chart_data(self) -> None:
        skills = self.manager.get_all()

        top = skills[:6]
        if top:
            self.radar_chart.set_data(
                [s.name for s in top], [s.level for s in top], max_val=5
            )
        else:
            self.radar_chart.set_data([], [])

        stats = self.manager.get_statistics()
        by_cat = stats.get("by_category", {})
        if by_cat:
            cats = sorted(by_cat.keys())
            self.bar_chart.set_data(cats, [by_cat[c] for c in cats])
        else:
            self.bar_chart.set_data([], [])

    # ---- 右键菜单 ----

    def _build_context_menu(self) -> QMenu | None:
        skill_id = self._get_selected_id()
        if not skill_id:
            return None
        menu = QMenu(self)
        menu.addAction("编辑", self._open_edit_dialog)
        menu.addSeparator()
        menu.addAction("删除", self._confirm_delete)
        return menu

    # ---- 添加 ----

    def _open_add_dialog(self) -> None:
        categories = self.manager.get_all_categories() or ["编程", "语言", "工具", "其他"]
        fields = [
            {"key": "name", "label": "技能名称", "type": "text", "required": True},
            {"key": "category", "label": "类别", "type": "combo", "options": categories},
            {"key": "level", "label": "熟练度", "type": "spinbox", "from_": 1, "to": 5},
            {"key": "hours_spent", "label": "学习时长(h)", "type": "text"},
            {"key": "description", "label": "描述", "type": "textarea"},
        ]
        data = FormDialog.get_form_data(self, "添加技能", fields)
        if data:
            self._do_add(data)

    def _do_add(self, data: dict) -> None:
        try:
            level = int(data["level"])
            hours = float(data["hours_spent"]) if data["hours_spent"] else 0.0
            self.manager.add_skill(
                name=data["name"], category=data["category"],
                level=level, hours_spent=hours,
                description=data.get("description", "")
            )
            self.refresh()
            self.emit_status(f"技能「{data['name']}」已添加")
        except Exception as e:
            QMessageBox.critical(self, "添加失败", str(e))

    # ---- 编辑 ----

    def _open_edit_dialog(self) -> None:
        skill = self._get_selected()
        if not skill:
            return
        categories = self.manager.get_all_categories() or ["编程", "语言", "工具", "其他"]
        fields = [
            {"key": "name", "label": "技能名称", "type": "text", "required": True},
            {"key": "category", "label": "类别", "type": "combo", "options": categories},
            {"key": "level", "label": "熟练度", "type": "spinbox", "from_": 1, "to": 5},
            {"key": "hours_spent", "label": "学习时长(h)", "type": "text"},
            {"key": "description", "label": "描述", "type": "textarea"},
        ]
        initial = {
            "name": skill.name, "category": skill.category,
            "level": skill.level, "hours_spent": str(skill.hours_spent),
            "description": skill.description,
        }
        data = FormDialog.get_form_data(self, "编辑技能", fields, initial)
        if data:
            self._do_edit(skill.id, data)

    def _do_edit(self, skill_id: str, data: dict) -> None:
        try:
            updates = {
                "name": data["name"], "category": data["category"],
                "level": int(data["level"]),
                "hours_spent": float(data["hours_spent"]) if data["hours_spent"] else 0.0,
                "description": data.get("description", ""),
            }
            self.manager.update_skill(skill_id, **updates)
            self.refresh()
            self.emit_status(f"技能「{data['name']}」已更新")
        except Exception as e:
            QMessageBox.critical(self, "编辑失败", str(e))

    # ---- 删除 ----

    def _confirm_delete(self) -> None:
        skill = self._get_selected()
        if not skill:
            return
        if ConfirmDialog.show(self, "确认删除", f"确定要删除技能「{skill.name}」吗？"):
            self.manager.delete_skill(skill.id)
            self.refresh()
            self.emit_status(f"技能「{skill.name}」已删除")

    # ---- 筛选和搜索 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self.refresh()
            return
        results = self.manager.search(keyword)
        self._populate_table(results)

    def _on_filter(self, category: str) -> None:
        if not category or category == "全部":
            self.refresh()
            return
        results = self.manager.get_by_category(category)
        self._populate_table(results)

    # ---- 数据加载 ----

    def refresh(self) -> None:
        skills = self.manager.get_all()
        self._populate_table(skills)
        self._load_chart_data()

        categories = self.manager.get_all_categories()
        self.category_filter.blockSignals(True)
        self.category_filter.clear()
        self.category_filter.addItem("全部")
        self.category_filter.addItems(categories)
        self.category_filter.setCurrentIndex(0)
        self.category_filter.blockSignals(False)

        stats = self.manager.get_statistics()
        parts = [f"共 {stats['total']} 项技能"]
        if stats["total"] > 0:
            parts.append(f"总学习时长: {stats['total_hours']:.1f}h")
            parts.append(f"平均熟练度: {stats['avg_level']}/5")
        self._set_stats_text("  |  ".join(parts))

    def _populate_table(self, skills: list[Skill]) -> None:
        self._clear_table()
        for s in skills:
            self._add_row([
                s.name, s.category, f"{s.level}/5",
                str(s.hours_spent), s.description
            ], item_id=s.id)

    def _get_selected(self) -> Skill | None:
        skill_id = self._get_selected_id()
        if not skill_id:
            QMessageBox.information(self, "提示", "请先选中一条记录")
            return None
        return self.manager.get_by_id(skill_id)

    # ---- CSV ----

    def _export_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "导出技能数据", "skills.csv", "CSV 文件 (*.csv)"
        )
        if path:
            try:
                self.manager.export_csv(path)
                self.emit_status(f"技能数据已导出到 {path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def _import_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "导入技能数据", "", "CSV 文件 (*.csv)"
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
