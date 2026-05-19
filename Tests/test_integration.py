"""全功能集成测试。"""

import json
import os
import shutil
import sys
import tempfile
import unittest

# 重定向数据目录到临时位置
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import Core.Config as Config


class TestIntegration(unittest.TestCase):
    """端到端集成测试，使用临时数据目录。"""

    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls._orig = {
            "DATA_DIR": Config.DATA_DIR,
            "BOOKS_DIR": Config.BOOKS_DIR,
            "BACKUP_DIR": Config.BACKUP_DIR,
            "PROFILE_PATH": Config.PROFILE_PATH,
            "SKILL_PATH": Config.SKILL_PATH,
            "STATUS_PATH": Config.STATUS_PATH,
            "KNOWLEDGE_PATH": Config.KNOWLEDGE_PATH,
            "PASSWORD_PATH": Config.PASSWORD_PATH,
        }
        Config.DATA_DIR = os.path.join(cls.tmpdir, "Data")
        Config.BOOKS_DIR = os.path.join(Config.DATA_DIR, "books")
        Config.BACKUP_DIR = os.path.join(Config.DATA_DIR, "backups")
        Config.PROFILE_PATH = os.path.join(Config.DATA_DIR, "profile.json")
        Config.SKILL_PATH = os.path.join(Config.DATA_DIR, "skills.json")
        Config.STATUS_PATH = os.path.join(Config.DATA_DIR, "status.json")
        Config.KNOWLEDGE_PATH = os.path.join(Config.DATA_DIR, "knowledge.json")
        Config.PASSWORD_PATH = os.path.join(Config.DATA_DIR, "passwords.json")

    @classmethod
    def tearDownClass(cls):
        for k, v in cls._orig.items():
            setattr(Config, k, v)
        shutil.rmtree(cls.tmpdir, ignore_errors=True)

    def setUp(self):
        # 清理旧数据
        for p in [Config.PROFILE_PATH, Config.SKILL_PATH, Config.STATUS_PATH,
                   Config.KNOWLEDGE_PATH, Config.PASSWORD_PATH]:
            if os.path.exists(p):
                os.remove(p)
        for d in [Config.BOOKS_DIR, Config.BACKUP_DIR]:
            if os.path.exists(d):
                shutil.rmtree(d, ignore_errors=True)

    # ==== 1. 自动初始化 ====

    def test_auto_init_directories(self):
        """验证 ensure_directories 自动创建所需目录。"""
        self.assertFalse(os.path.exists(Config.BOOKS_DIR))
        self.assertFalse(os.path.exists(Config.BACKUP_DIR))

        Config.ensure_directories()

        self.assertTrue(os.path.exists(Config.BOOKS_DIR))
        self.assertTrue(os.path.exists(Config.BACKUP_DIR))

    def test_storage_auto_creates_files(self):
        """验证 JSONFileStorage 首次使用时自动创建空文件。"""
        self.assertFalse(os.path.exists(Config.SKILL_PATH))

        from Core.Storage import JSONFileStorage
        storage = JSONFileStorage(Config.SKILL_PATH)
        self.assertTrue(os.path.exists(Config.SKILL_PATH))
        self.assertEqual(storage.get_all(), [])

    # ==== 2. 完整 CRUD 流程 ====

    def test_profile_lifecycle(self):
        """档案：创建 → 更新 → 查询 → 导出。"""
        from Services.ProfileManager import ProfileManager

        pm = ProfileManager()

        # 空档案
        p = pm.get_profile()
        self.assertEqual(p.name, "")

        # 更新
        p = pm.update_profile(name="集成测试", gender="男",
                               phone="13900001111", email="test@test.com")
        self.assertEqual(p.name, "集成测试")
        self.assertIsNotNone(p.updated_at)

        # 统计
        s = pm.get_summary()
        self.assertGreater(s["filled"], 0)

        # 导出
        export_path = os.path.join(self.tmpdir, "profile_export.json")
        pm.export_profile(export_path)
        with open(export_path, "r", encoding="utf-8") as f:
            exported = json.load(f)
        self.assertEqual(exported["name"], "集成测试")

    def test_skill_lifecycle(self):
        """技能：添加 → 搜索 → 统计 → 更新 → 删除。"""
        from Services.SkillManager import SkillManager

        sm = SkillManager()

        # 添加
        s1 = sm.add_skill("Python", "编程语言", 4, 300, "数据分析")
        s2 = sm.add_skill("Git", "工具", 3, 100)
        s3 = sm.add_skill("English", "语言", 2, 200)

        self.assertIsNotNone(s1.id)
        self.assertEqual(len(sm.get_all()), 3)

        # 搜索
        results = sm.search("python")
        self.assertEqual(len(results), 1)

        # 统计
        stats = sm.get_statistics()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["total_hours"], 600.0)

        # 更新
        updated = sm.update_skill(s1.id, level=5)
        self.assertEqual(updated.level, 5)

        # 删除
        self.assertTrue(sm.delete_skill(s3.id))
        self.assertEqual(len(sm.get_all()), 2)

    def test_status_lifecycle(self):
        """状态：增/同天更新 → 范围查询 → 统计。"""
        from Services.StatusManager import StatusManager

        sm = StatusManager()

        sm.add_record("2026-05-10", mood=2, energy=3, focus=4, sleep_hours=6.5)
        sm.add_record("2026-05-11", mood=4, energy=4, focus=3, sleep_hours=8.0)
        sm.add_record("2026-05-12", mood=5, energy=5, focus=5, sleep_hours=7.0)

        # 同天更新
        updated = sm.add_record("2026-05-10", mood=3)
        self.assertEqual(updated.mood, 3)

        # 范围查询
        range_results = sm.get_by_date_range("2026-05-10", "2026-05-11")
        self.assertGreaterEqual(len(range_results), 2)

        # 统计
        stats = sm.get_statistics(period="all")
        self.assertEqual(stats["count"], 3)
        self.assertAlmostEqual(stats["mood"], 4.0, delta=0.5)

    def test_knowledge_lifecycle(self):
        """知识：笔记 → 电子书导入 → 搜索 → 统计。"""
        from Services.KnowledgeManager import KnowledgeManager

        km = KnowledgeManager()

        # 笔记
        n1 = km.create_note("Python入门", "技术", ["Python", "入门"], "内容ABC")
        n2 = km.create_note("旅行的意义", "生活", ["旅行"], "读万卷书")

        self.assertEqual(km.get_statistics()["total_notes"], 2)

        # 电子书
        tmp_pdf = os.path.join(self.tmpdir, "ebook.pdf")
        with open(tmp_pdf, "wb") as f:
            f.write(b"%PDF-1.4\n%fake pdf content")

        ebook = km.import_ebook(tmp_pdf, "深入理解Python", "技术", ["Python", "进阶"])
        self.assertEqual(ebook.item_type, "ebook")
        self.assertIsNotNone(km.get_ebook_file_path(ebook.id))

        # 搜索
        results = km.search("python")
        self.assertGreaterEqual(len(results), 2)

        # 统计
        stats = km.get_statistics()
        self.assertEqual(stats["total_notes"], 2)
        self.assertEqual(stats["total_ebooks"], 1)

        # 删除笔记
        km.delete_item(n1.id)
        self.assertEqual(km.get_statistics()["total_notes"], 1)

        # 删除电子书（含文件）
        ebook_path = km.get_ebook_file_path(ebook.id)
        km.delete_item(ebook.id, delete_file=True)
        self.assertFalse(os.path.exists(ebook_path))
        self.assertEqual(km.get_statistics()["total_ebooks"], 0)

    def test_password_lifecycle(self):
        """密码：添加 → 查看明文 → 更新密码 → 搜索。"""
        from Services.PasswordManager import PasswordManager

        pm = PasswordManager()

        e1 = pm.add_entry("GitHub", "github.com", "user1", "pass123")
        e2 = pm.add_entry("Gmail", "mail.google.com", "user2", "secret456")

        self.assertEqual(pm.count(), 2)

        # 密码编码存储
        self.assertNotEqual(e1.password, "pass123")

        # 解密
        decrypted = pm.get_decrypted_password(e1.id)
        self.assertEqual(decrypted, "pass123")

        # 更新
        updated = pm.update_entry(e1.id, password="newpass789")
        self.assertEqual(pm.get_decrypted_password(e1.id), "newpass789")

        # 搜索
        results = pm.search("github")
        self.assertEqual(len(results), 1)

        # 删除
        pm.delete_entry(e2.id)
        self.assertEqual(pm.count(), 1)

    # ==== 3. 备份/恢复循环 ====

    def test_backup_restore_cycle(self):
        """完整备份 → 修改数据 → 恢复 → 验证。"""
        from Services.ProfileManager import ProfileManager
        from Services.SkillManager import SkillManager
        from Services.PasswordManager import PasswordManager
        from Services.BackupManager import BackupManager

        # 创建初始数据
        pm = ProfileManager()
        pm.update_profile(name="备份测试")

        sm = SkillManager()
        sm.add_skill("Go", "编程语言", 3, 50)

        pwm = PasswordManager()
        pwm.add_entry("TestSite", "test.com", "admin", "backuppass")

        # 备份
        bm = BackupManager()
        backup_path = bm.create_backup()
        self.assertTrue(os.path.exists(backup_path))

        # 验证备份内容
        info = bm.get_backup_info(backup_path)
        self.assertEqual(info["skills"], 1)
        self.assertEqual(info["passwords"], 1)

        # 修改数据（模拟数据丢失）
        for s in sm.get_all():
            sm.delete_skill(s.id)

        pm.update_profile(name="已修改")

        self.assertEqual(len(sm.get_all()), 0)

        # 恢复全部
        result = bm.restore_backup(backup_path)
        self.assertIn("skills", result["success"])
        self.assertIn("profile", result["success"])

        # 验证恢复
        self.assertEqual(len(sm.get_all()), 1)
        restored_profile = pm.get_profile()
        self.assertEqual(restored_profile.name, "备份测试")

        # 清理备份
        bm.delete_backup(backup_path)
        self.assertFalse(os.path.exists(backup_path))

    def test_selective_restore(self):
        """选择性恢复：只恢复指定模块。"""
        from Services.SkillManager import SkillManager
        from Services.StatusManager import StatusManager
        from Services.BackupManager import BackupManager

        sm = SkillManager()
        sm.add_skill("C++", "编程语言", 4, 500)

        stm = StatusManager()
        stm.add_record("2026-05-01", mood=5)

        bm = BackupManager()
        backup_path = bm.create_backup()

        # 删除数据
        for s in sm.get_all():
            sm.delete_skill(s.id)
        for s in stm.get_all():
            stm.delete_record(s.id)

        # 只恢复 skills
        result = bm.restore_backup(backup_path, modules=["skills"])
        self.assertIn("skills", result["success"])
        self.assertNotIn("status", result["success"])

        self.assertEqual(len(sm.get_all()), 1)
        self.assertEqual(len(stm.get_all()), 0)

    # ==== 4. 错误处理 ====

    def test_invalid_pdf_import(self):
        """无效 PDF 导入应抛异常。"""
        from Services.KnowledgeManager import KnowledgeManager
        from Core.Exceptions import ValidationError

        km = KnowledgeManager()

        # 非 PDF 文件
        txt_path = os.path.join(self.tmpdir, "not_pdf.pdf")
        with open(txt_path, "w") as f:
            f.write("Hello, I'm not a PDF!")

        with self.assertRaises(ValidationError):
            km.import_ebook(txt_path, "Test", "技术", [])

        # 不存在的文件
        with self.assertRaises(ValidationError):
            km.import_ebook("/nonexistent/ebook.pdf", "Ghost", "技术", [])

    def test_validation_errors(self):
        """各模块输入校验。"""
        from Core.Exceptions import ValidationError
        from Services.SkillManager import SkillManager
        from Services.StatusManager import StatusManager
        from Services.PasswordManager import PasswordManager

        sm = SkillManager()
        with self.assertRaises(ValidationError):
            sm.add_skill("", "工具", 3, 10)
        with self.assertRaises(ValidationError):
            sm.add_skill("X", "工具", 6, 10)

        stm = StatusManager()
        with self.assertRaises(ValidationError):
            stm.add_record("2026-05-19", mood=10)
        with self.assertRaises(ValidationError):
            stm.add_record("19-05-2026")

        pwm = PasswordManager()
        with self.assertRaises(ValidationError):
            pwm.add_entry("", "", "", "pass")
        with self.assertRaises(ValidationError):
            pwm.add_entry("Site", "", "", "")


if __name__ == "__main__":
    unittest.main()
