"""知识管理页面 — 笔记 + 电子书双 Tab。"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from Services.KnowledgeManager import KnowledgeManager
from Models.Knowledge import KnowledgeItem
from .Widgets import SearchBar, FormDialog, ConfirmDialog, KeywordEntry
from .ChartWidgets import BarChart


def _format_size(size_bytes: int) -> str:
    """格式化文件大小显示。"""
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

class KnowledgePage(tk.Frame):
    """知识管理页面，包含笔记 / 电子书两个 Tab。"""

    def __init__(self, parent: tk.Widget, set_status):
        super().__init__(parent, bg="#ffffff")
        self.manager = KnowledgeManager()
        self.set_status = set_status

        self.notebook = ttk.Notebook(self)
        self.note_tab = NoteTabView(self.notebook, self.manager, self.set_status)
        self.ebook_tab = EbookTabView(self.notebook, self.manager, self.set_status)
        self.notebook.add(self.note_tab, text="  文本笔记  ")
        self.notebook.add(self.ebook_tab, text="  PDF电子书  ")
        self.notebook.pack(fill=tk.BOTH, expand=True)

    def refresh(self) -> None:
        current = self.notebook.select()
        tab = self.notebook.nametowidget(current)
        if hasattr(tab, "refresh"):
            tab.refresh()

    def highlight_item(self, item_id: str, item_type: str = "note") -> None:
        """定位并高亮指定条目（支持 note/ebook 子类型）。"""
        if item_type == "ebook":
            self.notebook.select(self.ebook_tab)
            self.ebook_tab.highlight_item(item_id)
        else:
            self.notebook.select(self.note_tab)
            self.note_tab.highlight_item(item_id)


# ============================================================
#  NoteTabView — 文本笔记
# ============================================================

class NoteTabView(tk.Frame):
    """文本笔记子视图，左右分栏布局。"""

    def __init__(self, parent: tk.Widget, manager: KnowledgeManager, set_status):
        super().__init__(parent, bg="#ffffff")
        self.manager = manager
        self.set_status = set_status
        self.current_note: KnowledgeItem | None = None

        self._build_toolbar()

        # 左右分栏
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=4)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=4)

        # 左侧：笔记列表
        left = tk.Frame(paned, bg="#ffffff")
        paned.add(left, width=320, minsize=200)

        self._build_note_list(left)

        # 右侧：详情编辑面板
        right = tk.Frame(paned, bg="#ffffff")
        paned.add(right, width=500, minsize=300)

        self._build_detail_panel(right)

        # 类别分布图
        self.note_bar_chart = BarChart(self, height=150, title="")
        self.note_bar_chart.pack(fill=tk.X, padx=12, pady=(4, 0))

        # 底部统计
        self._build_stats_bar()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self, bg="#fafafa", pady=6)
        toolbar.pack(fill=tk.X, padx=12, pady=(12, 0))

        self.search_bar = SearchBar(toolbar, on_search=self._on_search)
        self.search_bar.pack(side=tk.LEFT, padx=4)

        tk.Label(toolbar, text="类别：", bg="#fafafa",
                 font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(8, 2))

        self.category_filter = ttk.Combobox(
            toolbar, state="readonly", width=8,
            font=("Microsoft YaHei", 9)
        )
        self.category_filter.pack(side=tk.LEFT, padx=4)
        self.category_filter.bind("<<ComboboxSelected>>", lambda e: self._on_filter())

        add_btn = tk.Button(
            toolbar, text="+ 新建笔记", command=self._open_create_dialog,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        add_btn.pack(side=tk.RIGHT, padx=4)

    # ---- 左侧笔记列表 ----

    def _build_note_list(self, parent: tk.Frame) -> None:
        columns = ("title", "category", "keywords", "updated")
        self.note_tree = ttk.Treeview(parent, columns=columns, show="headings",
                                      selectmode="browse")

        self.note_tree.heading("title", text="标题")
        self.note_tree.heading("category", text="类别")
        self.note_tree.heading("keywords", text="关键词")
        self.note_tree.heading("updated", text="更新时间")

        self.note_tree.column("title", width=120)
        self.note_tree.column("category", width=50, anchor=tk.CENTER)
        self.note_tree.column("keywords", width=80)
        self.note_tree.column("updated", width=80, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL,
                                  command=self.note_tree.yview)
        self.note_tree.configure(yscrollcommand=scrollbar.set)

        self.note_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.note_tree.bind("<<TreeviewSelect>>", self._on_select_note)

    # ---- 右侧详情面板 ----

    def _build_detail_panel(self, parent: tk.Frame) -> None:
        form = tk.Frame(parent, bg="#ffffff", padx=12, pady=8)
        form.pack(fill=tk.BOTH, expand=True)

        # 标题
        tk.Label(form, text="标题：", bg="#ffffff",
                 font=("Microsoft YaHei", 10, "bold")).pack(anchor=tk.W)
        self.title_entry = tk.Entry(form, font=("Microsoft YaHei", 11))
        self.title_entry.pack(fill=tk.X, pady=(2, 8))

        # 类别
        row1 = tk.Frame(form, bg="#ffffff")
        row1.pack(fill=tk.X, pady=(0, 8))
        tk.Label(row1, text="类别：", bg="#ffffff",
                 font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)
        self.category_combo = ttk.Combobox(
            row1, values=self.manager.VALID_CATEGORIES,
            state="readonly", font=("Microsoft YaHei", 9), width=10
        )
        self.category_combo.pack(side=tk.LEFT, padx=8)

        # 关键词
        tk.Label(form, text="关键词：", bg="#ffffff",
                 font=("Microsoft YaHei", 9)).pack(anchor=tk.W)
        self.keyword_entry = KeywordEntry(form)
        self.keyword_entry.pack(fill=tk.X, pady=(2, 8))

        # 内容
        tk.Label(form, text="内容：", bg="#ffffff",
                 font=("Microsoft YaHei", 9)).pack(anchor=tk.W)
        self.content_text = tk.Text(form, font=("Microsoft YaHei", 10),
                                    wrap=tk.WORD, undo=True)
        self.content_text.pack(fill=tk.BOTH, expand=True, pady=(2, 8))

        # 操作按钮
        btn_row = tk.Frame(form, bg="#ffffff")
        btn_row.pack(fill=tk.X)

        self.save_btn = tk.Button(
            btn_row, text="保存修改", command=self._save_current_note,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        self.save_btn.pack(side=tk.LEFT, padx=(0, 8))

        self.delete_btn = tk.Button(
            btn_row, text="删除笔记", command=self._confirm_delete,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        self.delete_btn.pack(side=tk.LEFT)

        self._toggle_detail_editing(False)

    def _toggle_detail_editing(self, enabled: bool) -> None:
        state = tk.NORMAL if enabled else tk.DISABLED
        self.title_entry.configure(state=state)
        self.category_combo.configure(state="readonly" if enabled else tk.DISABLED)
        self.content_text.configure(state=state)
        self.keyword_entry.entry.configure(state=state)
        if enabled:
            self.save_btn.configure(state=tk.NORMAL)
            self.delete_btn.configure(state=tk.NORMAL)
        else:
            self.save_btn.configure(state=tk.DISABLED)
            self.delete_btn.configure(state=tk.DISABLED)

    # ---- 底部统计 ----

    def _build_stats_bar(self) -> None:
        self.stats_var = tk.StringVar()
        stats = tk.Label(
            self, textvariable=self.stats_var, bg="#f5f5f5",
            font=("Microsoft YaHei", 9), fg="#666666", pady=4
        )
        stats.pack(fill=tk.X, side=tk.BOTTOM)

    # ---- 选择笔记 ----

    def _on_select_note(self, event) -> None:
        selection = self.note_tree.selection()
        if not selection:
            return
        note_id = selection[0]
        note = self.manager.get_by_id(note_id)
        if note:
            self._display_note(note)

    def _display_note(self, note: KnowledgeItem) -> None:
        self.current_note = note
        self._toggle_detail_editing(True)

        self.title_entry.delete(0, tk.END)
        self.title_entry.insert(0, note.title)

        if note.category in self.manager.VALID_CATEGORIES:
            self.category_combo.set(note.category)
        else:
            self.category_combo.set("")

        self.keyword_entry.set_keywords(note.keywords)

        self.content_text.delete("1.0", tk.END)
        self.content_text.insert("1.0", note.content)

    # ---- 新建 ----

    def _open_create_dialog(self) -> None:
        fields = [
            {"name": "title", "label": "标题", "type": "text", "required": True},
            {"name": "category", "label": "类别", "type": "combobox",
             "options": self.manager.VALID_CATEGORIES},
            {"name": "content", "label": "内容", "type": "textarea"},
        ]
        FormDialog(self, "新建笔记", fields, on_save=self._do_create)

    def _do_create(self, data: dict) -> None:
        try:
            note = self.manager.create_note(
                title=data["title"],
                category=data.get("category", ""),
                keywords=[],
                content=data.get("content", "")
            )
            self.refresh()
            self.set_status(f"笔记「{note.title}」已创建")
        except Exception as e:
            messagebox.showerror("创建失败", str(e))

    # ---- 保存 ----

    def _save_current_note(self) -> None:
        if not self.current_note:
            return
        try:
            self.manager.update_note(
                self.current_note.id,
                title=self.title_entry.get().strip(),
                category=self.category_combo.get(),
                keywords=self.keyword_entry.get_keywords(),
                content=self.content_text.get("1.0", tk.END).strip()
            )
            self.current_note = self.manager.get_by_id(self.current_note.id)
            self.set_status(f"笔记「{self.current_note.title}」已保存")
            self._refresh_note_list()
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

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
            self.set_status("笔记已删除")

    def _clear_detail(self) -> None:
        self._toggle_detail_editing(False)
        self.title_entry.delete(0, tk.END)
        self.content_text.delete("1.0", tk.END)
        self.keyword_entry.set_keywords([])

    # ---- 搜索和筛选 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self._refresh_note_list()
            return
        results = self.manager.search(keyword)
        results = [r for r in results if r.item_type == "note"]
        self._populate_note_tree(results)

    def _on_filter(self) -> None:
        category = self.category_filter.get()
        if not category or category == "全部":
            self._refresh_note_list()
            return
        results = self.manager.get_by_category(category, item_type="note")
        self._populate_note_tree(results)

    # ---- 数据刷新 ----

    def refresh(self) -> None:
        self._refresh_note_list()
        self._update_stats()

    def _refresh_note_list(self) -> None:
        notes = self.manager.get_all(item_type="note")
        self._populate_note_tree(notes)

        # 更新类别筛选
        categories = self.manager.get_all_categories(item_type="note")
        self.category_filter["values"] = ["全部"] + categories
        if not self.category_filter.get():
            self.category_filter.set("全部")

    def _populate_note_tree(self, notes: list[KnowledgeItem]) -> None:
        for item in self.note_tree.get_children():
            self.note_tree.delete(item)
        for n in notes:
            self.note_tree.insert("", tk.END, iid=n.id, values=(
                n.title,
                n.category,
                _format_keywords(n.keywords),
                n.updated_at[:10] if n.updated_at else n.created_at[:10],
            ))

    def highlight_item(self, item_id: str) -> None:
        """定位并高亮指定笔记条目。"""
        if not self.note_tree.exists(item_id):
            return
        self.note_tree.selection_set(item_id)
        self.note_tree.see(item_id)
        self.note_tree.focus(item_id)

    def _update_stats(self) -> None:
        stats = self.manager.get_statistics()
        cats = ", ".join(f"{k}:{v}" for k, v in stats["by_category"].items())
        self.stats_var.set(
            f"共 {stats['total_notes']} 篇笔记"
            + (f"  |  {cats}" if cats else "")
        )

        # 更新类别柱状图（仅笔记）
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


# ============================================================
#  EbookTabView — PDF 电子书
# ============================================================

class EbookTabView(tk.Frame):
    """PDF 电子书子视图。"""

    def __init__(self, parent: tk.Widget, manager: KnowledgeManager, set_status):
        super().__init__(parent, bg="#ffffff")
        self.manager = manager
        self.set_status = set_status

        self._build_toolbar()
        self._build_table()
        self._build_context_menu()
        self._build_stats_bar()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self, bg="#fafafa", pady=6)
        toolbar.pack(fill=tk.X, padx=12, pady=(12, 0))

        self.search_bar = SearchBar(toolbar, on_search=self._on_search)
        self.search_bar.pack(side=tk.LEFT, padx=4)

        tk.Label(toolbar, text="类别：", bg="#fafafa",
                 font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(8, 2))

        self.category_filter = ttk.Combobox(
            toolbar, state="readonly", width=8,
            font=("Microsoft YaHei", 9)
        )
        self.category_filter.pack(side=tk.LEFT, padx=4)
        self.category_filter.bind("<<ComboboxSelected>>", lambda e: self._on_filter())

        import_btn = tk.Button(
            toolbar, text="+ 导入电子书", command=self._open_import_dialog,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        import_btn.pack(side=tk.RIGHT, padx=4)

    # ---- 表格 ----

    def _build_table(self) -> None:
        columns = ("title", "category", "keywords", "size", "created")
        self.tree = ttk.Treeview(self, columns=columns, show="headings",
                                 selectmode="browse")

        self.tree.heading("title", text="书名")
        self.tree.heading("category", text="类别")
        self.tree.heading("keywords", text="关键词")
        self.tree.heading("size", text="大小")
        self.tree.heading("created", text="导入时间")

        self.tree.column("title", width=180)
        self.tree.column("category", width=60, anchor=tk.CENTER)
        self.tree.column("keywords", width=100)
        self.tree.column("size", width=70, anchor=tk.CENTER)
        self.tree.column("created", width=100, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 12), pady=8)

        self.tree.bind("<Double-1>", lambda e: self._open_ebook())

    # ---- 右键菜单 ----

    def _build_context_menu(self) -> None:
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="打开阅读", command=self._open_ebook)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="编辑信息", command=self._open_edit_dialog)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="删除", command=self._confirm_delete)

        self.tree.bind("<Button-3>", self._show_context_menu)

    def _show_context_menu(self, event) -> None:
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)

    # ---- 底部统计 ----

    def _build_stats_bar(self) -> None:
        self.stats_var = tk.StringVar()
        stats = tk.Label(
            self, textvariable=self.stats_var, bg="#f5f5f5",
            font=("Microsoft YaHei", 9), fg="#666666", pady=4
        )
        stats.pack(fill=tk.X, side=tk.BOTTOM)

    # ---- 导入 ----

    def _open_import_dialog(self) -> None:
        EbookImportDialog(self, self.manager, on_done=self.refresh)

    # ---- 打开 ----

    def _open_ebook(self) -> None:
        item = self._get_selected()
        if not item:
            return
        try:
            self.manager.open_ebook(item.id)
            self.set_status(f"正在打开「{item.title}」...")
        except Exception as e:
            messagebox.showerror("打开失败", str(e))

    # ---- 编辑信息 ----

    def _open_edit_dialog(self) -> None:
        item = self._get_selected()
        if not item:
            return

        categories = self.manager.get_all_categories(item_type="ebook") or self.manager.VALID_CATEGORIES
        dialog = EbookEditDialog(self, item, categories, on_save=lambda d: self._do_edit(item.id, d))

    def _do_edit(self, ebook_id: str, data: dict) -> None:
        try:
            self.manager.update_ebook_info(
                ebook_id, title=data["title"],
                category=data["category"], keywords=data["keywords"]
            )
            self.refresh()
            self.set_status(f"电子书「{data['title']}」信息已更新")
        except Exception as e:
            messagebox.showerror("编辑失败", str(e))

    # ---- 删除 ----

    def _confirm_delete(self) -> None:
        item = self._get_selected()
        if not item:
            return

        result = messagebox.askyesnocancel(
            "确认删除",
            f"确定要删除电子书「{item.title}」吗？\n\n"
            f"选「是」同时删除 PDF 文件\n"
            f"选「否」仅删除记录，保留文件"
        )
        if result is None:
            return  # 取消
        delete_file = result  # True=是, False=否
        self.manager.delete_item(item.id, delete_file=delete_file)
        self.refresh()
        self.set_status(f"电子书「{item.title}」已删除")

    # ---- 搜索筛选 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self.refresh()
            return
        results = self.manager.search(keyword)
        results = [r for r in results if r.item_type == "ebook"]
        self._populate_tree(results)

    def _on_filter(self) -> None:
        category = self.category_filter.get()
        if not category or category == "全部":
            self.refresh()
            return
        results = self.manager.get_by_category(category, item_type="ebook")
        self._populate_tree(results)

    # ---- 数据刷新 ----

    def refresh(self) -> None:
        ebooks = self.manager.get_all(item_type="ebook")
        self._populate_tree(ebooks)

        categories = self.manager.get_all_categories(item_type="ebook")
        self.category_filter["values"] = ["全部"] + categories
        if not self.category_filter.get():
            self.category_filter.set("全部")

        stats = self.manager.get_statistics()
        self.stats_var.set(f"共 {stats['total_ebooks']} 本电子书")

    def _populate_tree(self, ebooks: list[KnowledgeItem]) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        for eb in ebooks:
            self.tree.insert("", tk.END, iid=eb.id, values=(
                eb.title,
                eb.category,
                _format_keywords(eb.keywords),
                _format_size(eb.file_size),
                eb.created_at[:10] if eb.created_at else "-",
            ))

    def _get_selected(self) -> KnowledgeItem | None:
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选中一本电子书")
            return None
        return self.manager.get_by_id(selection[0])

    def highlight_item(self, item_id: str) -> None:
        """定位并高亮指定电子书条目。"""
        if not self.tree.exists(item_id):
            return
        self.tree.selection_set(item_id)
        self.tree.see(item_id)
        self.tree.focus(item_id)


# ============================================================
#  EbookImportDialog — 导入电子书
# ============================================================

class EbookImportDialog(tk.Toplevel):
    """PDF 电子书导入对话框。"""

    def __init__(self, parent: tk.Widget, manager: KnowledgeManager,
                 on_done):
        super().__init__(parent)
        self.title("导入 PDF 电子书")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.manager = manager
        self.on_done = on_done
        self.source_path: str = ""

        self._build()

    def _build(self) -> None:
        form = tk.Frame(self, padx=20, pady=12)
        form.pack(fill=tk.BOTH, expand=True)

        # PDF 文件选择
        tk.Label(form, text="PDF 文件：", font=("Microsoft YaHei", 10),
                 anchor=tk.E, width=10).grid(row=0, column=0, sticky=tk.E, padx=(0, 8), pady=4)

        file_row = tk.Frame(form)
        file_row.grid(row=0, column=1, sticky=tk.EW, pady=4)

        self.file_var = tk.StringVar(value="未选择文件")
        file_label = tk.Label(file_row, textvariable=self.file_var,
                             font=("Microsoft YaHei", 9), fg="#999999")
        file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        browse_btn = tk.Button(
            file_row, text="浏览...", command=self._browse_file,
            font=("Microsoft YaHei", 9), cursor="hand2"
        )
        browse_btn.pack(side=tk.RIGHT)

        # 文件大小
        self.size_var = tk.StringVar(value="")
        size_label = tk.Label(form, textvariable=self.size_var,
                             font=("Microsoft YaHei", 9), fg="#666666")
        size_label.grid(row=1, column=1, sticky=tk.W, pady=(0, 8))

        # 书名
        tk.Label(form, text="书名：", font=("Microsoft YaHei", 10),
                 anchor=tk.E, width=10).grid(row=2, column=0, sticky=tk.E, padx=(0, 8), pady=4)
        self.title_entry = tk.Entry(form, font=("Microsoft YaHei", 10))
        self.title_entry.grid(row=2, column=1, sticky=tk.EW, pady=4)

        # 类别
        tk.Label(form, text="类别：", font=("Microsoft YaHei", 10),
                 anchor=tk.E, width=10).grid(row=3, column=0, sticky=tk.E, padx=(0, 8), pady=4)
        self.category_combo = ttk.Combobox(
            form, values=self.manager.VALID_CATEGORIES,
            state="readonly", font=("Microsoft YaHei", 10)
        )
        self.category_combo.grid(row=3, column=1, sticky=tk.EW, pady=4)
        self.category_combo.set("技术")

        # 关键词
        tk.Label(form, text="关键词：", font=("Microsoft YaHei", 10),
                 anchor=tk.E, width=10).grid(row=4, column=0, sticky=tk.NE, padx=(0, 8), pady=4)
        self.keyword_entry = KeywordEntry(form)
        self.keyword_entry.grid(row=4, column=1, sticky=tk.EW, pady=4)

        form.columnconfigure(1, weight=1)

        # 按钮
        btn_frame = tk.Frame(self, pady=10)
        btn_frame.pack(fill=tk.X)

        cancel_btn = tk.Button(btn_frame, text="取消", command=self.destroy,
                               font=("Microsoft YaHei", 9), padx=16, cursor="hand2")
        cancel_btn.pack(side=tk.RIGHT, padx=8)

        import_btn = tk.Button(btn_frame, text="导入", command=self._do_import,
                               font=("Microsoft YaHei", 9), padx=16, cursor="hand2")
        import_btn.pack(side=tk.RIGHT)

    def _browse_file(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("PDF 文件", "*.pdf"), ("所有文件", "*.*")]
        )
        if path:
            self.source_path = path
            basename = os.path.basename(path)
            self.file_var.set(basename if len(basename) < 50 else basename[:47] + "...")

            size = os.path.getsize(path)
            self.size_var.set(f"文件大小：{_format_size(size)}")

            # 自动填充书名
            name = os.path.splitext(basename)[0]
            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, name)

    def _do_import(self) -> None:
        if not self.source_path:
            messagebox.showwarning("提示", "请先选择 PDF 文件")
            return
        try:
            self.manager.import_ebook(
                source_path=self.source_path,
                title=self.title_entry.get().strip(),
                category=self.category_combo.get(),
                keywords=self.keyword_entry.get_keywords()
            )
            self.on_done()
            self.destroy()
        except Exception as e:
            messagebox.showerror("导入失败", str(e))


# ============================================================
#  EbookEditDialog — 编辑电子书信息
# ============================================================

class EbookEditDialog(tk.Toplevel):
    """编辑电子书元数据对话框。"""

    def __init__(self, parent: tk.Widget, item: KnowledgeItem,
                 categories: list[str], on_save):
        super().__init__(parent)
        self.title("编辑电子书信息")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.on_save = on_save

        form = tk.Frame(self, padx=20, pady=12)
        form.pack(fill=tk.BOTH, expand=True)

        # 书名
        tk.Label(form, text="书名：", font=("Microsoft YaHei", 10),
                 anchor=tk.E, width=10).grid(row=0, column=0, sticky=tk.E, padx=(0, 8), pady=4)
        title_entry = tk.Entry(form, font=("Microsoft YaHei", 10))
        title_entry.insert(0, item.title)
        title_entry.grid(row=0, column=1, sticky=tk.EW, pady=4)

        # 类别
        tk.Label(form, text="类别：", font=("Microsoft YaHei", 10),
                 anchor=tk.E, width=10).grid(row=1, column=0, sticky=tk.E, padx=(0, 8), pady=4)
        cat_combo = ttk.Combobox(form, values=categories, state="readonly",
                                 font=("Microsoft YaHei", 10))
        cat_combo.set(item.category)
        cat_combo.grid(row=1, column=1, sticky=tk.EW, pady=4)

        # 关键词
        tk.Label(form, text="关键词：", font=("Microsoft YaHei", 10),
                 anchor=tk.E, width=10).grid(row=2, column=0, sticky=tk.NE, padx=(0, 8), pady=4)
        kw_entry = KeywordEntry(form)
        kw_entry.set_keywords(item.keywords)
        kw_entry.grid(row=2, column=1, sticky=tk.EW, pady=4)

        form.columnconfigure(1, weight=1)

        # 按钮
        btn_frame = tk.Frame(self, pady=10)
        btn_frame.pack(fill=tk.X)

        def save():
            self.on_save({
                "title": title_entry.get().strip(),
                "category": cat_combo.get(),
                "keywords": kw_entry.get_keywords(),
            })
            self.destroy()

        cancel_btn = tk.Button(btn_frame, text="取消", command=self.destroy,
                               font=("Microsoft YaHei", 9), padx=16, cursor="hand2")
        cancel_btn.pack(side=tk.RIGHT, padx=8)

        save_btn = tk.Button(btn_frame, text="保存", command=save,
                             font=("Microsoft YaHei", 9), padx=16, cursor="hand2")
        save_btn.pack(side=tk.RIGHT)
