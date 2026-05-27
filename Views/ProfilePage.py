"""个人档案页面 — PySide6 版本。"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QComboBox, QTextEdit, QPushButton, QFrame, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from Services.ProfileManager import ProfileManager

FIELDS = [
    ("name", "姓名", "text"),
    ("gender", "性别", "combo"),
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


class ProfilePage(QWidget):
    """个人档案管理页面，表单式编辑。"""

    def __init__(self, parent=None, set_status=None):
        super().__init__(parent)
        self.manager = ProfileManager()
        self.set_status = set_status
        self.editing = False
        self.widgets: dict[str, QWidget] = {}

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        header = QHBoxLayout()
        title_lbl = QLabel("个人档案")
        title_lbl.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        header.addWidget(title_lbl)
        header.addStretch()

        self.edit_btn = QPushButton("编辑")
        self.edit_btn.clicked.connect(self._toggle_edit)
        header.addWidget(self.edit_btn)

        export_btn = QPushButton("导出")
        export_btn.clicked.connect(self._export)
        header.addWidget(export_btn)
        layout.addLayout(header)

        # 表单
        form_container = QWidget()
        form = QFormLayout(form_container)
        form.setSpacing(8)

        for field, label, kind in FIELDS:
            if kind == "combo":
                widget = QComboBox()
                widget.addItems(["男", "女", "其他"])
                widget.setEnabled(False)
            elif kind == "textarea":
                widget = QTextEdit()
                widget.setMaximumHeight(80)
                widget.setReadOnly(True)
            else:
                widget = QLineEdit()
                widget.setReadOnly(True)

            self.widgets[field] = widget
            form.addRow(label + "：", widget)

        layout.addWidget(form_container)

        # 统计栏
        self.summary_label = QLabel()
        self.summary_label.setProperty("statsLabel", True)
        self.summary_label.setStyleSheet("color: #666666; font-size: 11px; padding: 6px;")
        layout.addWidget(self.summary_label)

    def refresh(self) -> None:
        profile = self.manager.get_profile()
        for field, _label, kind in FIELDS:
            value = getattr(profile, field, "")
            widget = self.widgets[field]
            if kind == "textarea":
                widget.setPlainText(str(value) if value else "")
            elif kind == "combo":
                widget.setCurrentText(value if value else "")
            else:
                widget.setText(str(value) if value else "")
        self._update_summary()

    def _toggle_edit(self) -> None:
        if self.editing:
            self._save()
        else:
            self.editing = True
            self.edit_btn.setText("保存")
            self._set_fields_enabled(True)

    def _save(self) -> None:
        data = {}
        for field, _label, kind in FIELDS:
            widget = self.widgets[field]
            if kind == "textarea":
                data[field] = widget.toPlainText().strip()
            elif kind == "combo":
                data[field] = widget.currentText()
            else:
                data[field] = widget.text().strip()

        try:
            self.manager.update_profile(**data)
            self.editing = False
            self.edit_btn.setText("编辑")
            self._set_fields_enabled(False)
            self._update_status("档案已保存")
            self._update_summary()
        except Exception as e:
            QMessageBox.critical(self, "保存失败", str(e))

    def _set_fields_enabled(self, enabled: bool) -> None:
        for field, _label, kind in FIELDS:
            widget = self.widgets[field]
            if kind == "combo":
                widget.setEnabled(enabled)
            elif kind == "textarea":
                widget.setReadOnly(not enabled)
            else:
                widget.setReadOnly(not enabled)

    def _export(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "导出档案", "profile.json",
            "JSON 文件 (*.json);;CSV 文件 (*.csv)"
        )
        if path:
            try:
                if path.endswith(".csv"):
                    self.manager.export_csv(path)
                else:
                    self.manager.export_profile(path)
                self._update_status(f"档案已导出到 {path}")
            except Exception as e:
                QMessageBox.critical(self, "导出失败", str(e))

    def _update_summary(self) -> None:
        s = self.manager.get_summary()
        self.summary_label.setText(
            f"档案完整度：{s['filled']}/{s['total']} 字段已填写"
            f"    最后更新：{s['last_updated']}"
        )

    def _update_status(self, message: str) -> None:
        if self.set_status:
            self.set_status(message)
