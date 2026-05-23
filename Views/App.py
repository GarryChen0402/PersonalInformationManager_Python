"""应用程序主窗口。"""

import tkinter as tk
from tkinter import font as tkfont
from tkinter import messagebox

from .NavFrame import NavFrame
from .DashboardPage import DashboardPage
from .ProfilePage import ProfilePage
from .SkillPage import SkillPage
from .StatusPage import StatusPage
from .KnowledgePage import KnowledgePage
from .PasswordPage import PasswordPage
from .BackupPage import BackupPage
from .TodoPage import TodoPage
from .GlobalSearchBar import SearchResult
from Services.ConfigManager import ConfigManager
from Services.CryptoService import CryptoService
from Services.PasswordManager import PasswordManager
from Services.SkillManager import SkillManager
from Services.StatusManager import StatusManager
from Services.KnowledgeManager import KnowledgeManager
from Services.TodoManager import TodoManager


# ---- 配色主题 ----

LIGHT_THEME = {
    "bg": "#ffffff",
    "fg": "#333333",
    "toolbar_bg": "#fafafa",
    "stats_bg": "#f5f5f5",
    "nav_bg": "#f0f0f0",
    "nav_active": "#4a90d9",
    "button_bg": "#e0e0e0",
    "card_bg": "#f8f9fa",
    "border": "#dddddd",
    "status_bg": "#f0f0f0",
}

DARK_THEME = {
    "bg": "#1e1e1e",
    "fg": "#d4d4d4",
    "toolbar_bg": "#252526",
    "stats_bg": "#2d2d2d",
    "nav_bg": "#252526",
    "nav_active": "#264f78",
    "button_bg": "#3c3c3c",
    "card_bg": "#2d2d2d",
    "border": "#3e3e3e",
    "status_bg": "#252526",
}

THEMES = {"light": LIGHT_THEME, "dark": DARK_THEME}


