"""习惯管理业务逻辑 — CRUD + 打卡 + 连续统计。"""

from datetime import date, timedelta

import Core.Config as Config
from Core.Exceptions import ValidationError
from Core.Storage import JSONFileStorage
from Models.Habit import Habit
from Models.HabitRecord import HabitRecord


class HabitManager:
    """习惯管理器。"""

    VALID_CATEGORIES = ["健康", "学习", "工作", "生活", "其他"]
    VALID_FREQUENCIES = ["daily", "weekly", "custom"]

    def __init__(self):
        self.habit_storage = JSONFileStorage(Config.HABITS_PATH)
        self.record_storage = JSONFileStorage(Config.HABIT_RECORDS_PATH)

    # ---- 习惯 CRUD ----

    def add_habit(self, name: str, frequency: str = "daily",
                  custom_days: int = 1, target_count: int = 1,
                  category: str = "", description: str = "",
                  color: str = "#4a90d9") -> Habit:
        """创建新习惯。"""
        if not name.strip():
            raise ValidationError("习惯名称不能为空")
        if frequency not in self.VALID_FREQUENCIES:
            raise ValidationError(f"频率类型无效，可选：{self.VALID_FREQUENCIES}")
        if frequency == "custom" and custom_days < 1:
            raise ValidationError("自定义频率天数至少为 1")
        if target_count < 1:
            raise ValidationError("目标次数至少为 1")

        record = {
            "name": name.strip(),
            "description": description.strip(),
            "frequency": frequency,
            "custom_days": custom_days if frequency == "custom" else 1,
            "target_count": target_count,
            "category": category if category in self.VALID_CATEGORIES else "其他",
            "color": color,
            "archived": False,
        }
        saved = self.habit_storage.add(record)
        return Habit.from_dict(saved)

    def get_all(self, include_archived: bool = False) -> list[Habit]:
        habits = [Habit.from_dict(r) for r in self.habit_storage.get_all()]
        if not include_archived:
            habits = [h for h in habits if not h.archived]
        habits.sort(key=lambda h: h.name)
        return habits

    def get_by_id(self, habit_id: str) -> Habit | None:
        record = self.habit_storage.get_by_id(habit_id)
        return Habit.from_dict(record) if record else None

    def get_active(self) -> list[Habit]:
        return self.get_all(include_archived=False)

    def update_habit(self, habit_id: str, **updates) -> Habit:
        if "name" in updates and not updates["name"].strip():
            raise ValidationError("习惯名称不能为空")
        if "frequency" in updates and updates["frequency"] not in self.VALID_FREQUENCIES:
            raise ValidationError(f"频率类型无效")
        if "target_count" in updates and updates["target_count"] < 1:
            raise ValidationError("目标次数至少为 1")
        updated = self.habit_storage.update(habit_id, updates)
        return Habit.from_dict(updated)

    def archive_habit(self, habit_id: str) -> Habit:
        updated = self.habit_storage.update(habit_id, {"archived": True})
        return Habit.from_dict(updated)

    def unarchive_habit(self, habit_id: str) -> Habit:
        updated = self.habit_storage.update(habit_id, {"archived": False})
        return Habit.from_dict(updated)

    def delete_habit(self, habit_id: str, delete_records: bool = True) -> bool:
        if delete_records:
            all_records = self.record_storage.get_all()
            for r in all_records:
                if r.get("habit_id") == habit_id:
                    self.record_storage.delete(r["id"])
        return self.habit_storage.delete(habit_id)

    # ---- 打卡管理 ----

    def check_in(self, habit_id: str, date_str: str | None = None,
                 count: int = 1, note: str = "") -> HabitRecord:
        """打卡。若当天已有记录则更新次数。"""
        habit = self.get_by_id(habit_id)
        if not habit:
            raise ValidationError("习惯不存在")
        if count < 1:
            raise ValidationError("打卡次数至少为 1")

        target_date = date_str or date.today().isoformat()

        existing = self._find_record(habit_id, target_date)
        if existing:
            updated = self.record_storage.update(existing.id, {
                "count": existing.count + count,
                "note": note if note else existing.note,
            })
            return HabitRecord.from_dict(updated)

        record = {
            "habit_id": habit_id,
            "date": target_date,
            "count": count,
            "note": note.strip(),
        }
        saved = self.record_storage.add(record)
        return HabitRecord.from_dict(saved)

    def undo_check_in(self, habit_id: str, date_str: str | None = None) -> bool:
        """撤销打卡。"""
        target_date = date_str or date.today().isoformat()
        existing = self._find_record(habit_id, target_date)
        if existing:
            return self.record_storage.delete(existing.id)
        return False

    def get_records(self, habit_id: str, start_date: str | None = None,
                    end_date: str | None = None) -> list[HabitRecord]:
        records = self.record_storage.query(habit_id=habit_id)
        result = [HabitRecord.from_dict(r) for r in records]
        if start_date:
            result = [r for r in result if r.date >= start_date]
        if end_date:
            result = [r for r in result if r.date <= end_date]
        result.sort(key=lambda r: r.date)
        return result

    def get_record(self, habit_id: str, date_str: str | None = None) -> HabitRecord | None:
        target_date = date_str or date.today().isoformat()
        return self._find_record(habit_id, target_date)

    def is_checked_in(self, habit_id: str, date_str: str | None = None) -> bool:
        return self.get_record(habit_id, date_str) is not None

    def _find_record(self, habit_id: str, date_str: str) -> HabitRecord | None:
        records = self.record_storage.query(habit_id=habit_id, date=date_str)
        return HabitRecord.from_dict(records[0]) if records else None

    # ---- 连续统计 ----

    def get_streak(self, habit_id: str) -> dict:
        """计算习惯的连续打卡统计。"""
        habit = self.get_by_id(habit_id)
        if not habit:
            return {"current": 0, "longest": 0, "total_checkins": 0,
                    "completion_rate": 0.0}

        records = self.get_records(habit_id)
        total = len(records)

        if total == 0:
            return {"current": 0, "longest": 0, "total_checkins": 0,
                    "completion_rate": 0.0}

        current, longest = self._calculate_streak(records, habit.frequency,
                                                   habit.custom_days)
        return {
            "current": current,
            "longest": longest,
            "total_checkins": total,
            "completion_rate": 0.0,  # 需要开始日期计算，暂时保留
        }

    def _calculate_streak(self, records: list[HabitRecord],
                          frequency: str, custom_days: int) -> tuple[int, int]:
        """计算当前连续和最长连续天数。"""
        dates = sorted(set(r.date for r in records))
        if not dates:
            return 0, 0

        today = date.today()
        current_streak = 0
        longest_streak = 0
        temp_streak = 0

        check_date = today
        checked_dates = set(dates)

        # 从今天往回计算当前连续
        while True:
            if self._is_date_covered(check_date, checked_dates, frequency, custom_days):
                current_streak += 1
            else:
                break
            # 根据频率计算上一个周期
            check_date = self._prev_period_start(check_date, frequency, custom_days)
            if current_streak > 366:
                break  # 防止死循环

        # 计算所有时间的最长连续
        sorted_dates = sorted(date.fromisoformat(d) for d in dates)
        check_start = sorted_dates[0]
        period_dates = set()  # 当前周期内的日期
        for d in sorted_dates:
            period_dates.add(d)

        temp = 1
        for i in range(1, len(sorted_dates)):
            curr = sorted_dates[i]
            prev = sorted_dates[i - 1]
            diff = (curr - prev).days

            max_gap = custom_days if frequency == "custom" else (
                7 if frequency == "weekly" else 1
            )
            if diff <= max_gap:
                temp += 1
            else:
                longest_streak = max(longest_streak, temp)
                temp = 1
        longest_streak = max(longest_streak, temp)

        return current_streak, longest_streak

    def _is_date_covered(self, target_date: date, checked_dates: set[str],
                         frequency: str, custom_days: int) -> bool:
        """检查目标日期所在周期是否有打卡。"""
        if frequency == "daily":
            return target_date.isoformat() in checked_dates
        elif frequency == "weekly":
            start = target_date - timedelta(days=target_date.weekday())
            for i in range(7):
                if (start + timedelta(days=i)).isoformat() in checked_dates:
                    return True
            return False
        else:  # custom
            for i in range(custom_days):
                if (target_date - timedelta(days=i)).isoformat() in checked_dates:
                    return True
            return False

    def _prev_period_start(self, current: date, frequency: str,
                           custom_days: int) -> date:
        """返回上一个周期的开始日期。"""
        if frequency == "daily":
            return current - timedelta(days=1)
        elif frequency == "weekly":
            return current - timedelta(weeks=1)
        else:
            return current - timedelta(days=custom_days)

    def get_today_stats(self) -> dict:
        """获取今日打卡统计。"""
        active = self.get_active()
        today_str = date.today().isoformat()
        checked = 0
        for habit in active:
            if self.is_checked_in(habit.id, today_str):
                checked += 1
        return {
            "total_active": len(active),
            "checked_today": checked,
            "completion_rate": (checked / len(active)) if active else 0.0,
        }

    def get_heatmap_data(self, habit_id: str, year: int | None = None) -> dict[str, int]:
        """获取指定习惯的年度打卡热力图数据。"""
        if year is None:
            year = date.today().year
        start = f"{year}-01-01"
        end = f"{year}-12-31"
        records = self.get_records(habit_id, start, end)
        return {r.date: r.count for r in records}

    # ---- 搜索 ----

    def search(self, keyword: str) -> list[Habit]:
        """按名称或描述搜索习惯。"""
        all_h = self.habit_storage.get_all()
        kw = keyword.lower()
        results = [
            r for r in all_h
            if kw in r.get("name", "").lower()
            or kw in r.get("description", "").lower()
        ]
        return [Habit.from_dict(r) for r in results]
