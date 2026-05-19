"""SkillManager 单元测试。"""

import os
import tempfile
import unittest

import Core.Config as Config
from Core.Exceptions import ValidationError, RecordNotFoundError
from Services.SkillManager import SkillManager


class TestSkillManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.orig_path = Config.SKILL_PATH
        Config.SKILL_PATH = os.path.join(cls.tmpdir, "skills.json")

    @classmethod
    def tearDownClass(cls):
        Config.SKILL_PATH = cls.orig_path
        for f in os.listdir(cls.tmpdir):
            os.unlink(os.path.join(cls.tmpdir, f))
        os.rmdir(cls.tmpdir)

    def setUp(self):
        if os.path.exists(Config.SKILL_PATH):
            os.remove(Config.SKILL_PATH)
        self.manager = SkillManager()

    def test_add_skill(self):
        skill = self.manager.add_skill("Python", "编程语言", 4, 200.0)
        self.assertEqual(skill.name, "Python")
        self.assertEqual(skill.category, "编程语言")
        self.assertEqual(skill.level, 4)
        self.assertEqual(skill.hours_spent, 200.0)

    def test_add_skill_empty_name(self):
        with self.assertRaises(ValidationError):
            self.manager.add_skill("  ", "编程语言", 3, 10)

    def test_add_skill_invalid_level(self):
        with self.assertRaises(ValidationError):
            self.manager.add_skill("Test", "工具", 6, 10)

        with self.assertRaises(ValidationError):
            self.manager.add_skill("Test", "工具", 0, 10)

    def test_add_skill_unknown_category(self):
        skill = self.manager.add_skill("Mystery", "未知类别", 3, 50)
        self.assertEqual(skill.category, "其他")

    def test_get_all_sorted(self):
        self.manager.add_skill("A", "工具", 2, 10)
        self.manager.add_skill("B", "编程语言", 5, 100)
        skills = self.manager.get_all()
        self.assertEqual(skills[0].level, 5)

    def test_get_by_category(self):
        self.manager.add_skill("Python", "编程语言", 4, 200)
        self.manager.add_skill("Vim", "工具", 3, 50)
        results = self.manager.get_by_category("编程语言")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Python")

    def test_search(self):
        self.manager.add_skill("Python编程", "编程语言", 4, 200, "后端开发")
        self.manager.add_skill("Excel", "工具", 3, 30, "办公软件")
        results = self.manager.search("python")
        self.assertEqual(len(results), 1)
        results2 = self.manager.search("办公")
        self.assertEqual(len(results2), 1)

    def test_update_skill(self):
        skill = self.manager.add_skill("Python", "编程语言", 3, 100)
        updated = self.manager.update_skill(skill.id, level=5, hours_spent=150.0)
        self.assertEqual(updated.level, 5)
        self.assertEqual(updated.hours_spent, 150.0)

    def test_update_skill_invalid_level(self):
        skill = self.manager.add_skill("Python", "编程语言", 3, 100)
        with self.assertRaises(ValidationError):
            self.manager.update_skill(skill.id, level=10)

    def test_delete_skill(self):
        skill = self.manager.add_skill("Del", "其他", 1, 1)
        self.assertTrue(self.manager.delete_skill(skill.id))
        self.assertIsNone(self.manager.get_by_id(skill.id))

    def test_statistics(self):
        self.manager.add_skill("A", "编程语言", 4, 100)
        self.manager.add_skill("B", "编程语言", 2, 50)
        self.manager.add_skill("C", "工具", 3, 30)
        stats = self.manager.get_statistics()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["total_hours"], 180.0)
        self.assertEqual(stats["avg_level"], 3.0)
        self.assertEqual(stats["by_category"]["编程语言"], 2)
        self.assertEqual(stats["by_category"]["工具"], 1)

    def test_statistics_empty(self):
        stats = self.manager.get_statistics()
        self.assertEqual(stats["total"], 0)

    def test_get_all_categories(self):
        self.manager.add_skill("A", "编程语言", 3, 10)
        self.manager.add_skill("B", "工具", 3, 10)
        cats = self.manager.get_all_categories()
        self.assertIn("编程语言", cats)
        self.assertIn("工具", cats)


if __name__ == "__main__":
    unittest.main()
