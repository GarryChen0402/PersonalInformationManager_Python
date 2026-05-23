"""可复用的 Tkinter 通用组件。"""

import csv
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable


# ---- SearchBar ----

class SearchBar(tk.Frame):
    """搜索框组件：输入框 + 搜索按钮。"""

    def __init__(self, parent: tk.Widget, on_search: Callable[[str], None],
                 placeholder: str = "输入关键词搜索..."):
        super().__init__(parent)
        self.on_search = on_search

        self.entry = tk.Entry(self, font=("Microsoft YaHei", 10), width=20)
        self.entry.pack(side=tk.LEFT, padx=(0, 4))
        self.entry.insert(0, placeholder)
        self.entry.bind("<FocusIn>", self._clear_placeholder)
        self.entry.bind("<Return>", lambda e: self._do_search())

        self.btn = tk.Button(
            self, text="搜索", command=self._do_search,
            font=("Microsoft YaHei", 9), padx=8, cursor="hand2"
        )
        self.btn.pack(side=tk.LEFT)

        self._placeholder = placeholder

    def _clear_placeholder(self, event) -> None:
        if self.entry.get() == self._placeholder:
            self.entry.delete(0, tk.END)

    def _do_search(self) -> None:
        keyword = self.entry.get().strip()
        if keyword == self._placeholder:
            keyword = ""
        self.on_search(keyword)

    def get(self) -> str:
        val = self.entry.get().strip()
        return "" if val == self._placeholder else val


# ---- FormDialog ----

class FormDialog(tk.Toplevel):
    """通用表单弹窗。

    fields 格式: [{"name": "title", "label": "技能名称", "type": "text", "required": True}, ...]
    支持 type: "text", "combobox" (需 options), "textarea", "spinbox" (需 from_/to_)
    """

    def __init__(self, parent: tk.Widget, title: str, fields: list[dict],
                 on_save: Callable[[dict], None], initial_data: dict | None = None):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.fields = fields
        self.on_save = on_save
        self.initial_data = initial_data or {}
        self.result = None
        self.widgets: dict[str, tk.Widget] = {}

        self._build()

    def _build(self) -> None:
        form = tk.Frame(self, padx=20, pady=12)
        form.pack(fill=tk.BOTH, expand=True)

        for i, field in enumerate(self.fields):
            name = field["name"]
            label_text = field.get("label", name)
            kind = field.get("type", "text")

            lbl = tk.Label(form, text=f"{label_text}：",
                           font=("Microsoft YaHei", 10), anchor=tk.E, width=10)
            lbl.grid(row=i, column=0, sticky=tk.NE, padx=(0, 8), pady=4)

            if kind == "combobox":
                options = field.get("options", [])
                widget = ttk.Combobox(form, values=options, state="readonly",
                                      font=("Microsoft YaHei", 10))
                if name in self.initial_data:
                    widget.set(self.initial_data[name])
                widget.grid(row=i, column=1, sticky=tk.EW, pady=4, ipadx=4)

            elif kind == "textarea":
                widget = tk.Text(form, height=3, font=("Microsoft YaHei", 10),
                                 wrap=tk.WORD)
                if name in self.initial_data:
                    widget.insert("1.0", self.initial_data[name])
                widget.grid(row=i, column=1, sticky=tk.EW, pady=4)

            elif kind == "spinbox":
                from_val = field.get("from_", 1)
                to_val = field.get("to", 5)
                widget = tk.Spinbox(form, from_=from_val, to=to_val,
                                    font=("Microsoft YaHei", 10), width=8)
                if name in self.initial_data:
                    widget.delete(0, tk.END)
                    widget.insert(0, str(self.initial_data[name]))
                widget.grid(row=i, column=1, sticky=tk.W, pady=4)

            else:  # "text" 或其他默认
                widget = tk.Entry(form, font=("Microsoft YaHei", 10))
                show = field.get("show", "")
                if show:
                    widget.configure(show=show)
                if name in self.initial_data:
                    widget.insert(0, str(self.initial_data[name]))
                widget.grid(row=i, column=1, sticky=tk.EW, pady=4)

            self.widgets[name] = widget

        form.columnconfigure(1, weight=1)

        # 按钮
        btn_frame = tk.Frame(self, pady=10)
        btn_frame.pack(fill=tk.X)

        cancel_btn = tk.Button(btn_frame, text="取消", command=self.destroy,
                               font=("Microsoft YaHei", 9), padx=16, cursor="hand2")
        cancel_btn.pack(side=tk.RIGHT, padx=8)

        save_btn = tk.Button(btn_frame, text="保存", command=self._collect_and_save,
                             font=("Microsoft YaHei", 9), padx=16, cursor="hand2")
        save_btn.pack(side=tk.RIGHT)

    def _collect_and_save(self) -> None:
        """收集表单数据，校验必填字段，调用 on_save。"""
        data = {}
        for field in self.fields:
            name = field["name"]
            kind = field.get("type", "text")
            widget = self.widgets[name]

            if kind == "textarea":
                value = widget.get("1.0", tk.END).strip()
            elif kind == "spinbox":
                try:
                    value = float(widget.get()) if "." in widget.get() else int(widget.get())
                except ValueError:
                    value = widget.get()
            else:
                value = widget.get().strip()

            # 必填校验
            if field.get("required") and not value and kind not in ("spinbox",):
                messagebox.showwarning("输入校验", f"请填写「{field['label']}」")
                return

            data[name] = value

        self.on_save(data)
        self.destroy()


