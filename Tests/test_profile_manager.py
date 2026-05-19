"""ProfileManager 单元测试。"""

import json
import os
import tempfile
import unittest

import Core.Config as Config
from Core.Exceptions import DataLoadError, DataSaveError
from Services.ProfileManager import ProfileManager


class TestProfileManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.orig_path = Config.PROFILE_PATH
        Config.PROFILE_PATH = os.path.join(cls.tmpdir, "profile.json")

    @classmethod
    def tearDownClass(cls):
        Config.PROFILE_PATH = cls.orig_path
        for f in os.listdir(cls.tmpdir):
            os.unlink(os.path.join(cls.tmpdir, f))
        os.rmdir(cls.tmpdir)

    def setUp(self):
        if os.path.exists(Config.PROFILE_PATH):
            os.remove(Config.PROFILE_PATH)
        self.manager = ProfileManager()

    def test_empty_profile(self):
        profile = self.manager.get_profile()
        self.assertEqual(profile.name, "")
        self.assertEqual(profile.gender, "")

    def test_update_profile(self):
        profile = self.manager.update_profile(
            name="张三", gender="男", phone="13800138000"
        )
        self.assertEqual(profile.name, "张三")
        self.assertEqual(profile.gender, "男")
        self.assertEqual(profile.phone, "13800138000")
        self.assertIsNotNone(profile.updated_at)

    def test_update_only_valid_fields(self):
        profile = self.manager.update_profile(invalid_field="should_be_ignored")
        self.assertFalse(hasattr(profile, "invalid_field"))

    def test_partial_update(self):
        self.manager.update_profile(name="初始", phone="123")
        self.manager.update_profile(phone="456")
        profile = self.manager.get_profile()
        self.assertEqual(profile.name, "初始")
        self.assertEqual(profile.phone, "456")

    def test_summary(self):
        self.manager.update_profile(
            name="test", gender="男", birthday="2000-01-01",
            phone="1", email="2", address="3",
            wechat="4", qq="5", github="6", blog="7", bio="8"
        )
        s = self.manager.get_summary()
        self.assertEqual(s["filled"], 11)
        self.assertEqual(s["total"], 11)

    def test_summary_empty(self):
        s = self.manager.get_summary()
        self.assertEqual(s["filled"], 0)

    def test_export_profile(self):
        self.manager.update_profile(name="导出测试")
        export_path = os.path.join(self.tmpdir, "exported.json")
        self.manager.export_profile(export_path)
        self.assertTrue(os.path.exists(export_path))
        with open(export_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["name"], "导出测试")


if __name__ == "__main__":
    unittest.main()
