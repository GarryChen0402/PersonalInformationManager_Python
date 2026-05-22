"""全局搜索集成测试。"""

import os
import tempfile
import unittest

import Core.Config as Config
from Services.SkillManager import SkillManager
from Services.TodoManager import TodoManager
from Services.PasswordManager import PasswordManager
from Services.KnowledgeManager import KnowledgeManager
from Services.CryptoService import CryptoService


class TestGlobalSearch(unittest.TestCase):
    """跨模块搜索能力测试。"""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.orig_skill = Config.SKILL_PATH
        cls.orig_todo = Config.TODO_PATH
        cls.orig_password = Config.PASSWORD_PATH
        cls.orig_knowledge = Config.KNOWLEDGE_PATH
        cls.orig_config = Config.CONFIG_PATH
        Config.SKILL_PATH = os.path.join(cls.tmpdir, "skills.json")
        Config.TODO_PATH = os.path.join(cls.tmpdir, "todos.json")
        Config.PASSWORD_PATH = os.path.join(cls.tmpdir, "passwords.json")
        Config.KNOWLEDGE_PATH = os.path.join(cls.tmpdir, "knowledge.json")
        Config.CONFIG_PATH = os.path.join(cls.tmpdir, "config.json")

    @classmethod
    def tearDownClass(cls):
        Config.SKILL_PATH = cls.orig_skill
        Config.TODO_PATH = cls.orig_todo
        Config.PASSWORD_PATH = cls.orig_password
        Config.KNOWLEDGE_PATH = cls.orig_knowledge
        Config.CONFIG_PATH = cls.orig_config
        CryptoService.lock()
        for f in os.listdir(cls.tmpdir):
            os.unlink(os.path.join(cls.tmpdir, f))
        os.rmdir(cls.tmpdir)

    def setUp(self):
        CryptoService.lock()
        for p in [Config.SKILL_PATH, Config.TODO_PATH, Config.PASSWORD_PATH,
                  Config.KNOWLEDGE_PATH, Config.CONFIG_PATH]:
            if os.path.exists(p):
                os.remove(p)
        CryptoService.setup_master_password("testpass", "testpass")
        self.skill_mgr = SkillManager()
        self.todo_mgr = TodoManager()
        self.password_mgr = PasswordManager()
        self.knowledge_mgr = KnowledgeManager()

    # ---- Skill 搜索 ----

    def test_skill_search_name(self):
        self.skill_mgr.add_skill("Python编程", "编程语言", 4, 200)
        results = self.skill_mgr.search("Python")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].name, "Python编程")

    def test_skill_search_description(self):
        self.skill_mgr.add_skill("Python", "编程语言", 4, 200, description="后端开发和数据分析")
        results = self.skill_mgr.search("数据分析")
        self.assertEqual(len(results), 1)

    def test_skill_search_no_match(self):
        self.skill_mgr.add_skill("Python", "编程语言", 4, 200)
        results = self.skill_mgr.search("Java")
        self.assertEqual(len(results), 0)

    # ---- Todo 搜索 ----

    def test_todo_search_title(self):
        self.todo_mgr.add_todo("买菜做饭")
        results = self.todo_mgr.search("买菜")
        self.assertEqual(len(results), 1)

    def test_todo_search_description(self):
        self.todo_mgr.add_todo("购物", description="去超市买菜")
        results = self.todo_mgr.search("超市")
        self.assertEqual(len(results), 1)

    def test_todo_search_case_insensitive(self):
        self.todo_mgr.add_todo("Python学习")
        results = self.todo_mgr.search("python")
        self.assertEqual(len(results), 1)

    # ---- Knowledge 搜索 ----

    def test_knowledge_search_note(self):
        self.knowledge_mgr.create_note(
            title="Python学习笔记", category="技术", keywords=["Python"],
            content="类和对象的使用方法"
        )
        results = self.knowledge_mgr.search("Python")
        self.assertEqual(len(results), 1)

    def test_knowledge_search_content(self):
        self.knowledge_mgr.create_note(
            title="杂记", category="其他", keywords=["设计"],
            content="今天学习了设计模式"
        )
        results = self.knowledge_mgr.search("设计模式")
        self.assertEqual(len(results), 1)

    # ---- Password 搜索 ----

    def test_password_search_platform(self):
        self.password_mgr.add_entry(
            platform="GitHub", url="https://github.com", username="user1",
            password="pass123", note="代码托管"
        )
        results = self.password_mgr.search("GitHub")
        self.assertEqual(len(results), 1)

    def test_password_search_url(self):
        self.password_mgr.add_entry(
            platform="GitLab", url="https://gitlab.com", username="user1",
            password="pass123"
        )
        results = self.password_mgr.search("gitlab")
        self.assertEqual(len(results), 1)

    def test_password_search_username(self):
        self.password_mgr.add_entry(
            platform="Unknown", url="", username="admin_user",
            password="pass123"
        )
        results = self.password_mgr.search("admin")
        self.assertEqual(len(results), 1)

    # ---- 跨模块搜索 ----

    def test_search_across_modules(self):
        """模拟 App._do_global_search 的跨模块搜索逻辑。"""
        self.skill_mgr.add_skill("Python", "编程语言", 4, 200, "编程技能")
        self.todo_mgr.add_todo("学习Python", description="完成Python课程")
        self.knowledge_mgr.create_note(
            title="Python笔记", category="技术", keywords=["Python"],
            content="语言的特性"
        )

        kw = "Python"
        all_results: list[str] = []

        for s in self.skill_mgr.search(kw):
            all_results.append(f"skill:{s.name}")
        for t in self.todo_mgr.search(kw):
            all_results.append(f"todo:{t.title}")
        for k in self.knowledge_mgr.search(kw):
            all_results.append(f"knowledge:{k.title}")

        self.assertEqual(len(all_results), 3)
        self.assertIn("skill:Python", all_results)
        self.assertIn("todo:学习Python", all_results)
        self.assertIn("knowledge:Python笔记", all_results)

    def test_search_no_cross_contamination(self):
        """验证各模块搜索互不干扰。"""
        self.skill_mgr.add_skill("Java", "编程语言", 3, 100)
        self.todo_mgr.add_todo("买菜", description="超市")

        skill_results = self.skill_mgr.search("买菜")
        self.assertEqual(len(skill_results), 0)

        todo_results = self.todo_mgr.search("Java")
        self.assertEqual(len(todo_results), 0)

    # ---- 去重搜索 ----

    def test_unicode_search(self):
        """验证中文搜索能力。"""
        self.skill_mgr.add_skill("机器学习", "AI", 4, 300, "人工智能领域")
        self.todo_mgr.add_todo("完成机器学习作业")

        skill_hits = self.skill_mgr.search("机器学习")
        todo_hits = self.todo_mgr.search("机器学习")
        self.assertEqual(len(skill_hits), 1)
        self.assertEqual(len(todo_hits), 1)


if __name__ == "__main__":
    unittest.main()