# ---- ConfirmDialog ----

class ConfirmDialog:
    """确认弹窗封装。"""

    @staticmethod
    def show(parent: tk.Widget, title: str, message: str) -> bool:
        return messagebox.askyesno(title, message, parent=parent)


# ---- DateRangePicker ----

class DateRangePicker(tk.Frame):
    """日期范围选择组件：开始日期 + 结束日期 + 查询按钮。"""

    def __init__(self, parent: tk.Widget, on_query: Callable[[str, str], None]):
        super().__init__(parent)
        self.on_query = on_query

        tk.Label(self, text="从：", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT)

        self.start_entry = tk.Entry(self, font=("Microsoft YaHei", 10), width=10)
        self.start_entry.pack(side=tk.LEFT, padx=2)
        self.start_entry.bind("<Return>", lambda e: self._do_query())

        tk.Label(self, text="到：", font=("Microsoft YaHei", 9)).pack(side=tk.LEFT, padx=(6, 0))

        self.end_entry = tk.Entry(self, font=("Microsoft YaHei", 10), width=10)
        self.end_entry.pack(side=tk.LEFT, padx=2)
        self.end_entry.bind("<Return>", lambda e: self._do_query())

        query_btn = tk.Button(
            self, text="查询", command=self._do_query,
            font=("Microsoft YaHei", 9), padx=8, cursor="hand2"
        )
        query_btn.pack(side=tk.LEFT, padx=6)

        # 快捷按钮
        today_btn = tk.Button(
            self, text="最近7天", command=self._set_last_week,
            font=("Microsoft YaHei", 8), padx=4
        )
        today_btn.pack(side=tk.LEFT, padx=2)

        month_btn = tk.Button(
            self, text="最近30天", command=self._set_last_month,
            font=("Microsoft YaHei", 8), padx=4
        )
        month_btn.pack(side=tk.LEFT, padx=2)

    def _do_query(self) -> None:
        start = self.start_entry.get().strip()
        end = self.end_entry.get().strip()
        if start and end:
            self.on_query(start, end)

    def _set_last_week(self) -> None:
        from datetime import datetime, timedelta
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        self.set_range(start, end)
        self._do_query()

    def _set_last_month(self) -> None:
        from datetime import datetime, timedelta
        end = datetime.now().strftime("%Y-%m-%d")
        start = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        self.set_range(start, end)
        self._do_query()

    def set_range(self, start: str, end: str) -> None:
        self.start_entry.delete(0, tk.END)
        self.start_entry.insert(0, start)
        self.end_entry.delete(0, tk.END)
        self.end_entry.insert(0, end)


# ---- StatsBar ----

class StatsBar(tk.Frame):
    """统计栏组件，水平排列多组统计标签。"""

    def __init__(self, parent: tk.Widget, items: list[tuple[str, str]] | None = None):
        super().__init__(parent, bg="#f5f5f5")
        self.labels: list[tk.Label] = []
        self.items = items or []

        for i, (name, value) in enumerate(self.items):
            lbl = tk.Label(
                self, text=f"{name}: {value}", bg="#f5f5f5",
                font=("Microsoft YaHei", 9), fg="#666666", padx=12, pady=4
            )
            lbl.pack(side=tk.LEFT)
            self.labels.append(lbl)

    def update(self, items: list[tuple[str, str]]) -> None:
        """更新统计项。"""
        self.items = items
        # 移除旧标签
        for lbl in self.labels:
            lbl.destroy()
        self.labels.clear()
        # 创建新标签
        for name, value in items:
            lbl = tk.Label(
                self, text=f"{name}: {value}", bg="#f5f5f5",
                font=("Microsoft YaHei", 9), fg="#666666", padx=12, pady=4
            )
            lbl.pack(side=tk.LEFT)
            self.labels.append(lbl)


# ---- KeywordEntry ----

