"""应用程序主窗口 — PySide6 版本。"""

import datetime
import sys

from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QStatusBar, QSplitter, QLabel,
    QMessageBox, QApplication, QDialog, QVBoxLayout, QLineEdit,
    QPushButton, QHBoxLayout, QWidget
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction, QKeySequence, QFont

from .NavFrame import NavFrame
from .Themes import THEMES, THEME_NAMES, THEME_DISPLAY
from Services.ConfigManager import ConfigManager
from Services.CryptoService import CryptoService
from Services.PasswordManager import PasswordManager
from Services.SkillManager import SkillManager
from Services.StatusManager import StatusManager
from Services.KnowledgeManager import KnowledgeManager
from Services.TodoManager import TodoManager
from Services.HabitManager import HabitManager
from Services.JournalManager import JournalManager


class App(QMainWindow):
    """个人信息管理器主应用程序 (PySide6)。"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("个人信息管理器 v1.3")
        self.resize(960, 640)
        self.setMinimumSize(800, 500)

        self.config_manager = ConfigManager()
        self._font_scale = 1.0

        # 搜索管理器（全局搜索复用）
        self._search_managers = {
            "skill": SkillManager(),
            "status": StatusManager(),
            "knowledge": KnowledgeManager(),
            "todo": TodoManager(),
            "habit": HabitManager(),
            "journal": JournalManager(),
            "password": PasswordManager(),
        }

        # 页面容器
        self.stack = QStackedWidget()
        self.pages: dict[str, QWidget] = {}

        # 导航栏
        self.nav = NavFrame()

        # 主布局
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.nav)
        self.splitter.addWidget(self.stack)
        self.splitter.setStretchFactor(0, 0)
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([170, 790])
        self.setCentralWidget(self.splitter)

        # 状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.clock_label = QLabel()
        self.status_bar.addPermanentWidget(self.clock_label)

        version_label = QLabel("v1.3  ")
        self.status_bar.addPermanentWidget(version_label)

        # 连接导航信号
        self.nav.navigated.connect(self._switch_page)

        # 初始化
        self._init_pages()
        self._init_shortcuts()
        self._apply_theme()
        self._restore_window_geometry()
        self._start_clock()

        # 默认页面
        last_module = self.config_manager.get_last_active_module()
        self._switch_page(last_module)
        self.set_status("就绪")

        # 主密码处理
        self._handle_master_password()

    # ---- 页面初始化 ----

    def _init_pages(self) -> None:
        """初始化所有功能页面（渐进迁移：页面完成后自动加载）。"""
        page_factories = {}

        # 阶段三：核心模块（上）
        try:
            from .DashboardPage import DashboardPage
            page_factories["dashboard"] = lambda: DashboardPage(self.stack, self.set_status, self._switch_page)
        except ImportError:
            page_factories["dashboard"] = lambda: self._placeholder_page("数据概览")

        try:
            from .ProfilePage import ProfilePage
            page_factories["profile"] = lambda: ProfilePage(self.stack, self.set_status)
        except ImportError:
            page_factories["profile"] = lambda: self._placeholder_page("个人档案")

        try:
            from .SkillPage import SkillPage
            page_factories["skill"] = lambda: SkillPage(self.stack, self.set_status)
        except ImportError:
            page_factories["skill"] = lambda: self._placeholder_page("技能管理")

        # 阶段四：核心模块（下）
        try:
            from .StatusPage import StatusPage
            page_factories["status"] = lambda: StatusPage(self.stack, self.set_status)
        except ImportError:
            page_factories["status"] = lambda: self._placeholder_page("状态管理")

        try:
            from .KnowledgePage import KnowledgePage
            page_factories["knowledge"] = lambda: KnowledgePage(self.stack, self.set_status)
        except ImportError:
            page_factories["knowledge"] = lambda: self._placeholder_page("知识管理")

        try:
            from .TodoPage import TodoPage
            page_factories["todo"] = lambda: TodoPage(self.stack, self.set_status)
        except ImportError:
            page_factories["todo"] = lambda: self._placeholder_page("待办事项")

        # 阶段五：功能模块
        try:
            from .HabitPage import HabitPage
            page_factories["habit"] = lambda: HabitPage(self.stack, self.set_status)
        except ImportError:
            page_factories["habit"] = lambda: self._placeholder_page("习惯追踪")

        try:
            from .JournalPage import JournalPage
            page_factories["journal"] = lambda: JournalPage(self.stack, self.set_status)
        except ImportError:
            page_factories["journal"] = lambda: self._placeholder_page("日记")

        try:
            from .PasswordPage import PasswordPage
            page_factories["password"] = lambda: PasswordPage(self.stack, self.set_status)
        except ImportError:
            page_factories["password"] = lambda: self._placeholder_page("密码管理")

        # 阶段六：收尾
        try:
            from .BackupPage import BackupPage
            page_factories["backup"] = lambda: BackupPage(self.stack, self.set_status)
        except ImportError:
            page_factories["backup"] = lambda: self._placeholder_page("数据管理")

        for name, factory in page_factories.items():
            try:
                page = factory()
            except Exception:
                page = self._placeholder_page(name)
            self.pages[name] = page
            self.stack.addWidget(page)

    def _placeholder_page(self, title: str) -> QWidget:
        """占位页面（模块尚未迁移时显示）。"""
        w = QWidget()
        layout = QVBoxLayout(w)
        label = QLabel(f"{title}\n\n模块迁移中...")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Microsoft YaHei", 14))
        layout.addWidget(label)
        return w

    # ---- 页面切换 ----

    def _switch_page(self, page_name: str) -> None:
        """切换内容区显示的页面。"""
        page = self.pages.get(page_name)
        if page is None:
            return
        self.stack.setCurrentWidget(page)
        if hasattr(page, "refresh"):
            page.refresh()
        if page_name != "dashboard":
            self.config_manager.set_last_active_module(page_name)
        self.nav.set_active(page_name)

    def _navigate_to(self, page_name: str) -> None:
        """导航辅助方法（供 Dashboard 卡片点击使用）。"""
        self._switch_page(page_name)

    # ---- 全局搜索 ----

    def _do_global_search(self, keyword: str) -> list:
        """跨模块搜索，聚合结果。"""
        from .GlobalSearchBar import SearchResult
        results: list[SearchResult] = []
        kw = keyword.lower()

        for s in self._search_managers["skill"].search(keyword):
            results.append(SearchResult(
                name=s.name, module="skill", item_id=s.id,
                snippet=f"{s.category}  Lv{s.level}"
            ))

        for item in self._search_managers["knowledge"].search(keyword):
            mod = "note" if item.item_type == "note" else "ebook"
            results.append(SearchResult(
                name=item.title, module=mod, item_id=item.id,
                snippet=item.category
            ))

        for t in self._search_managers["todo"].search(keyword):
            priority = {"high": "高", "mid": "中", "low": "低"}.get(t.priority, "")
            results.append(SearchResult(
                name=t.title, module="todo", item_id=t.id,
                snippet=f"{priority}优先级" if priority else ""
            ))

        for h in self._search_managers["habit"].search(keyword):
            results.append(SearchResult(
                name=h.name, module="habit", item_id=h.id,
                snippet=h.category
            ))

        for j in self._search_managers["journal"].search(keyword):
            results.append(SearchResult(
                name=j.title or f"{j.date} 日记",
                module="journal", item_id=j.id,
                snippet=j.title or j.content[:30]
            ))

        for p in self._search_managers["password"].search(keyword):
            results.append(SearchResult(
                name=p.platform, module="password", item_id=p.id,
                snippet=p.username
            ))

        for s in self._search_managers["status"].get_all():
            if kw in s.note.lower() or kw in s.date:
                results.append(SearchResult(
                    name=s.date, module="status", item_id=s.id,
                    snippet=f"心情{s.mood} 精力{s.energy}"
                ))

        return results[:20]

    def _on_global_navigate(self, module: str, item_id: str) -> None:
        """搜索结果导航。"""
        nav_map = {
            "skill": "skill", "note": "knowledge", "ebook": "knowledge",
            "todo": "todo", "habit": "habit", "journal": "journal",
            "password": "password", "status": "status",
        }
        page_name = nav_map.get(module, module)
        self._switch_page(page_name)
        page = self.pages.get(page_name)
        if page and hasattr(page, "highlight_item"):
            if page_name == "knowledge":
                page.highlight_item(item_id, module)
            else:
                page.highlight_item(item_id)

    # ---- 状态栏 ----

    def set_status(self, message: str) -> None:
        """更新状态栏消息。"""
        self.status_bar.showMessage(message, 5000)

    # ---- 主题 ----

    def _apply_theme(self) -> None:
        """应用主题样式表。"""
        theme_name = self.config_manager.get_theme()
        stylesheet = THEMES.get(theme_name, THEMES["light"])
        QApplication.instance().setStyleSheet(stylesheet)

    def _cycle_theme(self) -> None:
        """循环切换主题。"""
        current = self.config_manager.get_theme()
        try:
            idx = THEME_NAMES.index(current)
        except ValueError:
            idx = 0
        new_theme = THEME_NAMES[(idx + 1) % len(THEME_NAMES)]
        self.config_manager.set_theme(new_theme)
        self._apply_theme()
        display = THEME_DISPLAY.get(new_theme, new_theme)
        self.set_status(f"主题已切换：{display}")

    # ---- 快捷键 ----

    def _init_shortcuts(self) -> None:
        """初始化键盘快捷键。"""
        # Ctrl+T: 切换主题
        switch_theme = QAction("切换主题", self)
        switch_theme.setShortcut(QKeySequence("Ctrl+T"))
        switch_theme.triggered.connect(self._cycle_theme)
        self.addAction(switch_theme)

        # Ctrl+Shift+F 或 Ctrl+S: 聚焦搜索（阶段六实现）
        focus_search = QAction("全局搜索", self)
        focus_search.setShortcut(QKeySequence("Ctrl+Shift+F"))
        focus_search.triggered.connect(self.nav.focus_search)
        self.addAction(focus_search)

        focus_search2 = QAction("全局搜索2", self)
        focus_search2.setShortcut(QKeySequence("Ctrl+S"))
        focus_search2.triggered.connect(self.nav.focus_search)
        self.addAction(focus_search2)

        # Ctrl+N: 新建
        new_action = QAction("新建", self)
        new_action.setShortcut(QKeySequence("Ctrl+N"))
        new_action.triggered.connect(self._new_item_shortcut)
        self.addAction(new_action)

        # Ctrl+= / Ctrl+- / Ctrl+0: 字体缩放
        zoom_in = QAction("放大字体", self)
        zoom_in.setShortcut(QKeySequence("Ctrl+="))
        zoom_in.triggered.connect(lambda: self._scale_fonts(0.1))
        self.addAction(zoom_in)

        zoom_out = QAction("缩小字体", self)
        zoom_out.setShortcut(QKeySequence("Ctrl+-"))
        zoom_out.triggered.connect(lambda: self._scale_fonts(-0.1))
        self.addAction(zoom_out)

        zoom_reset = QAction("重置字体", self)
        zoom_reset.setShortcut(QKeySequence("Ctrl+0"))
        zoom_reset.triggered.connect(self._reset_font_scale)
        self.addAction(zoom_reset)

        # Ctrl+1~9: 快速导航（前 9 个模块）
        nav_order = ["profile", "status", "skill", "knowledge", "todo", "habit", "journal", "password", "backup"]
        for i, name in enumerate(nav_order):
            if i < 9:
                action = QAction(f"导航{name}", self)
                action.setShortcut(QKeySequence(f"Ctrl+{i + 1}"))
                action.triggered.connect(lambda checked, n=name: self._switch_page(n))
                self.addAction(action)

    def _new_item_shortcut(self) -> None:
        """Ctrl+N 触发当前页面的创建操作。"""
        current_widget = self.stack.currentWidget()
        if current_widget is None:
            return
        method_names = ["_open_add_dialog", "_open_create_dialog",
                        "_open_import_dialog", "_toggle_edit", "add_item"]
        for method_name in method_names:
            method = getattr(current_widget, method_name, None)
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
        font = QApplication.instance().font()
        base_size = self.config_manager.get("font_size", 9)
        font.setPointSize(int(base_size * new_scale))
        QApplication.instance().setFont(font)
        self.set_status(f"字体缩放：{self._font_scale:.1f}x")

    def _reset_font_scale(self) -> None:
        """重置字体缩放。"""
        if self._font_scale == 1.0:
            return
        self._font_scale = 1.0
        font = QApplication.instance().font()
        base_size = self.config_manager.get("font_size", 9)
        font.setPointSize(base_size)
        QApplication.instance().setFont(font)
        self.set_status("字体缩放已重置")

    # ---- 主密码 ----

    def _handle_master_password(self) -> None:
        """处理主密码：已配置则解锁，有密码数据但未配置则提示设置。"""
        if CryptoService.is_configured():
            QTimer.singleShot(100, self._show_unlock_dialog)
        elif self._has_password_data():
            QTimer.singleShot(500, self._show_setup_suggestion)

    def _has_password_data(self) -> bool:
        pm = PasswordManager()
        return pm.count() > 0

    def _show_unlock_dialog(self) -> None:
        dialog = _PasswordUnlockDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._check_password_migration()
            self.set_status("主密码已解锁")
        else:
            self.set_status("密码管理功能已锁定（主密码未解锁）")

    def _show_setup_suggestion(self) -> None:
        result = QMessageBox.question(
            self, "设置主密码",
            "检测到已有密码数据（旧格式）。\n\n"
            "建议立即设置主密码以保护数据安全。\n\n"
            "是否现在设置主密码？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if result == QMessageBox.Yes:
            self._show_setup_dialog()

    def _show_setup_dialog(self) -> None:
        dialog = _PasswordSetupDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._check_password_migration()
            self.set_status("主密码已设置，密码数据已加密保护")

    def _check_password_migration(self) -> None:
        if not CryptoService.is_unlocked():
            return
        try:
            pm = PasswordManager()
            if self.config_manager.is_password_migration_pending():
                count = pm.migrate_from_base64()
                if count > 0:
                    self.config_manager.clear_password_migration_flag()
                    self.set_status(f"密码数据迁移完成：{count} 条已升级加密")
            status = pm.get_migration_status()
            if status.get("needs_migration"):
                v2_count = pm.migrate_to_v2()
                if v2_count > 0:
                    self.set_status(f"密码加密升级完成：{v2_count} 条已升级为 v2 格式（HMAC 认证）")
        except Exception:
            pass

    # ---- 窗口几何 ----

    def _restore_window_geometry(self) -> None:
        geo_hex = self.config_manager.get_window_geometry()
        if geo_hex:
            try:
                self.restoreGeometry(bytes.fromhex(geo_hex))
            except Exception:
                pass

    def _save_window_geometry(self) -> None:
        try:
            geo_hex = self.saveGeometry().hex()
            self.config_manager.set_window_geometry(geo_hex)
        except Exception:
            pass

    # ---- 时钟 ----

    def _start_clock(self) -> None:
        def update():
            self.clock_label.setText(
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
        update()
        self._clock_timer = QTimer()
        self._clock_timer.timeout.connect(update)
        self._clock_timer.start(60000)

    # ---- 关闭 ----

    def closeEvent(self, event) -> None:
        result = QMessageBox.question(
            self, "确认退出",
            "确定要退出个人信息管理器吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if result == QMessageBox.Yes:
            self._save_window_geometry()
            event.accept()
        else:
            event.ignore()


# ---- 主密码对话框 ----

class _PasswordUnlockDialog(QDialog):
    """主密码解锁对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("主密码验证")
        self.setFixedSize(340, 160)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("请输入主密码以解锁密码管理功能："))

        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        self.pwd_input.setPlaceholderText("主密码")
        layout.addWidget(self.pwd_input)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        btn_layout = QHBoxLayout()
        skip_btn = QPushButton("跳过")
        skip_btn.clicked.connect(self.reject)
        unlock_btn = QPushButton("解锁")
        unlock_btn.clicked.connect(self._try_unlock)
        unlock_btn.setDefault(True)
        btn_layout.addWidget(skip_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(unlock_btn)
        layout.addLayout(btn_layout)

        self.pwd_input.setFocus()

    def _try_unlock(self) -> None:
        pwd = self.pwd_input.text()
        try:
            if CryptoService.unlock(pwd):
                self.accept()
            else:
                self.error_label.setText("主密码错误，请重试")
                self.error_label.setVisible(True)
                self.pwd_input.clear()
                self.pwd_input.setFocus()
        except Exception as ex:
            self.error_label.setText(str(ex))
            self.error_label.setVisible(True)
            self.pwd_input.clear()


class _PasswordSetupDialog(QDialog):
    """主密码设置对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置主密码")
        self.setFixedSize(380, 250)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("请设置主密码（至少 4 位）："))

        layout.addWidget(QLabel("主密码："))
        self.pwd_input = QLineEdit()
        self.pwd_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.pwd_input)

        layout.addWidget(QLabel("确认密码："))
        self.confirm_input = QLineEdit()
        self.confirm_input.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.confirm_input)

        self.strength_label = QLabel()
        layout.addWidget(self.strength_label)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red;")
        self.error_label.setVisible(False)
        layout.addWidget(self.error_label)

        self.pwd_input.textChanged.connect(self._update_strength)

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        setup_btn = QPushButton("设置")
        setup_btn.clicked.connect(self._do_setup)
        setup_btn.setDefault(True)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(setup_btn)
        layout.addLayout(btn_layout)

        self.pwd_input.setFocus()

    def _update_strength(self, pwd: str) -> None:
        if not pwd:
            self.strength_label.setText("")
            return
        info = CryptoService.get_password_strength(pwd)
        labels = {"weak": "弱", "fair": "一般", "medium": "中等",
                   "strong": "强", "very_strong": "非常强"}
        colors = {"weak": "red", "fair": "orange", "medium": "#cc9900",
                   "strong": "green", "very_strong": "darkgreen"}
        level = info.get("level", "weak")
        self.strength_label.setText(f"密码强度：{labels.get(level, level)}")
        self.strength_label.setStyleSheet(f"color: {colors.get(level, 'gray')};")

    def _do_setup(self) -> None:
        pwd = self.pwd_input.text()
        confirm = self.confirm_input.text()
        try:
            CryptoService.setup_master_password(pwd, confirm)
            self.accept()
        except ValueError as e:
            self.error_label.setText(str(e))
            self.error_label.setVisible(True)
