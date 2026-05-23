"""所有 @dataclass 模型序列化/反序列化测试。"""

import unittest
from datetime import date, timedelta

from Models.Profile import Profile
from Models.Skill import Skill
from Models.Status import StatusRecord
from Models.Knowledge import KnowledgeItem
from Models.Password import PasswordEntry
from Models.TodoItem import TodoItem
from Models.AppConfig import AppConfig


class TestProfileModel(unittest.TestCase):
    def test_default_values(self):
        p = Profile()
        self.assertEqual(p.name, "")
        self.assertEqual(p.gender, "")

    def test_from_dict_partial(self):
        p = Profile.from_dict({"name": "Alice", "phone": "12345"})
        self.assertEqual(p.name, "Alice")
        self.assertEqual(p.phone, "12345")
        self.assertEqual(p.email, "")  # 默认值

    def test_from_dict_unknown_fields(self):
        p = Profile.from_dict({"name": "Bob", "unknown_field": "ignored"})
        self.assertEqual(p.name, "Bob")
        self.assertFalse(hasattr(p, "unknown_field"))

    def test_to_dict_roundtrip(self):
        p = Profile(name="Test", phone="123", email="a@b.com")
        d = p.to_dict()
        p2 = Profile.from_dict(d)
        self.assertEqual(p2.name, "Test")
        self.assertEqual(p2.phone, "123")
        self.assertEqual(p2.email, "a@b.com")


class TestSkillModel(unittest.TestCase):
    def test_default_values(self):
        s = Skill()
        self.assertEqual(s.level, 1)
        self.assertEqual(s.hours_spent, 0.0)

    def test_from_dict_to_dict(self):
        s = Skill.from_dict({"id": "abc", "name": "Python", "level": 4,
                             "hours_spent": 200.0, "category": "programming"})
        self.assertEqual(s.id, "abc")
        self.assertEqual(s.name, "Python")
        self.assertEqual(s.level, 4)
        self.assertEqual(s.hours_spent, 200.0)

        d = s.to_dict()
        self.assertEqual(d["name"], "Python")
        self.assertEqual(d["level"], 4)


class TestStatusRecordModel(unittest.TestCase):
    def test_default_values(self):
        s = StatusRecord()
        self.assertEqual(s.mood, 3)
        self.assertEqual(s.energy, 3)
        self.assertEqual(s.focus, 3)

    def test_from_dict(self):
        s = StatusRecord.from_dict({
            "date": "2026-05-23", "mood": 5, "energy": 4, "focus": 3,
            "weight": 70.5, "sleep_hours": 7.5, "note": "good day",
        })
        self.assertEqual(s.date, "2026-05-23")
        self.assertEqual(s.mood, 5)
        self.assertEqual(s.weight, 70.5)
        self.assertEqual(s.note, "good day")


class TestKnowledgeModel(unittest.TestCase):
    def test_default_values(self):
        k = KnowledgeItem()
        self.assertEqual(k.item_type, "note")
        self.assertEqual(k.keywords, [])

    def test_from_dict_keywords_not_list(self):
        k = KnowledgeItem.from_dict({"title": "Test", "keywords": "not_a_list"})
        self.assertEqual(k.keywords, [])

    def test_from_dict_keywords_list(self):
        k = KnowledgeItem.from_dict({"title": "Test", "keywords": ["Python", "AI"]})
        self.assertEqual(k.keywords, ["Python", "AI"])

    def test_ebook_defaults(self):
        k = KnowledgeItem.from_dict({"item_type": "ebook", "title": "Book",
                                      "file_path": "books/abc.pdf", "file_size": 1024})
        self.assertEqual(k.item_type, "ebook")
        self.assertEqual(k.file_path, "books/abc.pdf")
        self.assertEqual(k.file_size, 1024)


class TestPasswordEntryModel(unittest.TestCase):
    def test_default_values(self):
        p = PasswordEntry()
        self.assertEqual(p.platform, "")

    def test_from_dict(self):
        p = PasswordEntry.from_dict({
            "platform": "GitHub", "url": "https://github.com",
            "username": "user", "password": "v2:encrypted_data",
        })
        self.assertEqual(p.platform, "GitHub")
        self.assertEqual(p.username, "user")
        self.assertTrue(p.password.startswith("v2:"))


class TestTodoItemModel(unittest.TestCase):
    def test_default_values(self):
        t = TodoItem()
        self.assertEqual(t.priority, "mid")
        self.assertFalse(t.completed)

    def test_is_overdue_past_date(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        t = TodoItem(due_date=yesterday, completed=False)
        self.assertTrue(t.is_overdue())

    def test_is_overdue_today(self):
        today = date.today().isoformat()
        t = TodoItem(due_date=today, completed=False)
        self.assertFalse(t.is_overdue())

    def test_is_overdue_future(self):
        future = (date.today() + timedelta(days=7)).isoformat()
        t = TodoItem(due_date=future, completed=False)
        self.assertFalse(t.is_overdue())

    def test_is_overdue_completed(self):
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        t = TodoItem(due_date=yesterday, completed=True)
        self.assertFalse(t.is_overdue())

    def test_is_overdue_no_due_date(self):
        t = TodoItem(due_date="", completed=False)
        self.assertFalse(t.is_overdue())

    def test_is_overdue_invalid_date(self):
        t = TodoItem(due_date="not-a-date", completed=False)
        self.assertFalse(t.is_overdue())

    def test_from_dict(self):
        t = TodoItem.from_dict({
            "title": "Test Todo", "priority": "high",
            "due_date": "2026-06-01", "completed": False,
        })
        self.assertEqual(t.title, "Test Todo")
        self.assertEqual(t.priority, "high")
        self.assertFalse(t.completed)


class TestAppConfigModel(unittest.TestCase):
    def test_default_values(self):
        c = AppConfig()
        self.assertEqual(c.theme, "light")
        self.assertEqual(c.font_size, 10)
        self.assertEqual(c.search_history, [])

    def test_from_dict_search_history_not_list(self):
        c = AppConfig.from_dict({"search_history": "invalid"})
        self.assertEqual(c.search_history, [])

    def test_from_dict(self):
        c = AppConfig.from_dict({
            "theme": "dark", "font_size": 12,
            "search_history": ["Python", "Java"],
            "last_active_module": "todo",
        })
        self.assertEqual(c.theme, "dark")
        self.assertEqual(c.font_size, 12)
        self.assertEqual(c.search_history, ["Python", "Java"])
        self.assertEqual(c.last_active_module, "todo")