class KeywordEntry(tk.Frame):
    """关键词标签式输入组件。"""

    def __init__(self, parent: tk.Widget):
        super().__init__(parent)
        self._keywords: list[str] = []

        input_row = tk.Frame(self)
        input_row.pack(fill=tk.X)

        self.entry = tk.Entry(input_row, font=("Microsoft YaHei", 10))
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        self.entry.bind("<Return>", lambda e: self._add_keyword())

        add_btn = tk.Button(
            input_row, text="+", command=self._add_keyword,
            font=("Microsoft YaHei", 9), padx=6, cursor="hand2"
        )
        add_btn.pack(side=tk.LEFT)

        self.tags_frame = tk.Frame(self)
        self.tags_frame.pack(fill=tk.X, pady=(4, 0))

    def _add_keyword(self) -> None:
        kw = self.entry.get().strip()
        if kw and kw not in self._keywords:
            self._keywords.append(kw)
            self._render_tags()
        self.entry.delete(0, tk.END)

    def _remove_keyword(self, kw: str) -> None:
        if kw in self._keywords:
            self._keywords.remove(kw)
            self._render_tags()

    def _render_tags(self) -> None:
        for w in self.tags_frame.winfo_children():
            w.destroy()
        for kw in self._keywords:
            tag = tk.Frame(self.tags_frame, bg="#e0e8f0", padx=2)
            tag.pack(side=tk.LEFT, padx=2, pady=2)

            lbl = tk.Label(tag, text=kw, bg="#e0e8f0",
                          font=("Microsoft YaHei", 9))
            lbl.pack(side=tk.LEFT)

            close = tk.Label(tag, text=" x", bg="#e0e8f0", fg="#999999",
                            font=("Microsoft YaHei", 9), cursor="hand2")
            close.pack(side=tk.LEFT)
            close.bind("<Button-1>", lambda e, k=kw: self._remove_keyword(k))

    def get_keywords(self) -> list[str]:
        return list(self._keywords)

    def set_keywords(self, keywords: list[str]) -> None:
        self._keywords = list(keywords)
        self._render_tags()


# ---- CalendarNav ----

class CalendarNav(tk.Frame):
    """月历导航组件，支持日期标记和选择回调。"""

    WEEKDAY_HEADERS_CN = ["一", "二", "三", "四", "五", "六", "日"]

    def __init__(self, parent: tk.Widget, on_date_select: Callable[[str], None],
                 marked_dates: set[str] | None = None):
        super().__init__(parent)
        self.on_date_select = on_date_select
        self.marked_dates = marked_dates or set()
        self.selected_date: str | None = None
        self._current_year: int = 0
        self._current_month: int = 0
        self._day_buttons: list[tk.Label] = []

        self._build()

        from datetime import datetime
        now = datetime.now()
        self.goto_date(now.year, now.month)

    def _build(self) -> None:
        # 顶部：月份切换
        header = tk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 4))

        self._prev_btn = tk.Button(
            header, text="◀", command=self._prev_month,
            font=("Microsoft YaHei", 9), padx=6, cursor="hand2", relief=tk.FLAT
        )
        self._prev_btn.pack(side=tk.LEFT)

        self._month_label = tk.Label(
            header, text="", font=("Microsoft YaHei", 10, "bold"), width=12
        )
        self._month_label.pack(side=tk.LEFT, expand=True)

        self._next_btn = tk.Button(
            header, text="▶", command=self._next_month,
            font=("Microsoft YaHei", 9), padx=6, cursor="hand2", relief=tk.FLAT
        )
        self._next_btn.pack(side=tk.RIGHT)

        # 星期标题
        week_header = tk.Frame(self)
        week_header.pack(fill=tk.X)
        for day_name in self.WEEKDAY_HEADERS_CN:
            lbl = tk.Label(
                week_header, text=day_name, font=("Microsoft YaHei", 8),
                fg="#888888", width=3
            )
            lbl.pack(side=tk.LEFT, expand=True)

        # 日期网格
        self._grid_frame = tk.Frame(self)
        self._grid_frame.pack(fill=tk.BOTH, expand=True)

    def _render_grid(self) -> None:
        for btn in self._day_buttons:
            btn.destroy()
        self._day_buttons.clear()

        from datetime import datetime, date, timedelta
        first_day = date(self._current_year, self._current_month, 1)
        # 周一为 0
        start_weekday = first_day.weekday()

        # 计算当月天数
        if self._current_month == 12:
            next_month = date(self._current_year + 1, 1, 1)
        else:
            next_month = date(self._current_year, self._current_month + 1, 1)
        days_in_month = (next_month - first_day).days

        # 计算需要显示的总格数（从周一开始）
        today = date.today()

        for i in range(42):  # 最多 6 行 × 7 列
            day_num = i - start_weekday + 1
            col = i % 7
            row = i // 7

            if 1 <= day_num <= days_in_month:
                cell_date = date(self._current_year, self._current_month, day_num)
                date_str = cell_date.isoformat()
                text = str(day_num)

                # 颜色逻辑
                is_today = cell_date == today
                is_marked = date_str in self.marked_dates
                is_selected = date_str == self.selected_date

                bg = "#ffffff"
                fg = "#333333"
                font_style = ("Microsoft YaHei", 9)

                if is_selected:
                    bg = "#4a90d9"
                    fg = "#ffffff"
                elif is_today:
                    bg = "#e8f4fd"
                    fg = "#4a90d9"
                    font_style = ("Microsoft YaHei", 9, "bold")

                btn = tk.Label(
                    self._grid_frame, text=text, font=font_style,
                    bg=bg, fg=fg, width=3, padx=4, pady=2,
                    cursor="hand2", relief=tk.FLAT
                )
                btn.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
                btn.bind("<Button-1>", lambda e, d=date_str: self.select_date(d))

                # 标记点
                if is_marked and not is_selected:
                    btn.configure(text=f"{day_num}\n●")
                    from tkinter import font as tkfont
                    btn.configure(font=("Microsoft YaHei", 7))

                self._day_buttons.append(btn)
            else:
                # 空白填充
                spacer = tk.Label(
                    self._grid_frame, text="", font=("Microsoft YaHei", 9),
                    bg="#f5f5f5", width=3
                )
                spacer.grid(row=row, column=col, padx=1, pady=1, sticky="nsew")
                self._day_buttons.append(spacer)

        for c in range(7):
            self._grid_frame.columnconfigure(c, weight=1)

    def select_date(self, date_str: str) -> None:
        """选中指定日期并触发回调。"""
        self.selected_date = date_str
        self._render_grid()
        self.on_date_select(date_str)

    def set_marked_dates(self, dates: set[str]) -> None:
        """更新有标记的日期集合。"""
        self.marked_dates = dates
        self._render_grid()

    def goto_date(self, year: int, month: int) -> None:
        """跳转到指定年月。"""
        self._current_year = year
        self._current_month = month
        self._month_label.configure(text=f"{year}年 {month}月")
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

