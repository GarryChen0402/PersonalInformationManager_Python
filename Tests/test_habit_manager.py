"""HabitManager 单元测试。"""

import unittest
from datetime import date, timedelta

from Tests.test_base import PIMTestCase
from Core.Exceptions import ValidationError
from Services.HabitManager import HabitManager
import Core.Config as Config


class TestHabitManager(PIMTestCase):
    @classmethod
    def _data_paths(cls):
        return {"HABITS_PATH": "habits.json", "HABIT_RECORDS_PATH": "habit_records.json"}

    def setUp(self):
        super().setUp()
        self.manager = HabitManager()

    # ---- 习惯 CRUD ----

    def test_add_habit(self):
        h = self.manager.add_habit("晨跑", frequency="daily", target_count=1,
                                    category="健康")
        self.assertEqual(h.name, "晨跑")
        self.assertEqual(h.frequency, "daily")
        self.assertEqual(h.target_count, 1)
        self.assertEqual(h.category, "健康")
        self.assertFalse(h.archived)

    def test_add_habit_empty_name(self):
        with self.assertRaises(ValidationError):
            self.manager.add_habit("  ", "daily", 1, 1)

    def test_add_habit_invalid_frequency(self):
        with self.assertRaises(ValidationError):
            self.manager.add_habit("Test", "monthly")

    def test_add_habit_custom_days(self):
        h = self.manager.add_habit("每周跑步", frequency="custom", custom_days=3,
                                    target_count=1)
        self.assertEqual(h.frequency, "custom")
        self.assertEqual(h.custom_days, 3)

    def test_add_habit_invalid_target_count(self):
        with self.assertRaises(ValidationError):
            self.manager.add_habit("Test", "daily", 1, 0)

    def test_get_all(self):
        self.manager.add_habit("A", "daily", 1, 1)
        self.manager.add_habit("B", "daily", 1, 1)
        habits = self.manager.get_all()
        self.assertEqual(len(habits), 2)

    def test_get_all_excludes_archived(self):
        h = self.manager.add_habit("A", "daily", 1, 1)
        self.manager.archive_habit(h.id)
        habits = self.manager.get_all()
        self.assertEqual(len(habits), 0)

    def test_get_all_include_archived(self):
        h = self.manager.add_habit("A", "daily", 1, 1)
        self.manager.archive_habit(h.id)
        habits = self.manager.get_all(include_archived=True)
        self.assertEqual(len(habits), 1)

    def test_get_active(self):
        h1 = self.manager.add_habit("A", "daily", 1, 1)
        h2 = self.manager.add_habit("B", "daily", 1, 1)
        self.manager.archive_habit(h1.id)
        active = self.manager.get_active()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].id, h2.id)

    def test_update_habit(self):
        h = self.manager.add_habit("旧名称", "daily", 1, 1)
        updated = self.manager.update_habit(h.id, name="新名称", target_count=3)
        self.assertEqual(updated.name, "新名称")
        self.assertEqual(updated.target_count, 3)

    def test_update_habit_empty_name(self):
        h = self.manager.add_habit("Test", "daily", 1, 1)
        with self.assertRaises(ValidationError):
            self.manager.update_habit(h.id, name="  ")

    def test_archive_unarchive(self):
        h = self.manager.add_habit("Test", "daily", 1, 1)
        self.assertFalse(h.archived)

        archived = self.manager.archive_habit(h.id)
        self.assertTrue(archived.archived)

        unarchived = self.manager.unarchive_habit(h.id)
        self.assertFalse(unarchived.archived)

    def test_delete_habit_with_records(self):
        h = self.manager.add_habit("Test", "daily", 1, 1)
        self.manager.check_in(h.id)
        self.assertTrue(self.manager.delete_habit(h.id))
        self.assertIsNone(self.manager.get_by_id(h.id))

        # 关联的打卡记录也应被删除
        records = self.manager.get_records(h.id)
        self.assertEqual(len(records), 0)

    # ---- 打卡 ----

    def test_check_in(self):
        h = self.manager.add_habit("晨跑", "daily", 1, 1)
        today = date.today().isoformat()
        record = self.manager.check_in(h.id, today)
        self.assertEqual(record.habit_id, h.id)
        self.assertEqual(record.date, today)
        self.assertEqual(record.count, 1)

    def test_check_in_twice_same_day(self):
        h = self.manager.add_habit("晨跑", "daily", 1, 1)
        today = date.today().isoformat()
        self.manager.check_in(h.id, today, count=1)
        record = self.manager.check_in(h.id, today, count=1)
        self.assertEqual(record.count, 2)  # 累加

    def test_undo_check_in(self):
        h = self.manager.add_habit("晨跑", "daily", 1, 1)
        today = date.today().isoformat()
        self.manager.check_in(h.id, today)
        self.assertTrue(self.manager.is_checked_in(h.id, today))
        self.manager.undo_check_in(h.id, today)
        self.assertFalse(self.manager.is_checked_in(h.id, today))

    def test_undo_nonexistent(self):
        h = self.manager.add_habit("晨跑", "daily", 1, 1)
        self.assertFalse(self.manager.undo_check_in(h.id))

    def test_is_checked_in(self):
        h = self.manager.add_habit("晨跑", "daily", 1, 1)
        self.assertFalse(self.manager.is_checked_in(h.id))
        self.manager.check_in(h.id)
        self.assertTrue(self.manager.is_checked_in(h.id))

    def test_get_records_date_range(self):
        h = self.manager.add_habit("晨跑", "daily", 1, 1)
        dates = [(date.today() - timedelta(days=i)).isoformat() for i in range(5)]
        for d in dates:
            self.manager.check_in(h.id, d)

        records = self.manager.get_records(h.id, start_date=dates[2], end_date=dates[1])
        self.assertGreaterEqual(len(records), 1)

    # ---- 连续统计 ----

    def test_get_streak_empty(self):
        h = self.manager.add_habit("晨跑", "daily", 1, 1)
        streak = self.manager.get_streak(h.id)
        self.assertEqual(streak["current"], 0)
        self.assertEqual(streak["longest"], 0)

    def test_get_streak_today(self):
        h = self.manager.add_habit("晨跑", "daily", 1, 1)
        self.manager.check_in(h.id)
        streak = self.manager.get_streak(h.id)
        self.assertEqual(streak["current"], 1)
        self.assertEqual(streak["longest"], 1)

    def test_get_streak_consecutive_days(self):
        h = self.manager.add_habit("晨跑", "daily", 1, 1)
        for i in range(3):
            d = (date.today() - timedelta(days=i)).isoformat()
            self.manager.check_in(h.id, d)
        streak = self.manager.get_streak(h.id)
        self.assertEqual(streak["current"], 3)
        self.assertGreaterEqual(streak["longest"], 3)

    def test_get_streak_with_gap(self):
        """中间断了一天，当前连续只有今天。"""
        h = self.manager.add_habit("晨跑", "daily", 1, 1)
        today = date.today().isoformat()
        two_days_ago = (date.today() - timedelta(days=2)).isoformat()
        self.manager.check_in(h.id, two_days_ago)
        self.manager.check_in(h.id, today)
        streak = self.manager.get_streak(h.id)
        self.assertEqual(streak["current"], 1)  # 昨天没打卡，连续断了

    # ---- 今日统计 ----

    def test_get_today_stats(self):
        h1 = self.manager.add_habit("A", "daily", 1, 1)
        h2 = self.manager.add_habit("B", "daily", 1, 1)
        self.manager.check_in(h1.id)
        stats = self.manager.get_today_stats()
        self.assertEqual(stats["total_active"], 2)
        self.assertEqual(stats["checked_today"], 1)
        self.assertAlmostEqual(stats["completion_rate"], 0.5)

    def test_get_today_stats_empty(self):
        stats = self.manager.get_today_stats()
        self.assertEqual(stats["total_active"], 0)
        self.assertEqual(stats["checked_today"], 0)
        self.assertEqual(stats["completion_rate"], 0.0)

    # ---- 搜索 ----

    def test_search_by_name(self):
        self.manager.add_habit("晨跑", "daily", 1, 1)
        self.manager.add_habit("阅读", "daily", 1, 1)
        results = self.manager.search("晨跑")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "晨跑")

    def test_search_by_description(self):
        self.manager.add_habit("晨跑", "daily", 1, 1, description="每天早上跑步")
        results = self.manager.search("跑步")
        self.assertEqual(len(results), 1)

    def test_search_no_match(self):
        self.manager.add_habit("晨跑", "daily", 1, 1)
        results = self.manager.search("不存在的习惯")
        self.assertEqual(len(results), 0)

    # ---- 热力图数据 ----

    def test_get_heatmap_data(self):
        h = self.manager.add_habit("晨跑", "daily", 1, 1)
        today = date.today().isoformat()
        self.manager.check_in(h.id, today)
        data = self.manager.get_heatmap_data(h.id)
        self.assertIn(today, data)
        self.assertEqual(data[today], 1)
