"""StatusManager 单元测试。"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta

import Core.Config as Config
from Core.Exceptions import ValidationError
from Services.StatusManager import StatusManager


class TestStatusManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.orig_path = Config.STATUS_PATH
        Config.STATUS_PATH = os.path.join(cls.tmpdir, "status.json")

    @classmethod
    def tearDownClass(cls):
        Config.STATUS_PATH = cls.orig_path
        for f in os.listdir(cls.tmpdir):
            os.unlink(os.path.join(cls.tmpdir, f))
        os.rmdir(cls.tmpdir)

    def setUp(self):
        if os.path.exists(Config.STATUS_PATH):
            os.remove(Config.STATUS_PATH)
        self.manager = StatusManager()

    def test_add_record(self):
        record = self.manager.add_record("2026-05-19", mood=4, energy=3)
        self.assertEqual(record.mood, 4)
        self.assertEqual(record.energy, 3)
        self.assertEqual(record.date, "2026-05-19")

    def test_add_record_same_day_updates(self):
        r1 = self.manager.add_record("2026-05-19", mood=2, energy=2, focus=2)
        r2 = self.manager.add_record("2026-05-19", mood=5, energy=5, focus=5)
        self.assertEqual(r1.id, r2.id)
        self.assertEqual(r2.mood, 5)

    def test_invalid_date(self):
        with self.assertRaises(ValidationError):
            self.manager.add_record("19-05-2026", mood=3)

    def test_invalid_scores(self):
        with self.assertRaises(ValidationError):
            self.manager.add_record("2026-05-19", mood=6)
        with self.assertRaises(ValidationError):
            self.manager.add_record("2026-05-19", energy=0)

    def test_get_by_date(self):
        self.manager.add_record("2026-05-15", mood=4)
        record = self.manager.get_by_date("2026-05-15")
        self.assertEqual(record.mood, 4)

    def test_get_by_date_range(self):
        self.manager.add_record("2026-05-01", mood=2)
        self.manager.add_record("2026-05-10", mood=3)
        self.manager.add_record("2026-05-20", mood=4)
        results = self.manager.get_by_date_range("2026-05-05", "2026-05-15")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].mood, 3)

    def test_get_latest(self):
        for i in range(10):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            self.manager.add_record(date, mood=3)
        latest = self.manager.get_latest(limit=5)
        self.assertEqual(len(latest), 5)

    def test_update_record(self):
        record = self.manager.add_record("2026-05-19", mood=3, energy=3, focus=3)
        updated = self.manager.update_record(record.id, mood=5)
        self.assertEqual(updated.mood, 5)
        # energy and focus should be unchanged
        self.assertEqual(updated.energy, 3)
        self.assertEqual(updated.focus, 3)

    def test_update_record_invalid_scores(self):
        record = self.manager.add_record("2026-05-19", mood=3)
        with self.assertRaises(ValidationError):
            self.manager.update_record(record.id, energy=0)

    def test_delete_record(self):
        record = self.manager.add_record("2026-05-19", mood=3)
        self.assertTrue(self.manager.delete_record(record.id))

    def test_statistics_week(self):
        today = datetime.now().strftime("%Y-%m-%d")
        self.manager.add_record(today, mood=4, energy=3, focus=5, sleep_hours=7.0)
        stats = self.manager.get_statistics(period="week")
        self.assertEqual(stats["count"], 1)
        self.assertEqual(stats["mood"], 4.0)

    def test_statistics_empty(self):
        stats = self.manager.get_statistics()
        self.assertEqual(stats["count"], 0)

    def test_statistics_all(self):
        self.manager.add_record("2026-05-10", mood=2, energy=2, focus=2, sleep_hours=6.0)
        self.manager.add_record("2026-05-11", mood=4, energy=4, focus=4, sleep_hours=8.0)
        stats = self.manager.get_statistics(period="all")
        self.assertEqual(stats["count"], 2)
        self.assertEqual(stats["mood"], 3.0)
        self.assertEqual(stats["sleep_hours"], 7.0)


if __name__ == "__main__":
    unittest.main()