class CSVPreviewDialog(tk.Toplevel):
    """CSV 导入预览对话框。"""

    def __init__(self, parent: tk.Widget, file_path: str,
                 on_confirm: Callable[[str], None]):
        super().__init__(parent)
        self.title("CSV 导入预览")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.file_path = file_path
        self.on_confirm = on_confirm

        self._build()

    def _build(self) -> None:
        frame = tk.Frame(self, padx=12, pady=12)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame, text=f"文件：{self.file_path}",
            font=("Microsoft YaHei", 9), fg="#666666", anchor=tk.W
        ).pack(fill=tk.X, pady=(0, 8))

        # 预览表格（前 5 行）
        columns: list[str] = []
        try:
            with open(self.file_path, "r", encoding="utf-8-sig") as f:
                reader = csv.reader(f)
                header = next(reader)
                columns = [h.strip() for h in header]
                preview_rows = [next(reader) for _ in range(5)]
        except (StopIteration, OSError):
            columns = ["(无法读取)"]
            preview_rows = []

        tree = ttk.Treeview(frame, columns=columns, show="headings", height=6)
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=max(60, 360 // len(columns)))

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        for row in preview_rows:
            tree.insert("", tk.END, values=row)

        # 总行数
        total = sum(1 for _ in open(self.file_path, "r", encoding="utf-8-sig")) - 1
        info = tk.Label(
            frame, text=f"共 {total} 行数据（预览前 {min(5, total)} 行）",
            font=("Microsoft YaHei", 9), fg="#666666"
        )
        info.pack(anchor=tk.W, pady=(8, 0))

        # 按钮
        btn_frame = tk.Frame(self, pady=10)
        btn_frame.pack(fill=tk.X)

        cancel_btn = tk.Button(
            btn_frame, text="取消", command=self.destroy,
            font=("Microsoft YaHei", 9), padx=16, cursor="hand2"
        )
        cancel_btn.pack(side=tk.RIGHT, padx=8)

        confirm_btn = tk.Button(
            btn_frame, text="确认导入", command=self._do_confirm,
            font=("Microsoft YaHei", 9), padx=16, cursor="hand2"
        )
        confirm_btn.pack(side=tk.RIGHT)

    def _do_confirm(self) -> None:
        self.on_confirm(self.file_path)
        self.destroy()
