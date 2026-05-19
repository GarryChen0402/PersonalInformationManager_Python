"""状态管理业务逻辑。"""

from datetime import datetime, timedelta

import Core.Config as Config
from Core.Exceptions import ValidationError
from Core.Storage import JSONFileStorage
from Models.Status import StatusRecord


class StatusManager:
    """状态记录管理器。"""

    def __init__(self):
        self.storage = JSONFileStorage(Config.STATUS_PATH)

    # ---- 增 ----

    def add_record(self, date: str, mood: int = 3, energy: int = 3,
                   focus: int = 3, weight: float = 0.0,
                   sleep_hours: float = 0.0, note: str = "") -> StatusRecord:
        """添加状态记录。同一天已有记录则更新。"""
        self._validate_date(date)
        self._validate_scores(mood, energy, focus)

        # 检查是否已有同一天记录
        existing = self.get_by_date(date)
        if existing:
            self.update_record(existing.id,
                               mood=mood, energy=energy, focus=focus,
                               weight=weight, sleep_hours=sleep_hours, note=note)
            return self.get_by_id(existing.id)

        record = {
            "date": date,
            "mood": int(mood),
            "energy": int(energy),
            "focus": int(focus),
            "weight": float(weight),
            "sleep_hours": float(sleep_hours),
            "note": note.strip(),
        }
        saved = self.storage.add(record)
        return StatusRecord.from_dict(saved)

    # ---- 查 ----

    def get_all(self) -> list[StatusRecord]:
        """获取所有记录，按日期倒序。"""
        records = self.storage.get_all()
        records.sort(key=lambda r: r.get("date", ""), reverse=True)
        return [StatusRecord.from_dict(r) for r in records]

    def get_by_id(self, record_id: str) -> StatusRecord | None:
        record = self.storage.get_by_id(record_id)
        return StatusRecord.from_dict(record) if record else None

    def get_by_date(self, date: str) -> StatusRecord | None:
        """按日期查询单条记录。"""
        records = self.storage.query(date=date)
        return StatusRecord.from_dict(records[0]) if records else None

    def get_by_date_range(self, start_date: str, end_date: str) -> list[StatusRecord]:
        """按日期范围筛选。"""
        records = self.storage.get_all()
        results = [
            r for r in records
            if start_date <= r.get("date", "") <= end_date
        ]
        results.sort(key=lambda r: r.get("date", ""), reverse=True)
        return [StatusRecord.from_dict(r) for r in results]

    def get_latest(self, limit: int = 7) -> list[StatusRecord]:
        """获取最近 N 条记录。"""
        all_records = self.get_all()
        return all_records[:limit]

    # ---- 改 ----

    def update_record(self, record_id: str, **updates) -> StatusRecord:
        """更新状态记录（不更新 created_at）。"""
        if "mood" in updates:
            self._validate_scores(updates["mood"])
        if "energy" in updates:
            self._validate_scores(updates["energy"])
        if "focus" in updates:
            self._validate_scores(updates["focus"])

        # 移除 updated_at 以避免设置（状态记录只有 created_at）
        updates.pop("updated_at", None)

        updated = self.storage.update(record_id, updates)
        return StatusRecord.from_dict(updated)

    # ---- 删 ----

    def delete_record(self, record_id: str) -> bool:
        return self.storage.delete(record_id)

    # ---- 统计 ----

    def get_statistics(self, period: str = "week") -> dict:
        """获取指定周期的平均值统计。period: week/month/all"""
        records = self.get_all()
        if not records:
            return {"mood": 0, "energy": 0, "focus": 0, "sleep_hours": 0, "count": 0}

        today = datetime.now().strftime("%Y-%m-%d")

        if period == "week":
            cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            filtered = [r for r in records if r.date >= cutoff]
        elif period == "month":
            cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            filtered = [r for r in records if r.date >= cutoff]
        else:
            filtered = records

        if not filtered:
            return {"mood": 0, "energy": 0, "focus": 0, "sleep_hours": 0, "count": 0}

        n = len(filtered)
        return {
            "mood": round(sum(r.mood for r in filtered) / n, 1),
            "energy": round(sum(r.energy for r in filtered) / n, 1),
            "focus": round(sum(r.focus for r in filtered) / n, 1),
            "sleep_hours": round(sum(r.sleep_hours for r in filtered) / n, 1),
            "count": n,
        }

    # ---- 校验 ----

    @staticmethod
    def _validate_date(date: str) -> None:
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("日期格式错误，请使用 YYYY-MM-DD 格式")

    @staticmethod
    def _validate_scores(*scores: int) -> None:
        for s in scores:
            if s < 1 or s > 5:
                raise ValidationError("评分必须在 1-5 之间")
