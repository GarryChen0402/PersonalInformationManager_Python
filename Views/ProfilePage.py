"""个人档案页面。"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from Models.Profile import Profile
from Services.ProfileManager import ProfileManager


FIELDS = [
    ("name", "姓名", "text"),
    ("gender", "性别", "combobox"),
    ("birthday", "生日", "text"),
    ("phone", "手机", "text"),
    ("email", "邮箱", "text"),
    ("address", "地址", "text"),
    ("wechat", "微信", "text"),
    ("qq", "QQ", "text"),
    ("github", "GitHub", "text"),
    ("blog", "博客", "text"),
    ("bio", "简介", "textarea"),
]


class ProfilePage(tk.Frame):
    """个人档案管理页面，表单式编辑。"""

    def __init__(self, parent: tk.Widget, set_status):
        super().__init__(parent, bg="#ffffff")
        self.manager = ProfileManager()
        self.set_status = set_status
        self.editing = False
        self.widgets: dict[str, tk.Widget] = {}

        self._build_header()
        self._build_form()
        self._build_summary()

    # ---- 头部 ----

    def _build_header(self) -> None:
        header = tk.Frame(self, bg="#fafafa", pady=10)
        header.pack(fill=tk.X, padx=16, pady=(16, 0))

        tk.Label(
            header, text="个人档案", bg="#fafafa",
            font=("Microsoft YaHei", 16, "bold")
        ).pack(side=tk.LEFT)

        self.edit_btn = tk.Button(
            header, text="编辑", command=self._toggle_edit,
            font=("Microsoft YaHei", 9), padx=12,
            cursor="hand2"
        )
        self.edit_btn.pack(side=tk.RIGHT, padx=4)

        export_btn = tk.Button(
            header, text="导出", command=self._export,
            font=("Microsoft YaHei", 9), padx=12,
            cursor="hand2"
        )
        export_btn.pack(side=tk.RIGHT, padx=4)

    # ---- 表单 ----

    def _build_form(self) -> None:
        container = tk.Frame(self, bg="#ffffff")
        container.pack(fill=tk.BOTH, expand=True, padx=32, pady=16)

        for i, (field, label, kind) in enumerate(FIELDS):
            lbl = tk.Label(
                container, text=f"{label}：", bg="#ffffff",
                font=("Microsoft YaHei", 10), anchor=tk.E, width=8
            )
            lbl.grid(row=i, column=0, sticky=tk.NE, padx=(0, 8), pady=4)

            if kind == "combobox":
                widget = ttk.Combobox(
                    container, values=["男", "女", "其他"],
                    state="readonly", font=("Microsoft YaHei", 10)
                )
                widget.grid(row=i, column=1, sticky=tk.EW, pady=4)
            elif kind == "textarea":
                widget = tk.Text(
                    container, height=3, font=("Microsoft YaHei", 10),
                    wrap=tk.WORD, state=tk.DISABLED
                )
                widget.grid(row=i, column=1, sticky=tk.EW, pady=4)
            else:
                widget = tk.Entry(
                    container, font=("Microsoft YaHei", 10),
                    state=tk.DISABLED
                )
                widget.grid(row=i, column=1, sticky=tk.EW, pady=4)

            self.widgets[field] = widget

        container.columnconfigure(1, weight=1)

    # ---- 底部统计 ----

    def _build_summary(self) -> None:
        self.summary_var = tk.StringVar()
        summary = tk.Label(
            self, textvariable=self.summary_var, bg="#f5f5f5",
            font=("Microsoft YaHei", 9), fg="#666666", pady=6
        )
        summary.pack(fill=tk.X, side=tk.BOTTOM)

    # ---- 数据加载 ----

    def refresh(self) -> None:
        """从 Manager 重新加载档案数据并刷新界面。"""
        profile = self.manager.get_profile()
        for field, _label, kind in FIELDS:
            value = getattr(profile, field, "")
            widget = self.widgets[field]
            if kind == "textarea":
                self._set_text(widget, value)
            elif kind == "combobox":
                if value:
                    widget.set(value)
                else:
                    widget.set("")
            else:
                self._set_entry(widget, value)
        self._update_summary()

    # ---- 编辑状态切换 ----

    def _toggle_edit(self) -> None:
        if self.editing:
            self._save()
        else:
            self.editing = True
            self.edit_btn.configure(text="保存")
            self._set_fields_state(tk.NORMAL)
            if isinstance(self.widgets["gender"], ttk.Combobox):
                self.widgets["gender"].configure(state="readonly")

    def _save(self) -> None:
        data = {}
        for field, _label, kind in FIELDS:
            widget = self.widgets[field]
            if kind == "textarea":
                data[field] = widget.get("1.0", tk.END).strip()
            elif kind == "combobox":
                data[field] = widget.get()
            else:
                data[field] = widget.get().strip()

        try:
            self.manager.update_profile(**data)
            self.editing = False
            self.edit_btn.configure(text="编辑")
            self._set_fields_state(tk.DISABLED)
            self._update_status("档案已保存")
            self._update_summary()
        except Exception as e:
            messagebox.showerror("保存失败", str(e))

    def _set_fields_state(self, state: str) -> None:
        for field, _label, kind in FIELDS:
            widget = self.widgets[field]
            if kind == "combobox":
                widget.configure(state="readonly" if state == tk.DISABLED else "readonly")
            elif kind == "textarea":
                widget.configure(state=state)
            else:
                widget.configure(state=state)

    # ---- 导出 ----

    def _export(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json"), ("CSV 文件", "*.csv")],
            initialfile="profile.json"
        )
        if path:
            try:
                if path.endswith(".csv"):
                    self.manager.export_csv(path)
                else:
                    self.manager.export_profile(path)
                self._update_status(f"档案已导出到 {path}")
            except Exception as e:
                messagebox.showerror("导出失败", str(e))

    # ---- 统计 ----

    def _update_summary(self) -> None:
        s = self.manager.get_summary()
        self.summary_var.set(
            f"档案完整度：{s['filled']}/{s['total']} 字段已填写"
            f"    最后更新：{s['last_updated']}"
        )

    # ---- 工具方法 ----

    def _set_entry(self, widget: tk.Entry, value: str) -> None:
        state = widget.cget("state")
        widget.configure(state=tk.NORMAL)
        widget.delete(0, tk.END)
        widget.insert(0, value)
        widget.configure(state=state)

    def _set_text(self, widget: tk.Text, value: str) -> None:
        state = widget.cget("state")
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.configure(state=state)

    def _update_status(self, message: str) -> None:
        if self.set_status:
            self.set_status(message)
