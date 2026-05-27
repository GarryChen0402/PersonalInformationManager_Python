"""数据备份与恢复页面 — PySide6 版本。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QCheckBox,
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QDialogButtonBox
)
from PySide6.QtCore import Qt

from Services.BackupManager import BackupManager
from .Widgets import ConfirmDialog


def _format_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"


class BackupPage(QWidget):
    """数据管理页面，备份列表 + 操作按钮。"""

    def __init__(self, parent=None, set_status=None):
        super().__init__(parent)
        self.manager = BackupManager()
        self._set_status = set_status

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # 头部
        header = QHBoxLayout()
        title = QLabel("数据管理")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        header.addWidget(title)
        header.addStretch()

        create_btn = QPushButton("+ 创建备份")
        create_btn.clicked.connect(self._create_backup)
        header.addWidget(create_btn)
        layout.addLayout(header)

        # 表格
        self.table = self._build_table()
        layout.addWidget(self.table)

        # 操作按钮
        actions = QHBoxLayout()
        btn_configs = [
            ("查看详情", self._show_detail),
            ("恢复全部", self._restore_all),
            ("恢复选择...", self._restore_selected),
            ("删除备份", self._delete_backup),
        ]
        for text, handler in btn_configs:
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            actions.addWidget(btn)
        actions.addStretch()
        layout.addLayout(actions)

    def _build_table(self) -> QWidget:
        from PySide6.QtWidgets import QTableWidget
        table = QTableWidget()
        table.setColumnCount(3)
        table.setHorizontalHeaderLabels(["文件名", "创建时间", "大小"])
        table.setSelectionBehavior(QTableWidget.SelectRows)
        table.setSelectionMode(QTableWidget.SingleSelection)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.horizontalHeader().setStretchLastSection(True)
        return table

    # ---- 操作 ----

    def _create_backup(self) -> None:
        try:
            path = self.manager.create_backup()
            self.refresh()
            self._emit_status(f"备份已创建: {path}")
        except Exception as e:
            QMessageBox.critical(self, "备份失败", str(e))

    def _show_detail(self) -> None:
        backup = self._get_selected()
        if not backup:
            return
        info = self.manager.get_backup_info(backup["path"])
        if not info:
            QMessageBox.critical(self, "错误", "无法读取备份文件")
            return

        lines = [f"备份文件: {backup['name']}\n"]
        for module, detail in info.items():
            if isinstance(detail, int):
                lines.append(f"  {module}: {detail} 条记录")
            else:
                lines.append(f"  {module}: {detail}")
        QMessageBox.information(self, "备份详情", "\n".join(lines))

    def _restore_all(self) -> None:
        backup = self._get_selected()
        if not backup:
            return
        if not ConfirmDialog.show(
            self, "确认恢复",
            f"确定要从「{backup['name']}」恢复全部数据吗？\n此操作将覆盖当前数据。"
        ):
            return
        try:
            result = self.manager.restore_backup(backup["path"])
            msg = f"成功恢复: {', '.join(result['success'])}"
            if result["failed"]:
                msg += f"\n失败: {', '.join(result['failed'])}"
            QMessageBox.information(self, "恢复完成", msg + "\n\n建议重启程序以刷新所有页面。")
            self._emit_status("数据已恢复，建议重启程序")
        except Exception as e:
            QMessageBox.critical(self, "恢复失败", str(e))

    def _restore_selected(self) -> None:
        backup = self._get_selected()
        if not backup:
            return

        info = self.manager.get_backup_info(backup["path"])
        if not info:
            QMessageBox.critical(self, "错误", "无法读取备份文件")
            return

        dialog = RestoreSelectDialog(info, self)
        if dialog.exec() == QDialog.Accepted and dialog.selected_modules:
            try:
                result = self.manager.restore_backup(
                    backup["path"], modules=dialog.selected_modules
                )
                msg = f"成功恢复: {', '.join(result['success'])}"
                if result["failed"]:
                    msg += f"\n失败: {', '.join(result['failed'])}"
                QMessageBox.information(self, "恢复完成", msg)
                self._emit_status("部分数据已恢复")
            except Exception as e:
                QMessageBox.critical(self, "恢复失败", str(e))

    def _delete_backup(self) -> None:
        backup = self._get_selected()
        if not backup:
            return
        if ConfirmDialog.show(self, "确认删除",
                              f"确定要删除备份「{backup['name']}」吗？"):
            self.manager.delete_backup(backup["path"])
            self.refresh()
            self._emit_status(f"备份「{backup['name']}」已删除")

    # ---- 数据加载 ----

    def refresh(self) -> None:
        backups = self.manager.list_backups()
        self.table.setRowCount(0)
        for b in backups:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(b["name"]))
            self.table.setItem(row, 1, QTableWidgetItem(b["created_at"]))
            self.table.setItem(row, 2, QTableWidgetItem(_format_size(b["size"])))
            # Store path as UserRole on first column
            self.table.item(row, 0).setData(Qt.UserRole, b["path"])

    def _get_selected(self) -> dict | None:
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.information(self, "提示", "请先选中一个备份文件")
            return None
        path = self.table.item(row, 0).data(Qt.UserRole)
        for b in self.manager.list_backups():
            if b["path"] == path:
                return b
        return None

    def _emit_status(self, text: str) -> None:
        if self._set_status:
            self._set_status(text)


class RestoreSelectDialog(QDialog):
    """按模块选择恢复对话框。"""

    MODULE_NAMES = {
        "profile": "个人档案", "skills": "技能", "status": "状态",
        "knowledge": "知识", "passwords": "密码",
    }

    def __init__(self, info: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择恢复模块")
        self.setModal(True)
        self.selected_modules: list[str] = []
        self._build(info)

    def _build(self, info: dict) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        layout.addWidget(QLabel("请选择要恢复的模块："))

        self._checks: dict[str, QCheckBox] = {}
        for mod_key, mod_label in self.MODULE_NAMES.items():
            if mod_key in info:
                detail = info[mod_key]
                detail_text = f"{detail} 条记录" if isinstance(detail, int) else detail
                cb = QCheckBox(f"{mod_label} ({detail_text})")
                cb.setChecked(True)
                self._checks[mod_key] = cb
                layout.addWidget(cb)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("恢复")
        buttons.accepted.connect(self._do_restore)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _do_restore(self) -> None:
        self.selected_modules = [k for k, cb in self._checks.items() if cb.isChecked()]
        if not self.selected_modules:
            QMessageBox.warning(self, "提示", "请至少选择一个模块")
            return
        self.accept()
