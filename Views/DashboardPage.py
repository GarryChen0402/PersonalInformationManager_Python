"""数据概览仪表盘页面。"""

import tkinter as tk
from typing import Callable

from Services.ProfileManager import ProfileManager
from Services.SkillManager import SkillManager
from Services.StatusManager import StatusManager
from Services.KnowledgeManager import KnowledgeManager
from Services.PasswordManager import PasswordManager
from Services.BackupManager import BackupManager


class DashboardPage(tk.Frame):
    """仪表盘页面，以卡片网格展示各模块概览。"""

    CARD_STYLE = {
        "bg": "#f8f9fa",
        "bd": 1,
        "relief": tk.GROOVE,
        "padx": 16,
        "pady": 12,
        "cursor": "hand2",
    }

    CARDS = [
        {
            "id": "profile", "title": "个人档案", "icon": "P",
            "navigate": "profile",
            "fetch": lambda self: self._profile_info(),
        },
        {
            "id": "skill", "title": "技能管理", "icon": "S",
            "navigate": "skill",
            "fetch": lambda self: self._skill_info(),
        },
        {
            "id": "status", "title": "状态管理", "icon": "D",
            "navigate": "status",
            "fetch": lambda self: self._status_info(),
        },
        {
            "id": "knowledge", "title": "知识管理", "icon": "K",
            "navigate": "knowledge",
            "fetch": lambda self: self._knowledge_info(),
        },
        {
            "id": "password", "title": "密码管理", "icon": "W",
            "navigate": "password",
            "fetch": lambda self: self._password_info(),
        },
        {
            "id": "backup", "title": "数据管理", "icon": "B",
            "navigate": "backup",
            "fetch": lambda self: self._backup_info(),
        },
    ]

    def __init__(self, parent: tk.Widget, set_status, navigate: Callable[[str], None]):
        super().__init__(parent, bg="#ffffff")
        self.set_status = set_status
        self.navigate = navigate

        self.managers = {
            "profile": ProfileManager(),
            "skill": SkillManager(),
            "status": StatusManager(),
            "knowledge": KnowledgeManager(),
            "password": PasswordManager(),
            "backup": BackupManager(),
        }

        self._build_header()
        self._build_grid()

    def _build_header(self) -> None:
        header = tk.Frame(self, bg="#fafafa", pady=10)
        header.pack(fill=tk.X, padx=16, pady=(16, 8))

        tk.Label(header, text="数据概览", bg="#fafafa",
                 font=("Microsoft YaHei", 16, "bold")).pack(side=tk.LEFT)
        tk.Label(header, text="点击卡片可跳转到对应模块", bg="#fafafa",
                 font=("Microsoft YaHei", 9), fg="#999999").pack(side=tk.LEFT, padx=12)

    def _build_grid(self) -> None:
        grid = tk.Frame(self, bg="#ffffff", padx=12, pady=8)
        grid.pack(fill=tk.BOTH, expand=True)

        # 一行3列
        for i, card_def in enumerate(self.CARDS):
            row, col = divmod(i, 3)
            card = self._create_card(grid, card_def)
            card.grid(row=row, column=col, sticky=tk.NSEW, padx=6, pady=6)

            grid.columnconfigure(col, weight=1, uniform="card")
        for r in range((len(self.CARDS) + 2) // 3):
            grid.rowconfigure(r, weight=1)

    def _create_card(self, parent: tk.Frame, card_def: dict) -> tk.Frame:
        card = tk.Frame(parent, **self.CARD_STYLE)
        card.bind("<Button-1>", lambda e, name=card_def["navigate"]: self.navigate(name))

        # 图标
        icon_frame = tk.Frame(card, bg="#4a90d9", width=36, height=36)
        icon_frame.pack_propagate(False)
        icon_label = tk.Label(
            icon_frame, text=card_def["icon"],
            bg="#4a90d9", fg="#ffffff",
            font=("Microsoft YaHei", 14, "bold")
        )
        icon_label.pack(expand=True)
        icon_frame.pack(anchor=tk.NW, pady=(0, 8))
        icon_label.bind("<Button-1>", lambda e, name=card_def["navigate"]: self.navigate(name))

        # 标题
        title = tk.Label(
            card, text=card_def["title"],
            bg=self.CARD_STYLE["bg"],
            font=("Microsoft YaHei", 12, "bold")
        )
        title.pack(anchor=tk.W)
        title.bind("<Button-1>", lambda e, name=card_def["navigate"]: self.navigate(name))

        # 数据行
        self.card_data_labels: dict[str, list[tk.Label]] = {}
        lines = card_def["fetch"](self)
        data_labels = []
        for line in lines:
            lbl = tk.Label(
                card, text=line, bg=self.CARD_STYLE["bg"],
                font=("Microsoft YaHei", 9), fg="#555555", anchor=tk.W
            )
            lbl.pack(anchor=tk.W, pady=1)
            lbl.bind("<Button-1>", lambda e, name=card_def["navigate"]: self.navigate(name))
            data_labels.append(lbl)

        self.card_data_labels[card_def["id"]] = data_labels
        return card

    def refresh(self) -> None:
        """刷新所有卡片数据。"""
        for card_def in self.CARDS:
            lines = card_def["fetch"](self)
            labels = self.card_data_labels.get(card_def["id"], [])
            for i, line in enumerate(lines):
                if i < len(labels):
                    labels[i].configure(text=line)

    # ---- 各模块信息获取 ----

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
        cats = ", ".join(f"{k}:{v}" for k, v in s["by_category"].items())
        return parts + [f"涵盖 {len(s['by_category'])} 个类别"] + ([cats] if cats else [])

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
