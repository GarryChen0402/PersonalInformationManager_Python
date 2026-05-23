"""日记页面。"""

import tkinter as tk
from tkinter import messagebox, filedialog
from datetime import datetime

from .BasePage import BasePage
from .Widgets import CalendarNav, SearchBar
from Services.JournalManager import JournalManager
from Services.StatusManager import StatusManager
from Services.ConfigManager import ConfigManager


class JournalPage(BasePage):
    """日记页面：左侧日历导航 + 右侧编辑器。"""

    def __init__(self, parent: tk.Widget, set_status):
        super().__init__(parent, set_status)
        self.manager = JournalManager()
        self.status_manager = StatusManager()
        self.config_manager = ConfigManager()
        self._current_date: str | None = None

        self._build_toolbar()
        self._build_body()

        # 默认选中今天
        today = datetime.now().strftime("%Y-%m-%d")
        self.calendar.select_date(today)

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        toolbar = tk.Frame(self, bg="#fafafa", pady=6, padx=8)
        toolbar.pack(fill=tk.X)

        self.search_bar = SearchBar(
            toolbar, on_search=self._on_search, placeholder="搜索日记..."
        )
        self.search_bar.pack(side=tk.LEFT, padx=(0, 8))

        today_btn = tk.Button(
            toolbar, text="今天", command=self._go_today,
            font=("Microsoft YaHei", 9), padx=8, cursor="hand2"
        )
        today_btn.pack(side=tk.LEFT, padx=(0, 4))

        stats_btn = tk.Button(
            toolbar, text="统计", command=self._show_statistics,
            font=("Microsoft YaHei", 9), padx=8, cursor="hand2"
        )
        stats_btn.pack(side=tk.LEFT, padx=(0, 4))

        export_btn = tk.Button(
            toolbar, text="导出 Markdown", command=self._export_markdown,
            font=("Microsoft YaHei", 9), padx=8, cursor="hand2"
        )
        export_btn.pack(side=tk.LEFT)

        # 底部统计栏
        self._build_stats_bar()

    # ---- 主体：左右分栏 ----

    def _build_body(self) -> None:
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL, sashwidth=4, bg="#dddddd")
        paned.pack(fill=tk.BOTH, expand=True)

        # 左栏：日历
        left = tk.Frame(paned, bg="#ffffff", width=220)
        paned.add(left, minsize=200)

        self.calendar = CalendarNav(
            left, on_date_select=self._on_date_select
        )
        self.calendar.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # 右栏：编辑器
        right = tk.Frame(paned, bg="#ffffff")
        paned.add(right)

        # 标题
        title_frame = tk.Frame(right, bg="#ffffff")
        title_frame.pack(fill=tk.X, padx=12, pady=(12, 4))

        tk.Label(
            title_frame, text="标题：", font=("Microsoft YaHei", 10),
            bg="#ffffff"
        ).pack(side=tk.LEFT)

        self.title_var = tk.StringVar()
        self.title_entry = tk.Entry(
            title_frame, textvariable=self.title_var,
            font=("Microsoft YaHei", 11, "bold"), relief=tk.FLAT
        )
        self.title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))
        self.title_entry.bind("<KeyRelease>", lambda e: self._on_content_change())

        # 情绪关联
        self.mood_var = tk.StringVar()
        mood_label = tk.Label(
            right, textvariable=self.mood_var,
            font=("Microsoft YaHei", 9), fg="#888888", bg="#ffffff",
            anchor=tk.W, padx=12
        )
        mood_label.pack(fill=tk.X, pady=(0, 4))

        # 正文
        text_frame = tk.Frame(right, bg="#ffffff", padx=12, pady=4)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.text = tk.Text(
            text_frame, font=("Microsoft YaHei", 10),
            wrap=tk.WORD, relief=tk.FLAT,
            padx=8, pady=8, undo=True
        )
        self.text.pack(fill=tk.BOTH, expand=True)
        self.text.bind("<KeyRelease>", lambda e: self._on_content_change())

        # 底部操作栏
        bottom = tk.Frame(right, bg="#fafafa", pady=6, padx=12)
        bottom.pack(fill=tk.X)

        self.word_count_var = tk.StringVar(value="字数：0")
        tk.Label(
            bottom, textvariable=self.word_count_var,
            font=("Microsoft YaHei", 9), fg="#888888", bg="#fafafa"
        ).pack(side=tk.LEFT)

        save_btn = tk.Button(
            bottom, text="保存 (Ctrl+S)", command=self._save_current,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        save_btn.pack(side=tk.RIGHT, padx=(4, 0))

        del_btn = tk.Button(
            bottom, text="删除", command=self._delete_current,
            font=("Microsoft YaHei", 9), padx=8, cursor="hand2", fg="#cc0000"
        )
        del_btn.pack(side=tk.RIGHT, padx=4)

        # 绑定 Ctrl+S 保存
        self.text.bind("<Control-s>", lambda e: self._save_current())
        self.title_entry.bind("<Control-s>", lambda e: self._save_current())

    # ---- 事件 ----

    def _on_date_select(self, date_str: str) -> None:
        """切换日期前自动保存当前日记。"""
        self._auto_save()
        self._current_date = date_str
        self._load_entry(date_str)
        self._update_mood_display(date_str)

    def _load_entry(self, date_str: str) -> None:
        """加载指定日期的日记内容。"""
        entry = self.manager.get_entry(date_str)
        if entry:
            self.title_var.set(entry.title)
            self.text.delete("1.0", tk.END)
            self.text.insert("1.0", entry.content)
            self.word_count_var.set(f"字数：{entry.word_count}")
        else:
            self.title_var.set("")
            self.text.delete("1.0", tk.END)
            self.word_count_var.set("字数：0")

    def _on_content_change(self) -> None:
        """内容变化时更新字数统计。"""
        content = self.text.get("1.0", tk.END).strip()
        word_count = len(content.replace("\n", " ").split()) if content else 0
        self.word_count_var.set(f"字数：{word_count}")

    def _update_mood_display(self, date_str: str) -> None:
        """从 StatusManager 获取当天心情数据并显示。"""
        record = self.status_manager.get_by_date(date_str)
        if record:
            self.mood_var.set(
                f"心情：{self._mood_emoji(record.mood)} {record.mood}/5  "
                f"精力：{record.energy}/5  "
                f"专注：{record.focus}/5  "
                f"睡眠：{record.sleep_hours}h"
            )
        else:
            self.mood_var.set("")

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
        title = self.title_var.get().strip()
        content = self.text.get("1.0", tk.END).strip()
        self.manager.save_entry(self._current_date, title, content)
        self.set_status(f"日记已保存 ({self._current_date})")
        self._on_content_change()
        self._update_calendar_marks()

    def _auto_save(self) -> None:
        """失去焦点或切换日期时自动保存。"""
        if not self._current_date:
            return
        title = self.title_var.get().strip()
        content = self.text.get("1.0", tk.END).strip()
        # 检查是否有现有条目
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
        if not messagebox.askyesno("确认删除", f"确定要删除 {self._current_date} 的日记吗？"):
            return
        self.manager.delete_entry(self._current_date)
        self.title_var.set("")
        self.text.delete("1.0", tk.END)
        self.word_count_var.set("字数：0")
        self.mood_var.set("")
        self.set_status(f"已删除 {self._current_date} 的日记")
        self._update_calendar_marks()

    # ---- 搜索 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self.set_status("请输入搜索关键词")
            return
        results = self.manager.search(keyword)
        if results:
            entry = results[0]
            self.set_status(f"找到 {len(results)} 条结果，跳转到第一条：{entry.date}")
            self._auto_save()
            self.calendar.select_date(entry.date)
            self.calendar.goto_date(
                int(entry.date[:4]), int(entry.date[5:7])
            )
        else:
            self.set_status("未找到匹配的日记")

    # ---- 统计 ----

    def _show_statistics(self) -> None:
        stats = self.manager.get_statistics()
        msg = (
            f"日记总数：{stats['total_entries']} 篇\n"
            f"总字数：{stats['total_words']}\n"
            f"平均字数：{stats['avg_words']}\n"
            f"连续天数：{stats['current_streak']} 天"
        )
        messagebox.showinfo("日记统计", msg)

    # ---- 导出 ----

    def _export_markdown(self) -> None:
        if not self._current_date:
            messagebox.showinfo("提示", "请先选择一个日期")
            return

        entry = self.manager.get_entry(self._current_date)
        if not entry:
            messagebox.showinfo("提示", f"{self._current_date} 没有日记内容")
            return

        default_name = f"journal_{self._current_date}.md"
        path = filedialog.asksaveasfilename(
            defaultextension=".md", filetypes=[("Markdown", "*.md")],
            initialfile=default_name
        )
        if path:
            try:
                self.manager.export_single(self._current_date, path)
                self.set_status(f"日记已导出至：{path}")
            except Exception as e:
                messagebox.showerror("导出失败", str(e))

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
        """刷新页面数据。"""
        self._update_calendar_marks()
        if self._current_date:
            self._load_entry(self._current_date)
            self._update_mood_display(self._current_date)
        self._update_stats()

    def _update_stats(self) -> None:
        stats = self.manager.get_statistics()
        self.stats_var.set(
            f"共 {stats['total_entries']} 篇日记  "
            f"总字数 {stats['total_words']}  "
            f"连续 {stats['current_streak']} 天"
        )

    def highlight_item(self, item_id: str) -> None:
        """高亮指定日记条目（由全局搜索导航调用）。"""
        entry = self.manager.get_by_id(item_id)
        if entry:
            self._auto_save()
            self.calendar.select_date(entry.date)
            dt = datetime.strptime(entry.date, "%Y-%m-%d")
            self.calendar.goto_date(dt.year, dt.month)
