"""密码管理页面 — PySide6 版本。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QLabel,
    QTableWidgetItem, QFileDialog, QMessageBox, QMenu, QHeaderView,
    QDialog, QFormLayout, QLineEdit, QDialogButtonBox, QApplication
)
from PySide6.QtCore import Qt

from Services.PasswordManager import PasswordManager
from Services.CryptoService import CryptoService
from Models.Password import PasswordEntry
from .BasePage import BasePage
from .Widgets import SearchBar, FormDialog, ConfirmDialog


class PasswordPage(BasePage):
    """密码管理页面，密码不明文显示在列表中。"""

    def __init__(self, parent=None, set_status=None):
        super().__init__(parent, set_status)
        self.manager = PasswordManager()

        self._build_toolbar()
        self._build_table_columns()
        self._build_context_menu()

    # ---- 工具栏 ----

    def _build_toolbar(self) -> None:
        self._toolbar_widget = QWidget()
        toolbar_layout = QHBoxLayout(self._toolbar_widget)
        toolbar_layout.setContentsMargins(0, 4, 0, 4)

        self.search_bar = SearchBar(placeholder="搜索密码...")
        self.search_bar.search_requested.connect(self._on_search)
        toolbar_layout.addWidget(self.search_bar)

        toolbar_layout.addStretch()

        self.master_pwd_btn = QPushButton()
        self.master_pwd_btn.clicked.connect(self._on_master_pwd_click)
        toolbar_layout.addWidget(self.master_pwd_btn)

        add_btn = QPushButton("+ 添加密码")
        add_btn.clicked.connect(self._open_add_dialog)
        toolbar_layout.addWidget(add_btn)

        self._layout.insertWidget(0, self._toolbar_widget)

    def _update_master_pwd_btn(self) -> None:
        status = CryptoService.get_lock_status()
        if not status["is_configured"]:
            self.master_pwd_btn.setText("设置主密码")
        elif status["is_locked"]:
            cooldown = status.get("cooldown_remaining", 0)
            if cooldown > 0:
                self.master_pwd_btn.setText(f"已锁定({cooldown}s)")
            else:
                self.master_pwd_btn.setText("解锁主密码")
        else:
            self.master_pwd_btn.setText("已解锁")

    def _on_master_pwd_click(self) -> None:
        status = CryptoService.get_lock_status()
        if not status["is_configured"]:
            self._show_setup_dialog()
        elif status["is_locked"]:
            cooldown = status.get("cooldown_remaining", 0)
            if cooldown > 0:
                QMessageBox.information(
                    self, "已锁定",
                    f"连续错误次数过多，请 {cooldown} 秒后重试"
                )
            else:
                self._show_unlock_dialog()
        else:
            QMessageBox.information(self, "主密码", "主密码已解锁，密码功能可用。")

    # ---- 表格 ----

    def _build_table_columns(self) -> None:
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "平台", "网址", "账号", "备注", "更新时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)

    # ---- 右键菜单 ----

    def _build_context_menu(self) -> QMenu | None:
        entry_id = self._get_selected_id()
        if not entry_id:
            return None
        menu = QMenu(self)
        menu.addAction("查看密码", self._view_password)
        menu.addAction("复制密码", self._copy_password)
        menu.addSeparator()
        menu.addAction("编辑", self._open_edit_dialog)
        menu.addSeparator()
        menu.addAction("删除", self._confirm_delete)
        return menu

    # ---- 主密码管理 ----

    def _ensure_crypto_ready(self) -> bool:
        if not CryptoService.is_configured():
            result = QMessageBox.question(
                self, "未设置主密码",
                "密码管理功能需要先设置主密码来保护您的数据安全。\n\n"
                "是否现在设置主密码？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if result == QMessageBox.Yes:
                self._show_setup_dialog()
                return CryptoService.is_unlocked()
            return False

        if not CryptoService.is_unlocked():
            result = QMessageBox.question(
                self, "主密码已锁定",
                "主密码未解锁，无法操作密码数据。\n\n是否现在解锁？",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            if result == QMessageBox.Yes:
                self._show_unlock_dialog()
                return CryptoService.is_unlocked()
            return False

        return True

    def _show_setup_dialog(self) -> None:
        dialog = MasterPasswordSetupDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._update_master_pwd_btn()
            self.emit_status("主密码已设置，密码数据已加密保护")
            base64_count = self.manager.migrate_from_base64()
            v2_count = self.manager.migrate_to_v2()
            total = base64_count + v2_count
            if total > 0:
                self.emit_status(f"主密码已设置，{total} 条密码已升级加密")
            self.refresh()

    def _show_unlock_dialog(self) -> None:
        dialog = MasterPasswordUnlockDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self._update_master_pwd_btn()
            self.emit_status("主密码已解锁")
            status = self.manager.get_migration_status()
            if status.get("needs_migration"):
                v2_count = self.manager.migrate_to_v2()
                if v2_count > 0:
                    self.emit_status(f"主密码已解锁，{v2_count} 条密码已升级为 v2 格式")
            self.refresh()

    # ---- 添加 ----

    def _open_add_dialog(self) -> None:
        if not self._ensure_crypto_ready():
            return
        fields = [
            {"key": "platform", "label": "平台", "type": "text", "required": True},
            {"key": "url", "label": "网址", "type": "text"},
            {"key": "username", "label": "账号", "type": "text"},
            {"key": "password", "label": "密码", "type": "text",
             "show": "*", "required": True},
            {"key": "note", "label": "备注", "type": "text"},
        ]
        data = FormDialog.get_form_data(self, "添加密码", fields)
        if data:
            self._do_add(data)

    def _do_add(self, data: dict) -> None:
        if not self._ensure_crypto_ready():
            return
        try:
            self.manager.add_entry(
                platform=data["platform"], url=data.get("url", ""),
                username=data.get("username", ""),
                password=data["password"],
                note=data.get("note", "")
            )
            self.refresh()
            self.emit_status(f"密码「{data['platform']}」已添加")
        except Exception as e:
            QMessageBox.critical(self, "添加失败", str(e))

    # ---- 查看密码 ----

    def _view_password(self) -> None:
        if not self._ensure_crypto_ready():
            return
        entry = self._get_selected()
        if not entry:
            return
        try:
            plain = self.manager.get_decrypted_password(entry.id)
            QMessageBox.information(
                self, f"查看密码 - {entry.platform}",
                f"平台：{entry.platform}\n账号：{entry.username}\n密码：{plain}"
            )
        except Exception as e:
            QMessageBox.critical(self, "查看失败", str(e))

    # ---- 复制密码 ----

    def _copy_password(self) -> None:
        if not self._ensure_crypto_ready():
            return
        entry = self._get_selected()
        if not entry:
            return
        try:
            plain = self.manager.get_decrypted_password(entry.id)
            QApplication.clipboard().setText(plain)
            self.emit_status(f"密码「{entry.platform}」已复制到剪贴板")
        except Exception as e:
            QMessageBox.critical(self, "复制失败", str(e))

    # ---- 编辑 ----

    def _open_edit_dialog(self) -> None:
        if not self._ensure_crypto_ready():
            return
        entry = self._get_selected()
        if not entry:
            return
        fields = [
            {"key": "platform", "label": "平台", "type": "text", "required": True},
            {"key": "url", "label": "网址", "type": "text"},
            {"key": "username", "label": "账号", "type": "text"},
            {"key": "password", "label": "密码（留空不修改）", "type": "text", "show": "*"},
            {"key": "note", "label": "备注", "type": "text"},
        ]
        initial = {
            "platform": entry.platform, "url": entry.url,
            "username": entry.username, "note": entry.note,
        }
        data = FormDialog.get_form_data(self, "编辑密码", fields, initial)
        if data:
            self._do_edit(entry.id, data)

    def _do_edit(self, entry_id: str, data: dict) -> None:
        if not self._ensure_crypto_ready():
            return
        try:
            updates = {
                "platform": data["platform"], "url": data.get("url", ""),
                "username": data.get("username", ""),
                "note": data.get("note", ""),
            }
            if data.get("password"):
                updates["password"] = data["password"]
            self.manager.update_entry(entry_id, **updates)
            self.refresh()
            self.emit_status(f"密码「{data['platform']}」已更新")
        except Exception as e:
            QMessageBox.critical(self, "编辑失败", str(e))

    # ---- 删除 ----

    def _confirm_delete(self) -> None:
        entry = self._get_selected()
        if not entry:
            return
        if ConfirmDialog.show(self, "确认删除",
                              f"确定要删除「{entry.platform}」的密码记录吗？"):
            self.manager.delete_entry(entry.id)
            self.refresh()
            self.emit_status(f"密码「{entry.platform}」已删除")

    # ---- 搜索 ----

    def _on_search(self, keyword: str) -> None:
        if not keyword:
            self.refresh()
            return
        results = self.manager.search(keyword)
        self._populate_table(results)

    # ---- 数据加载 ----

    def refresh(self) -> None:
        entries = self.manager.get_all()
        self._populate_table(entries)
        self._set_stats_text(f"共 {self.manager.count()} 条密码记录")
        self._update_master_pwd_btn()

    def _populate_table(self, entries: list[PasswordEntry]) -> None:
        self._clear_table()
        for e in entries:
            self._add_row([
                e.platform, e.url, e.username, e.note,
                e.updated_at[:10] if e.updated_at else e.created_at[:10],
            ], item_id=e.id)

    def _get_selected(self) -> PasswordEntry | None:
        entry_id = self._get_selected_id()
        if not entry_id:
            QMessageBox.information(self, "提示", "请先选中一条记录")
            return None
        return self.manager.get_by_id(entry_id)


# ============================================================
#  MasterPasswordSetupDialog
# ============================================================

class MasterPasswordSetupDialog(QDialog):
    """主密码设置对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置主密码")
        self.setModal(True)
        self.setMinimumWidth(350)
        self._build()

    def _build(self) -> None:
        layout = QFormLayout(self)
        layout.setSpacing(10)

        layout.addRow(QLabel("请设置主密码（至少 4 位）："))

        pwd_row = QHBoxLayout()
        self.pwd_entry = QLineEdit()
        self.pwd_entry.setEchoMode(QLineEdit.Password)
        self.pwd_entry.textChanged.connect(self._on_pwd_changed)
        pwd_row.addWidget(self.pwd_entry)
        layout.addRow("主密码：", pwd_row)

        self.confirm_entry = QLineEdit()
        self.confirm_entry.setEchoMode(QLineEdit.Password)
        layout.addRow("确认密码：", self.confirm_entry)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red; font-size: 11px;")
        layout.addRow(self.error_label)

        self.strength_label = QLabel()
        self.strength_label.setStyleSheet("font-size: 10px;")
        layout.addRow(self.strength_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("设置")
        buttons.accepted.connect(self._do_setup)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.confirm_entry.returnPressed.connect(self._do_setup)
        self.pwd_entry.setFocus()

    def _on_pwd_changed(self) -> None:
        pwd = self.pwd_entry.text()
        if not pwd:
            self.strength_label.setText("")
            return
        info = CryptoService.get_password_strength(pwd)
        labels = {"weak": "弱", "fair": "一般", "medium": "中等",
                   "strong": "强", "very_strong": "非常强"}
        colors = {"weak": "red", "fair": "orange", "medium": "#cc9900",
                   "strong": "green", "very_strong": "darkgreen"}
        self.strength_label.setText(f"密码强度：{labels.get(info['level'], info['level'])}")
        self.strength_label.setStyleSheet(
            f"color: {colors.get(info['level'], 'gray')}; font-size: 10px;"
        )

    def _do_setup(self) -> None:
        pwd = self.pwd_entry.text()
        confirm = self.confirm_entry.text()
        try:
            CryptoService.setup_master_password(pwd, confirm)
            self.accept()
        except ValueError as e:
            self.error_label.setText(str(e))


# ============================================================
#  MasterPasswordUnlockDialog
# ============================================================

class MasterPasswordUnlockDialog(QDialog):
    """主密码解锁对话框。"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("解锁主密码")
        self.setModal(True)
        self.setMinimumWidth(320)
        self._build()

    def _build(self) -> None:
        layout = QFormLayout(self)
        layout.setSpacing(10)

        layout.addRow(QLabel("请输入主密码："))

        self.pwd_entry = QLineEdit()
        self.pwd_entry.setEchoMode(QLineEdit.Password)
        layout.addRow("", self.pwd_entry)

        self.error_label = QLabel()
        self.error_label.setStyleSheet("color: red; font-size: 11px;")
        layout.addRow(self.error_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("解锁")
        buttons.accepted.connect(self._do_unlock)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self.pwd_entry.returnPressed.connect(self._do_unlock)
        self.pwd_entry.setFocus()

    def _do_unlock(self) -> None:
        pwd = self.pwd_entry.text()
        try:
            if CryptoService.unlock(pwd):
                self.accept()
            else:
                self.error_label.setText("主密码错误，请重试")
                self.pwd_entry.clear()
        except Exception as ex:
            self.error_label.setText(str(ex))
            self.pwd_entry.clear()