class App:
    """个人信息管理器主应用程序。"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("个人信息管理器 (PIM)")
        self.root.geometry("960x640")
        self.root.minsize(800, 500)

        # 字体缩放
        self._font_scale = 1.0

        # 加载配置
        self.config_manager = ConfigManager()

        # 应用主题
        theme_name = self.config_manager.get_theme()
        self.theme = THEMES.get(theme_name, LIGHT_THEME)
        self.root.configure(bg=self.theme["bg"])

        # 底部状态栏（必须在 _handle_master_password 之前创建，
        # 因为解锁/设置对话框的回调会调用 set_status）
        bottom_frame = tk.Frame(
            self.root, bd=1, relief=tk.SUNKEN, bg=self.theme["status_bg"]
        )
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_var = tk.StringVar(value="就绪")
        self.status_bar = tk.Label(
            bottom_frame, textvariable=self.status_var,
            anchor=tk.W, padx=8, font=("Microsoft YaHei", 9),
            bg=self.theme["status_bg"], fg=self.theme["fg"]
        )
        self.status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # 主密码处理
        self._handle_master_password()

        version_label = tk.Label(
            bottom_frame, text="v1.2  ",
            anchor=tk.E, padx=8, font=("Microsoft YaHei", 9),
            bg=self.theme["status_bg"], fg=self.theme["fg"]
        )
        version_label.pack(side=tk.RIGHT)

        # 搜索管理器
        self._search_managers = {
            "skill": SkillManager(),
            "status": StatusManager(),
            "knowledge": KnowledgeManager(),
            "todo": TodoManager(),
            "password": PasswordManager(),
        }

        # 左侧导航栏
        self.nav = NavFrame(
            self.root, on_select=self._switch_page, theme=self.theme,
            on_search=self._do_global_search,
            on_navigate=self._on_global_navigate,
        )

        # 右侧内容区
        self.content = tk.Frame(self.root, bg=self.theme["bg"])
        self.content.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # 初始化页面
        self.pages: dict[str, tk.Frame] = {}
        self._init_pages()

        # 默认显示
        last_module = self.config_manager.get_last_active_module()
        self._switch_page(last_module)
        self.nav.set_active(last_module)

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 键盘快捷键
        self._bind_shortcuts()

    # ---- 主密码 ----

    def _handle_master_password(self) -> None:
        """处理主密码：已配置则解锁，有密码数据但未配置则提示设置。"""
        if CryptoService.is_configured():
            # 已有主密码配置，弹出解锁对话框
            self._show_unlock_dialog()
        elif self._has_password_data():
            # 有密码数据但未设置主密码（从旧版本升级），提示设置
            self.root.after(500, self._show_setup_suggestion)

    def _has_password_data(self) -> bool:
        """检查是否存在密码数据。"""
        pm = PasswordManager()
        return pm.count() > 0

    def _show_unlock_dialog(self) -> None:
        """显示主密码解锁对话框。"""
        dialog = tk.Toplevel(self.root)
        dialog.title("主密码验证")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        # 居中
        dialog.geometry("320x150")
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 320) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 150) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = tk.Frame(dialog, padx=20, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame, text="请输入主密码以解锁密码管理功能：",
            font=("Microsoft YaHei", 10)
        ).pack(anchor=tk.W, pady=(0, 10))

        pwd_var = tk.StringVar()
        pwd_entry = tk.Entry(
            frame, textvariable=pwd_var, show="*",
            font=("Microsoft YaHei", 11), width=30
        )
        pwd_entry.pack(fill=tk.X, pady=(0, 12))
        dialog.after_idle(pwd_entry.focus_set)

        error_var = tk.StringVar()
        error_label = tk.Label(
            frame, textvariable=error_var,
            font=("Microsoft YaHei", 9), fg="red"
        )
        error_label.pack(anchor=tk.W)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        def do_unlock():
            pwd = pwd_var.get()
            try:
                if CryptoService.unlock(pwd):
                    dialog.destroy()
                    self._check_password_migration()
                    self.set_status("主密码已解锁")
                else:
                    error_var.set("主密码错误，请重试")
                    pwd_var.set("")
            except Exception as ex:
                error_var.set(str(ex))
                pwd_var.set("")

        def do_skip():
            dialog.destroy()
            self.set_status("密码管理功能已锁定（主密码未解锁）")

        cancel_btn = tk.Button(
            btn_frame, text="跳过", command=do_skip,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT)

        unlock_btn = tk.Button(
            btn_frame, text="解锁", command=do_unlock,
            font=("Microsoft YaHei", 9), padx=16, cursor="hand2"
        )
        unlock_btn.pack(side=tk.RIGHT)

        pwd_entry.bind("<Return>", lambda e: do_unlock())
        dialog.bind("<Escape>", lambda e: do_skip())

        self.root.wait_window(dialog)

    def _show_setup_suggestion(self) -> None:
        """提示用户设置主密码（旧版本升级场景）。"""
        result = messagebox.askyesno(
            "设置主密码",
            "检测到已有密码数据（v1.0 旧格式）。\n\n"
            "v1.1 已升级为加密存储，建议立即设置主密码以保护数据安全。\n\n"
            "是否现在设置主密码？\n"
            "（选择「否」可稍后在密码管理页面设置）"
        )
        if result:
            self._show_setup_dialog()

    def _show_setup_dialog(self) -> None:
        """显示主密码设置对话框。"""
        dialog = tk.Toplevel(self.root)
        dialog.title("设置主密码")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()

        dialog.geometry("350x220")
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 350) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 220) // 2
        dialog.geometry(f"+{x}+{y}")

        frame = tk.Frame(dialog, padx=20, pady=16)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame, text="请设置主密码（至少 4 位）：",
            font=("Microsoft YaHei", 10)
        ).pack(anchor=tk.W, pady=(0, 10))

        tk.Label(
            frame, text="主密码：", font=("Microsoft YaHei", 9)
        ).pack(anchor=tk.W)
        pwd_var = tk.StringVar()
        pwd_entry = tk.Entry(
            frame, textvariable=pwd_var, show="*",
            font=("Microsoft YaHei", 11)
        )
        pwd_entry.pack(fill=tk.X, pady=(2, 8))
        dialog.after_idle(pwd_entry.focus_set)

        tk.Label(
            frame, text="确认密码：", font=("Microsoft YaHei", 9)
        ).pack(anchor=tk.W)
        confirm_var = tk.StringVar()
        confirm_entry = tk.Entry(
            frame, textvariable=confirm_var, show="*",
            font=("Microsoft YaHei", 11)
        )
        confirm_entry.pack(fill=tk.X, pady=(2, 8))

        error_var = tk.StringVar()
        error_label = tk.Label(
            frame, textvariable=error_var,
            font=("Microsoft YaHei", 9), fg="red"
        )
        error_label.pack(anchor=tk.W)

        # 密码强度指示
        strength_var = tk.StringVar(value="")
        strength_label = tk.Label(
            frame, textvariable=strength_var,
            font=("Microsoft YaHei", 9)
        )
        strength_label.pack(anchor=tk.W, pady=(4, 0))

        def on_pwd_change(*args):
            pwd = pwd_var.get()
            if not pwd:
                strength_var.set("")
                return
            info = CryptoService.get_password_strength(pwd)
            labels = {"weak": "弱", "fair": "一般", "medium": "中等",
                       "strong": "强", "very_strong": "非常强"}
            colors = {"weak": "red", "fair": "orange", "medium": "#cc9900",
                       "strong": "green", "very_strong": "darkgreen"}
            strength_var.set(f"密码强度：{labels.get(info['level'], info['level'])}")
            strength_label.configure(fg=colors.get(info["level"], "gray"))

        pwd_var.trace_add("write", on_pwd_change)

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=(8, 0))

        def do_setup():
            pwd = pwd_var.get()
            confirm = confirm_var.get()
            try:
                CryptoService.setup_master_password(pwd, confirm)
                dialog.destroy()
                self._check_password_migration()
                self.set_status("主密码已设置，密码数据已加密保护")
            except ValueError as e:
                error_var.set(str(e))

        cancel_btn = tk.Button(
            btn_frame, text="取消", command=dialog.destroy,
            font=("Microsoft YaHei", 9), padx=12, cursor="hand2"
        )
        cancel_btn.pack(side=tk.LEFT)

        save_btn = tk.Button(
            btn_frame, text="设置", command=do_setup,
            font=("Microsoft YaHei", 9), padx=16, cursor="hand2"
        )
        save_btn.pack(side=tk.RIGHT)

        confirm_entry.bind("<Return>", lambda e: do_setup())
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        self.root.wait_window(dialog)

    def _check_password_migration(self) -> None:
        """检查并执行密码数据迁移（base64 → v1 → v2）。"""
        if not CryptoService.is_unlocked():
            return
        try:
            pm = PasswordManager()
            # 先迁移 base64
            if self.config_manager.is_password_migration_pending():
                count = pm.migrate_from_base64()
                if count > 0:
                    self.config_manager.clear_password_migration_flag()
                    self.set_status(f"密码数据迁移完成：{count} 条已升级加密")

            # 再检查 v1→v2 迁移
            status = pm.get_migration_status()
            if status.get("needs_migration"):
                v2_count = pm.migrate_to_v2()
                if v2_count > 0:
                    self.set_status(f"密码加密升级完成：{v2_count} 条已升级为 v2 格式（HMAC 认证）")
        except Exception:
            pass  # 迁移失败不阻塞启动

    # ---- 页面初始化 ----

    def _init_pages(self) -> None:
        """初始化所有功能页面。"""
        self.pages["profile"] = ProfilePage(self.content, self.set_status)
        self.pages["skill"] = SkillPage(self.content, self.set_status)
        self.pages["status"] = StatusPage(self.content, self.set_status)
        self.pages["knowledge"] = KnowledgePage(self.content, self.set_status)
        self.pages["todo"] = TodoPage(self.content, self.set_status)
        self.pages["password"] = PasswordPage(self.content, self.set_status)
        self.pages["backup"] = BackupPage(self.content, self.set_status)

        self.pages["dashboard"] = DashboardPage(
            self.content, self.set_status, self._switch_page
        )

    # ---- 页面切换 ----

    def _switch_page(self, page_name: str) -> None:
        """切换内容区显示的页面。"""
        for page in self.pages.values():
            page.pack_forget()
        page = self.pages.get(page_name)
        if page:
            page.pack(fill=tk.BOTH, expand=True)
            if hasattr(page, "refresh"):
                page.refresh()
            self.config_manager.set_last_active_module(page_name)

    # ---- 全局搜索 ----

    def _do_global_search(self, keyword: str) -> list[SearchResult]:
        """跨模块搜索，聚合结果（每模块最多 8 条，总计最多 20 条）。"""
        results: list[SearchResult] = []

        # 技能
        for s in self._search_managers["skill"].search(keyword):
            results.append(SearchResult(
                name=s.name, module="skill", item_id=s.id,
                snippet=f"{s.category}  Lv{s.level}"
            ))

        # 知识（笔记 + 电子书）
        for item in self._search_managers["knowledge"].search(keyword):
            if item.item_type == "note":
                results.append(SearchResult(
                    name=item.title, module="note", item_id=item.id,
                    snippet=item.category
                ))
            elif item.item_type == "ebook":
                results.append(SearchResult(
                    name=item.title, module="ebook", item_id=item.id,
                    snippet=item.category
                ))

        # 待办
        for t in self._search_managers["todo"].search(keyword):
            priority = {"high": "高", "mid": "中", "low": "低"}.get(t.priority, "")
            results.append(SearchResult(
                name=t.title, module="todo", item_id=t.id,
                snippet=f"{priority}优先级" if priority else ""
            ))

        # 密码（不搜索密码内容，仅搜索平台/账号）
        for p in self._search_managers["password"].search(keyword):
            results.append(SearchResult(
                name=p.platform, module="password", item_id=p.id,
                snippet=p.username
            ))

        # 状态（搜索备注）
        for s in self._search_managers["status"].get_all():
            if kw in s.note.lower() or kw in s.date:
                results.append(SearchResult(
                    name=s.date, module="status", item_id=s.id,
                    snippet=f"心情{s.mood} 精力{s.energy}" if s.note else s.note[:16]
                ))

        return results[:20]

    def _on_global_navigate(self, module: str, item_id: str) -> None:
        """搜索结果导航：切换到目标页面并高亮条目。"""
        nav_map = {
            "skill": "skill", "note": "knowledge", "ebook": "knowledge",
            "todo": "todo", "password": "password", "status": "status",
        }
        page_name = nav_map.get(module, module)
        self._switch_page(page_name)
        self.nav.set_active(page_name)

        page = self.pages.get(page_name)
        if page and hasattr(page, "highlight_item"):
            # 对于知识页面，传递子类型
            if page_name == "knowledge":
                page.highlight_item(item_id, module)
            else:
                page.highlight_item(item_id)

    # ---- 状态栏 ----

    def set_status(self, message: str) -> None:
        """更新状态栏消息。"""
        self.status_var.set(message)

    # ---- 主题 ----

    def _toggle_theme(self) -> None:
        """切换浅色/深色主题。"""
        current = self.config_manager.get_theme()
        new_theme = "dark" if current == "light" else "light"
        self.config_manager.set_theme(new_theme)
        messagebox.showinfo(
            "主题切换",
            f"已切换到{'深色' if new_theme == 'dark' else '浅色'}主题。\n请重启程序以完全应用。"
        )

    # ---- 快捷键 ----

    def _bind_shortcuts(self) -> None:
        """绑定全局键盘快捷键。"""
        self.root.bind("<Control-t>", lambda e: self._toggle_theme())
        self.root.bind("<Control-Shift-F>", lambda e: self._focus_search())
        self.root.bind("<Control-s>", lambda e: self._focus_search())
        self.root.bind("<Control-n>", lambda e: self._new_item_shortcut())
        # 字体缩放
        self.root.bind("<Control-equal>", lambda e: self._scale_fonts(0.1))
        self.root.bind("<Control-minus>", lambda e: self._scale_fonts(-0.1))
        self.root.bind("<Control-0>", lambda e: self._reset_font_scale())
        # Ctrl+1~8 快速切换导航
        nav_order = ["profile", "status", "skill", "knowledge", "todo", "password", "backup", "dashboard"]
        for i, name in enumerate(nav_order):
            self.root.bind(f"<Control-Key-{i + 1}>", lambda e, n=name: self._navigate(n))

    def _navigate(self, page_name: str) -> None:
        """导航到指定页面。"""
        self._switch_page(page_name)
        self.nav.set_active(page_name)

    def _focus_search(self) -> None:
        """聚焦全局搜索框。"""
        if self.nav.search_bar:
            self.nav.search_bar.focus()

    def _new_item_shortcut(self) -> None:
        """Ctrl+N 触发当前页面的创建操作。"""
        current_module = self.config_manager.get_last_active_module()
        page = self.pages.get(current_module)
        if page is None:
            return
        # 各页面的创建方法名
        method_names = ["_open_add_dialog", "_open_create_dialog",
                        "_open_import_dialog", "_toggle_edit"]
        for method_name in method_names:
            method = getattr(page, method_name, None)
            if callable(method):
                method()
                return

    # ---- 字体缩放 ----

    def _scale_fonts(self, delta: float) -> None:
        """缩放全局字体。"""
        new_scale = max(0.6, min(2.0, self._font_scale + delta))
        if new_scale == self._font_scale:
            return
        self._font_scale = new_scale
        self._walk_scale_fonts(self.root, self._font_scale)
        self.set_status(f"字体缩放：{self._font_scale:.1f}x")

    def _reset_font_scale(self) -> None:
        """重置字体缩放为 1.0。"""
        if self._font_scale == 1.0:
            return
        self._font_scale = 1.0
        self._walk_scale_fonts(self.root, 1.0)
        self.set_status("字体缩放已重置")

    def _walk_scale_fonts(self, widget: tk.Widget, scale: float) -> None:
        """递归应用字体缩放到所有子控件。"""
        for child in widget.winfo_children():
            try:
                font_info = tkfont.Font(font=child.cget("font"))
                cfg = font_info.configure()
                size = cfg.get("size", 9)
                if size and isinstance(size, (int, float)) and size > 0:
                    key = f"_base_size_{child}"
                    if not hasattr(child, key):
                        setattr(child, key, size)
                    base = getattr(child, key)
                    new_size = max(5, int(base * scale))
                    font_info.configure(size=new_size)
                    child.configure(font=font_info)
            except Exception:
                pass
            self._walk_scale_fonts(child, scale)

    # ---- 关闭 ----

    def _on_close(self) -> None:
        """关闭窗口确认。"""
        if messagebox.askyesno("确认退出", "确定要退出个人信息管理器吗？"):
            self.root.destroy()

    # ---- 启动 ----

    def run(self) -> None:
        """启动主事件循环。"""
        self.root.mainloop()
