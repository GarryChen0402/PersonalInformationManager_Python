"""BackupManager 单元测试。"""

import json
import os
import tempfile
import time
import unittest

import Core.Config as Config
from Core.Exceptions import BackupError
from Services.BackupManager import BackupManager


class TestBackupManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.orig_backup = Config.BACKUP_DIR
        cls.orig_paths = {
            "profile": Config.PROFILE_PATH,
            "skills": Config.SKILL_PATH,
            "status": Config.STATUS_PATH,
            "knowledge": Config.KNOWLEDGE_PATH,
            "passwords": Config.PASSWORD_PATH,
        }
        Config.BACKUP_DIR = os.path.join(cls.tmpdir, "backups")
        Config.PROFILE_PATH = os.path.join(cls.tmpdir, "profile.json")
        Config.SKILL_PATH = os.path.join(cls.tmpdir, "skills.json")
        Config.STATUS_PATH = os.path.join(cls.tmpdir, "status.json")
        Config.KNOWLEDGE_PATH = os.path.join(cls.tmpdir, "knowledge.json")
        Config.PASSWORD_PATH = os.path.join(cls.tmpdir, "passwords.json")

        # 写入测试数据
        with open(Config.PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump({"name": "Test", "created_at": "2026-01-01"}, f)
        with open(Config.SKILL_PATH, "w", encoding="utf-8") as f:
            json.dump([{"id": "1", "name": "Python"}], f)
        with open(Config.STATUS_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        with open(Config.KNOWLEDGE_PATH, "w", encoding="utf-8") as f:
            json.dump([{"id": "k1", "title": "Note"}], f)
        with open(Config.PASSWORD_PATH, "w", encoding="utf-8") as f:
            json.dump([{"id": "p1", "platform": "GitHub"}], f)

    @classmethod
    def tearDownClass(cls):
        Config.BACKUP_DIR = cls.orig_backup
        Config.PROFILE_PATH = cls.orig_paths["profile"]
        Config.SKILL_PATH = cls.orig_paths["skills"]
        Config.STATUS_PATH = cls.orig_paths["status"]
        Config.KNOWLEDGE_PATH = cls.orig_paths["knowledge"]
        Config.PASSWORD_PATH = cls.orig_paths["passwords"]
        for root, dirs, files in os.walk(cls.tmpdir, topdown=False):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(cls.tmpdir)

    def setUp(self):
        # 清理备份目录
        backup_dir = Config.BACKUP_DIR
        if os.path.exists(backup_dir):
            for f in os.listdir(backup_dir):
                os.unlink(os.path.join(backup_dir, f))
        # 重置数据文件为初始状态
        with open(Config.PROFILE_PATH, "w", encoding="utf-8") as f:
            json.dump({"name": "Test", "created_at": "2026-01-01"}, f)
        with open(Config.SKILL_PATH, "w", encoding="utf-8") as f:
            json.dump([{"id": "1", "name": "Python"}], f)
        with open(Config.STATUS_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)
        with open(Config.KNOWLEDGE_PATH, "w", encoding="utf-8") as f:
            json.dump([{"id": "k1", "title": "Note"}], f)
        with open(Config.PASSWORD_PATH, "w", encoding="utf-8") as f:
            json.dump([{"id": "p1", "platform": "GitHub"}], f)
        self.manager = BackupManager()

    def test_create_backup(self):
        path = self.manager.create_backup()
        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.endswith(".json"))

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertIn("profile", data)
        self.assertIn("skills", data)
        self.assertEqual(data["profile"]["name"], "Test")

    def test_list_backups(self):
        self.manager.create_backup()
        time.sleep(1.1)  # 确保时间戳不同
        self.manager.create_backup()
        backups = self.manager.list_backups()
        self.assertEqual(len(backups), 2)
        self.assertIn("path", backups[0])
        self.assertIn("name", backups[0])
        self.assertIn("size", backups[0])
        self.assertIn("created_at", backups[0])

    def test_get_backup_info(self):
        path = self.manager.create_backup()
        info = self.manager.get_backup_info(path)
        self.assertIsNotNone(info)
        self.assertIn("profile", info)
        self.assertEqual(info["skills"], 1)

    def test_get_backup_info_nonexistent(self):
        info = self.manager.get_backup_info("/nonexistent/backup.json")
        self.assertIsNone(info)

    def test_restore_all(self):
        path = self.manager.create_backup()

        # 修改原数据
        with open(Config.SKILL_PATH, "w", encoding="utf-8") as f:
            json.dump([], f)

        result = self.manager.restore_backup(path)
        self.assertIn("skills", result["success"])

        with open(Config.SKILL_PATH, "r", encoding="utf-8") as f:
            restored = json.load(f)
        self.assertEqual(len(restored), 1)

    def test_restore_selective(self):
        path = self.manager.create_backup()

        result = self.manager.restore_backup(path, modules=["profile", "passwords"])
        self.assertIn("profile", result["success"])
        self.assertIn("passwords", result["success"])
        self.assertNotIn("skills", result["success"])

    def test_restore_nonexistent_backup(self):
        with self.assertRaises(BackupError):
            self.manager.restore_backup("/nonexistent/backup.json")

    def test_delete_backup(self):
        path = self.manager.create_backup()
        self.assertTrue(self.manager.delete_backup(path))
        self.assertFalse(os.path.exists(path))

    def test_delete_nonexistent_backup(self):
        self.assertFalse(self.manager.delete_backup("/nonexistent/backup.json"))


if __name__ == "__main__":
    unittest.main()
