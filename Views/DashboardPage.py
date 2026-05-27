"""数据概览仪表盘页面 — PySide6 版本。"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QFrame
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from Services.ProfileManager import ProfileManager
from Services.SkillManager import SkillManager
from Services.StatusManager import StatusManager
from Services.KnowledgeManager import KnowledgeManager
from Services.PasswordManager import PasswordManager
from Services.BackupManager import BackupManager
from .ChartWidgets import MiniChart


class _Card(QFrame):
    """仪表盘卡片组件。"""
    clicked = Signal(str)

    def __init__(self, card_id: str, title: str, icon: str, navigate_to: str, parent=None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(150)
        self._navigate_to = navigate_to

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(6)

        # 图标
        icon_label = QLabel(icon)
        icon_label.setFixedSize(36, 36)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_label.setStyleSheet(
            "QLabel { background-color: #4a90d9; color: white; border-radius: 4px; "
            "font-size: 16px; font-weight: bold; }"
        )
        layout.addWidget(icon_label)

        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Bold))
        layout.addWidget(title_label)

        # 数据容器
        self.data_layout = QVBoxLayout()
        self.data_layout.setSpacing(2)
        layout.addLayout(self.data_layout)

        # 迷你图预留区
        self.mini_chart_container = QVBoxLayout()
        layout.addLayout(self.mini_chart_container)

        layout.addStretch()
        self._setup_click()

    def _setup_click(self) -> None:
        def mouse_press(event):
            if event.button() == Qt.LeftButton:
                self.clicked.emit(self._navigate_to)
        self.mousePressEvent = mouse_press

    def set_data_lines(self, lines: list[str]) -> None:
        # 清除旧标签
        for i in reversed(range(self.data_layout.count())):
            w = self.data_layout.itemAt(i).widget()
            if w:
                w.deleteLater()
        for line in lines:
            lbl = QLabel(line)
            lbl.setStyleSheet("color: #555555; font-size: 11px;")
            self.data_layout.addWidget(lbl)


class DashboardPage(QWidget):
    """仪表盘页面，以卡片网格展示各模块概览。"""

    navigate = Signal(str)

    CARDS = [
        {"id": "profile", "title": "个人档案", "icon": "P", "navigate": "profile"},
        {"id": "skill", "title": "技能管理", "icon": "S", "navigate": "skill"},
        {"id": "status", "title": "状态管理", "icon": "D", "navigate": "status"},
        {"id": "knowledge", "title": "知识管理", "icon": "K", "navigate": "knowledge"},
        {"id": "password", "title": "密码管理", "icon": "W", "navigate": "password"},
        {"id": "backup", "title": "数据管理", "icon": "B", "navigate": "backup"},
    ]

    def __init__(self, parent=None, set_status=None, navigate=None):
        super().__init__(parent)
        self.set_status = set_status
        self._navigate_cb = navigate

        self.managers = {
            "profile": ProfileManager(),
            "skill": SkillManager(),
            "status": StatusManager(),
            "knowledge": KnowledgeManager(),
            "password": PasswordManager(),
            "backup": BackupManager(),
        }

        self._cards: dict[str, _Card] = {}
        self._mini_charts: dict[str, MiniChart] = {}

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        header = QHBoxLayout()
        title_lbl = QLabel("数据概览")
        title_lbl.setFont(QFont("Microsoft YaHei", 16, QFont.Bold))
        header.addWidget(title_lbl)
        subtitle = QLabel("点击卡片可跳转到对应模块")
        subtitle.setStyleSheet("color: #999999; font-size: 11px;")
        header.addWidget(subtitle)
        header.addStretch()
        layout.addLayout(header)

        # 卡片网格 2行 × 3列
        grid = QGridLayout()
        grid.setSpacing(10)
        for i, card_def in enumerate(self.CARDS):
            row, col = divmod(i, 3)
            card = _Card(card_def["id"], card_def["title"],
                        card_def["icon"], card_def["navigate"])
            card.clicked.connect(self._on_card_click)
            grid.addWidget(card, row, col)
            self._cards[card_def["id"]] = card

            # 状态卡片添加迷你图
            if card_def["id"] == "status":
                mini = MiniChart()
                mini.setMinimumHeight(40)
                card.mini_chart_container.addWidget(mini)
                self._mini_charts["status"] = mini

        layout.addLayout(grid)
        layout.addStretch()

    def _on_card_click(self, page_name: str) -> None:
        self.navigate.emit(page_name)
        if self._navigate_cb:
            self._navigate_cb(page_name)

    def refresh(self) -> None:
        for card_def in self.CARDS:
            card_id = card_def["id"]
            card = self._cards.get(card_id)
            if not card:
                continue
            if card_id == "profile":
                lines = self._profile_info()
            elif card_id == "skill":
                lines = self._skill_info()
            elif card_id == "status":
                lines = self._status_info()
            elif card_id == "knowledge":
                lines = self._knowledge_info()
            elif card_id == "password":
                lines = self._password_info()
            elif card_id == "backup":
                lines = self._backup_info()
            else:
                lines = []
            card.set_data_lines(lines)

        self._update_status_mini_chart()

    def _update_status_mini_chart(self) -> None:
        mini = self._mini_charts.get("status")
        if not mini:
            return
        records = self.managers["status"].get_latest(14)
        if len(records) >= 2:
            moods = [r.mood for r in reversed(records)]
            mini.set_data(moods)
        else:
            mini.set_data([])

    def _profile_info(self) -> list[str]:
        s = self.managers["profile"].get_summary()
        return [f"已填: {s['filled']}/{s['total']} 字段", f"最后更新: {s['last_updated']}"]

    def _skill_info(self) -> list[str]:
        s = self.managers["skill"].get_statistics()
        if s["total"] == 0:
            return ["暂无数据"]
        return [
            f"共 {s['total']} 项技能",
            f"总学习时长: {s['total_hours']:.0f}h",
            f"平均熟练度: {s['avg_level']}/5",
        ]

    def _status_info(self) -> list[str]:
        s = self.managers["status"].get_statistics(period="week")
        if s["count"] == 0:
            return ["本周暂无记录"]
        return [
            f"本周 {s['count']} 条记录",
            f"心情: {s['mood']}/5  精力: {s['energy']}/5",
            f"专注度: {s['focus']}/5  睡眠: {s['sleep_hours']}h",
        ]

    def _knowledge_info(self) -> list[str]:
        s = self.managers["knowledge"].get_statistics()
        parts = []
        if s["total_notes"] > 0:
            parts.append(f"笔记: {s['total_notes']} 篇")
        if s["total_ebooks"] > 0:
            parts.append(f"电子书: {s['total_ebooks']} 本")
        if not parts:
            return ["暂无数据"]
        return parts

    def _password_info(self) -> list[str]:
        count = self.managers["password"].count()
        if count == 0:
            return ["暂无数据"]
        return [f"共 {count} 条密码记录"]

    def _backup_info(self) -> list[str]:
        backups = self.managers["backup"].list_backups()
        if not backups:
            return ["暂无备份"]
        latest = backups[0]
        return [f"共 {len(backups)} 个备份", f"最近: {latest['created_at']}"]
