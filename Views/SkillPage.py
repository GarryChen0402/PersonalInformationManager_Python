"""技能管理页面。"""

import tkinter as tk
from tkinter import ttk, messagebox

from Services.SkillManager import SkillManager
from Models.Skill import Skill
from .Widgets import SearchBar, FormDialog, ConfirmDialog
from .ChartWidgets import RadarChart, BarChart


class SkillPage(tk.Frame):
    """技能管理页面，三段式布局。"""

    def __init__(self, parent: tk.Widget, set_status):
        super().__init__(parent, bg="#ffffff")
        self.manager = SkillManager()
        self.set_status = set_status

        self._build_toolbar()
        self._build_charts()
        self._build_table()
        self._build_context_menu()
        self._build_stats_bar()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self, bg="#fafafa", pady=8)
        toolbar.pack(fill=tk.X, padx=12, pady=(12, 0))

        self.search_bar = SearchBar(toolbar, on_search=self._on_search)
        self.search_bar.pack(side=tk.LEFT, padx=4)

        tk.Label(toolbar, text="类别：", bg="#fafafa",
                 font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(8, 2))

        self.category_filter = ttk.Combobox(
            toolbar, state="readonly", width=10,
            font=("Microsoft YaHei", 9)
        )
        self.category_filter.pack(side=tk.LEFT, padx=4)
        self.category_filter.bind("<<ComboboxSelected>>", lambda e: self._on_filter())

        add_btn = tk.Button(
            toolbar, text="+ 添加技能", command=self._open_add_dialog,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        add_btn.pack(side=tk.RIGHT, padx=4)

    # ---- 表格 ----

    def _build_table(self) -> None:
        columns = ("name", "category", "level", "hours", "description")
        self.tree = ttk.Treeview(self, columns=columns, show="headings",
                                 selectmode="browse")

        self.tree.heading("name", text="技能名称")
        self.tree.heading("category", text="类别")
        self.tree.heading("level", text="熟练度")
        self.tree.heading("hours", text="学习时长(h)")
        self.tree.heading("description", text="描述")

        self.tree.column("name", width=150)
        self.tree.column("category", width=80)
        self.tree.column("level", width=60, anchor=tk.CENTER)
        self.tree.column("hours", width=90, anchor=tk.CENTER)
        self.tree.column("description", width=200)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12), pady=8)

        self.tree.bind("<Double-1>", lambda e: self._open_edit_dialog())

    # ---- 右键菜单 ----

    def _build_context_menu(self) -> None:
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="编辑", command=self._open_edit_dialog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=self._confirm_delete)

        self.tree.bind("<Button-3>" if not self._is_mac() else "<Button-2>",
                       self._show_context_menu)

    @staticmethod
    def _is_mac() -> bool:
        import sys
        return sys.platform == "darwin"

    def _show_context_menu(self, event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    # ---- 统计栏 ----

    def _build_stats_bar(self) -> None:
        self.stats_var = tk.StringVar()
        stats = tk.Label(
            self, textvariable=self.stats_var, bg="#f5f5f5",
            font=("Microsoft YaHei", 9), fg="#666666", pady=6
        )
        stats.pack(fill=tk.X, side=tk.BOTTOM)

    # ---- 图表 ----

    def _build_charts(self) -> None:
        """构建技能图表区域（雷达图 + 柱状图并排）。"""
        charts_frame = tk.Frame(self, bg="#ffffff")
        charts_frame.pack(fill=tk.X, padx=12, pady=(4, 0))

        left = tk.Frame(charts_frame, bg="#ffffff")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        self.radar_chart = RadarChart(left, width=280, height=260, title="技能分布")
        self.radar_chart.pack()

        right = tk.Frame(charts_frame, bg="#ffffff")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))

        self.bar_chart = BarChart(right, width=280, height=260, title="类别分布")
        self.bar_chart.pack()

    def _load_chart_data(self) -> None:
        """加载图表数据。"""
        skills = self.manager.get_all()

        # 雷达图：熟练度最高的前 6 项技能
        top = skills[:6]
        if top:
            self.radar_chart.set_data(
                [s.name for s in top],
                [s.level for s in top],
                max_val=5,
            )
        else:
            self.radar_chart.set_data([], [])

        # 柱状图：类别分布
        stats = self.manager.get_statistics()
        by_cat = stats.get("by_category", {})
        if by_cat:
            cats = sorted(by_cat.keys())
            self.bar_chart.set_data(cats, [by_cat[c] for c in cats])
        else:
            self.bar_chart.set_data([], [])

    # ---- 添加 ----

    def _open_add_dialog(self) -> None:
        categories = self.manager.get_all_categories() or self.manager.VALID_CATEGORIES
        fields = [
            {"name": "name", "label": "技能名称", "type": "text", "required": True},
            {"name": "category", "label": "类别", "type": "combobox", "options": categories},
            {"name": "level", "label": "熟练度", "type": "spinbox", "from_": 1, "to": 5},
            {"name": "hours_spent", "label": "学习时长(h)", "type": "text"},
            {"name": "description", "label": "描述", "type": "textarea"},
        ]
        FormDialog(self, "添加技能", fields, on_save=self._do_add)

    def _do_add(self, data: dict) -> None:
        try:
            level = int(data["level"])
            hours = float(data["hours_spent"]) if data["hours_spent"] else 0.0
            self.manager.add_skill(
                name=data["name"], category=data["category"],
                level=level, hours_spent=hours, description=data.get("description", "")
            )
            self.refresh()
            self.set_status(f"技能「{data['name']}」已添加")
        except Exception as e:
            messagebox.showerror("添加失败", str(e))

    # ---- 编辑 ----

    def _open_edit_dialog(self) -> None:
        skill = self._get_selected()
        if not skill:
            return

        categories = self.manager.get_all_categories() or self.manager.VALID_CATEGORIES
        fields = [
            {"name": "name", "label": "技能名称", "type": "text", "required": True},
            {"name": "category", "label": "类别", "type": "combobox", "options": categories},
            {"name": "level", "label": "熟练度", "type": "spinbox", "from_": 1, "to": 5},
            {"name": "hours_spent", "label": "学习时长(h)", "type": "text"},
            {"name": "description", "label": "描述", "type": "textarea"},
        ]
        initial = {
            "name": skill.name, "category": skill.category,
            "level": skill.level, "hours_spent": str(skill.hours_spent),
            "description": skill.description,
        }
        FormDialog(self, "编辑技能", fields, on_save=lambda d: self._do_edit(skill.id, d),
                   initial_data=initial)

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
            self.set_status(f"技能「{data['name']}」已更新")
        except Exception as e:
            messagebox.showerror("编辑失败", str(e))

    # ---- 删除 ----

    def _confirm_delete(self) -> None:
        skill = self._get_selected()
        if not skill:
            return
        if ConfirmDialog.show(self, "确认删除", f"确定要删除技能「{skill.name}」吗？"):
            self.manager.delete_skill(skill.id)
            self.refresh()
            self.set_status(f"技能「{skill.name}」已删除")

    # ---- 筛选和搜索 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self.refresh()
            return
        results = self.manager.search(keyword)
        self._populate_tree(results)

    def _on_filter(self) -> None:
        category = self.category_filter.get()
        if not category or category == "全部":
            self.refresh()
            return
        results = self.manager.get_by_category(category)
        self._populate_tree(results)

    # ---- 数据加载 ----

    def refresh(self) -> None:
        """重新加载技能列表、图表和筛选选项。"""
        skills = self.manager.get_all()
        self._populate_tree(skills)

        self._load_chart_data()

        # 更新类别筛选
        categories = self.manager.get_all_categories()
        self.category_filter["values"] = ["全部"] + categories
        if not self.category_filter.get():
            self.category_filter.set("全部")

        # 更新统计栏
        stats = self.manager.get_statistics()
        parts = [f"共 {stats['total']} 项技能"]
        if stats["total"] > 0:
            parts.append(f"总学习时长: {stats['total_hours']:.1f}h")
            parts.append(f"平均熟练度: {stats['avg_level']}/5")
        self.stats_var.set("  |  ".join(parts))

    def _populate_tree(self, skills: list[Skill]) -> None:
        """用技能列表填充 Treeview。"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for s in skills:
            self.tree.insert("", tk.END, iid=s.id, values=(
                s.name, s.category, f"{s.level}/5", s.hours_spent, s.description
            ))

    def _get_selected(self) -> Skill | None:
        """获取当前选中行的 Skill 对象。"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选中一条记录")
            return None
        return self.manager.get_by_id(selection[0])
