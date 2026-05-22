"""TodoManager 单元测试。"""

import os
import tempfile
import unittest
from datetime import datetime, timedelta

import Core.Config as Config
from Core.Exceptions import ValidationError
from Services.TodoManager import TodoManager


class TestTodoManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.orig_path = Config.TODO_PATH
        Config.TODO_PATH = os.path.join(cls.tmpdir, "todos.json")

    @classmethod
    def tearDownClass(cls):
        Config.TODO_PATH = cls.orig_path
        for f in os.listdir(cls.tmpdir):
            os.unlink(os.path.join(cls.tmpdir, f))
        os.rmdir(cls.tmpdir)

    def setUp(self):
        if os.path.exists(Config.TODO_PATH):
            os.remove(Config.TODO_PATH)
        self.manager = TodoManager()

    # ---- 增 ----

    def test_add_todo(self):
        todo = self.manager.add_todo("买菜", priority="high", category="生活")
        self.assertEqual(todo.title, "买菜")
        self.assertEqual(todo.priority, "high")
        self.assertEqual(todo.category, "生活")
        self.assertFalse(todo.completed)
        self.assertIsNotNone(todo.id)

    def test_add_todo_empty_title(self):
        with self.assertRaises(ValidationError):
            self.manager.add_todo("  ")

    def test_add_todo_invalid_priority(self):
        with self.assertRaises(ValidationError):
            self.manager.add_todo("Test", priority="urgent")

    def test_add_todo_invalid_due_date(self):
        with self.assertRaises(ValidationError):
            self.manager.add_todo("Test", due_date="2025-13-01")

    def test_add_todo_valid_due_date(self):
        todo = self.manager.add_todo("Test", due_date="2025-12-31")
        self.assertEqual(todo.due_date, "2025-12-31")

    def test_add_todo_unknown_category(self):
        todo = self.manager.add_todo("Test", category="未知类别")
        self.assertEqual(todo.category, "")

    # ---- 查 ----

    def test_get_all_sorted(self):
        self.manager.add_todo("C", priority="low")
        self.manager.add_todo("A", priority="high")
        self.manager.add_todo("B", priority="mid")
        items = self.manager.get_all()
        self.assertEqual(len(items), 3)
        # high priority first
        self.assertEqual(items[0].title, "A")

    def test_filter_active(self):
        self.manager.add_todo("A")
        t = self.manager.add_todo("B")
        self.manager.toggle_complete(t.id)
        active = self.manager.get_all(status="active")
        self.assertEqual(len(active), 1)

    def test_filter_completed(self):
        t = self.manager.add_todo("A")
        self.manager.toggle_complete(t.id)
        completed = self.manager.get_all(status="completed")
        self.assertEqual(len(completed), 1)

    def test_get_by_category(self):
        self.manager.add_todo("A", category="工作")
        self.manager.add_todo("B", category="生活")
        results = self.manager.get_by_category("工作")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "A")

    def test_search(self):
        self.manager.add_todo("买菜做饭", description="去超市")
        self.manager.add_todo("写代码", description="Python项目")
        results = self.manager.search("买菜")
        self.assertEqual(len(results), 1)
        results2 = self.manager.search("超市")
        self.assertEqual(len(results2), 1)

    # ---- 改 ----

    def test_update_todo(self):
        todo = self.manager.add_todo("A", priority="low")
        updated = self.manager.update_todo(todo.id, title="AAA", priority="high")
        self.assertEqual(updated.title, "AAA")
        self.assertEqual(updated.priority, "high")

    def test_update_todo_empty_title(self):
        todo = self.manager.add_todo("A")
        with self.assertRaises(ValidationError):
            self.manager.update_todo(todo.id, title="  ")

    def test_update_todo_invalid_priority(self):
        todo = self.manager.add_todo("A")
        with self.assertRaises(ValidationError):
            self.manager.update_todo(todo.id, priority="urgent")

    def test_toggle_complete(self):
        todo = self.manager.add_todo("A")
        toggled = self.manager.toggle_complete(todo.id)
        self.assertTrue(toggled.completed)
        self.assertNotEqual(toggled.completed_at, "")

        # toggle back
        toggled2 = self.manager.toggle_complete(todo.id)
        self.assertFalse(toggled2.completed)

    def test_toggle_nonexistent(self):
        with self.assertRaises(ValidationError):
            self.manager.toggle_complete("nonexistent-id")

    # ---- 删 ----

    def test_delete_todo(self):
        todo = self.manager.add_todo("Del")
        self.assertTrue(self.manager.delete_todo(todo.id))
        self.assertIsNone(self.manager.get_by_id(todo.id))

    def test_batch_delete_completed(self):
        t1 = self.manager.add_todo("A")
        t2 = self.manager.add_todo("B")
        self.manager.toggle_complete(t1.id)
        count = self.manager.batch_delete_completed()
        self.assertEqual(count, 1)
        self.assertIsNone(self.manager.get_by_id(t1.id))
        self.assertIsNotNone(self.manager.get_by_id(t2.id))

    # ---- 统计 ----

    def test_statistics(self):
        t = self.manager.add_todo("A")
        self.manager.toggle_complete(t.id)
        self.manager.add_todo("B")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.manager.add_todo("C", due_date=yesterday)

        stats = self.manager.get_statistics()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["completed"], 1)
        self.assertEqual(stats["active"], 2)
        self.assertEqual(stats["overdue"], 1)

    def test_statistics_empty(self):
        stats = self.manager.get_statistics()
        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["overdue"], 0)

    # ---- 逾期 ----

    def test_get_overdue(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        self.manager.add_todo("Overdue", due_date=yesterday)
        self.manager.add_todo("Future", due_date=tomorrow)
        overdue = self.manager.get_overdue()
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0].title, "Overdue")

    def test_completed_not_overdue(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        t = self.manager.add_todo("Done", due_date=yesterday)
        self.manager.toggle_complete(t.id)
        overdue = self.manager.get_overdue()
        self.assertEqual(len(overdue), 0)

    # ---- CSV ----

    def test_export_csv(self):
        self.manager.add_todo("A", description="desc", priority="high",
                             category="工作", due_date="2025-06-01")
        csv_path = os.path.join(self.tmpdir, "todos_export.csv")
        self.manager.export_csv(csv_path)
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            content = f.read()
            self.assertIn("A", content)
            self.assertIn("high", content)

    def test_import_csv(self):
        csv_path = os.path.join(self.tmpdir, "todos_import.csv")
        with open(csv_path, "w", encoding="utf-8-sig") as f:
            f.write("标题,描述,优先级,类别,截止日期,完成,创建时间\n")
            f.write("任务1,描述1,high,工作,2025-06-01,否,\n")
            f.write("任务2,描述2,mid,生活,,是,\n")
        result = self.manager.import_csv(csv_path)
        self.assertEqual(result["success"], 2)
        self.assertEqual(result["failed"], 0)

    def test_import_csv_skip_invalid(self):
        csv_path = os.path.join(self.tmpdir, "todos_import_invalid.csv")
        with open(csv_path, "w", encoding="utf-8-sig") as f:
            f.write("标题,描述,优先级,类别,截止日期,完成,创建时间\n")
            f.write(",empty title,mid,工作,,,\n")
            f.write("有效任务,desc,mid,工作,,,\n")
        result = self.manager.import_csv(csv_path)
        self.assertEqual(result["success"], 1)
        self.assertEqual(result["failed"], 1)

    # ---- 排序 ----

    def test_sort_overdue_first(self):
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        self.manager.add_todo("A", priority="low")
        self.manager.add_todo("B", priority="low", due_date=yesterday)
        items = self.manager.get_all()
        self.assertEqual(items[0].title, "B")  # overdue first

    def test_sort_priority_within_same_status(self):
        self.manager.add_todo("Low", priority="low")
        self.manager.add_todo("High", priority="high")
        items = self.manager.get_all()
        self.assertEqual(items[0].title, "High")


if __name__ == "__main__":
    unittest.main()
