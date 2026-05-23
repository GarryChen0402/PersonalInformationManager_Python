"""ConfigManager 单元测试 — 补全 v1.1 测试盲区。"""

import os
import unittest

from Tests.test_base import PIMTestCase
from Services.ConfigManager import ConfigManager
import Core.Config as Config


class TestConfigManager(PIMTestCase):
    """ConfigManager 全部方法测试。"""

    @classmethod
    def _data_paths(cls):
        return {"CONFIG_PATH": "config.json"}

    def setUp(self):
        super().setUp()
        # 单例重置
        ConfigManager._instance = None
        self.cm = ConfigManager()

    # ---- 默认值 ----

    def test_defaults_on_first_load(self):
        self.assertEqual(self.cm.get_theme(), "light")
        self.assertEqual(self.cm.get_font_size(), 10)
        self.assertEqual(self.cm.get_master_password_token(), "")
        self.assertEqual(self.cm.get_last_active_module(), "profile")
        self.assertEqual(self.cm.get_search_history(), [])

    def test_missing_keys_merged_with_defaults(self):
        # 手动写入一个不完整配置
        import json
        with open(Config.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"theme": "dark"}, f)

        ConfigManager._instance = None
        cm = ConfigManager()
        self.assertEqual(cm.get_theme(), "dark")  # 保留已有值
        self.assertEqual(cm.get_font_size(), 10)   # 补充默认值

    # ---- 单例 ----

    def test_singleton_behavior(self):
        cm2 = ConfigManager()
        self.assertIs(self.cm, cm2)

    def test_singleton_after_reset(self):
        ConfigManager._instance = None
        cm2 = ConfigManager()
        self.assertIsNot(self.cm, cm2)

    # ---- 通用 get/set ----

    def test_get_set_basic(self):
        self.cm.set("test_key", "test_value")
        self.assertEqual(self.cm.get("test_key"), "test_value")

    def test_get_default(self):
        self.assertEqual(self.cm.get("nonexistent", "fallback"), "fallback")

    def test_set_persists(self):
        self.cm.set("custom", 42)

        ConfigManager._instance = None
        cm2 = ConfigManager()
        self.assertEqual(cm2.get("custom"), 42)

    # ---- 主题 ----

    def test_get_set_theme(self):
        self.cm.set_theme("dark")
        self.assertEqual(self.cm.get_theme(), "dark")

    # ---- 字体大小 ----

    def test_get_set_font_size(self):
        self.cm.set_font_size(12)
        self.assertEqual(self.cm.get_font_size(), 12)

    def test_font_size_clamp_min(self):
        self.cm.set_font_size(5)
        self.assertEqual(self.cm.get_font_size(), 8)

    def test_font_size_clamp_max(self):
        self.cm.set_font_size(20)
        self.assertEqual(self.cm.get_font_size(), 16)

    def test_font_size_in_range(self):
        self.cm.set_font_size(10)
        self.assertEqual(self.cm.get_font_size(), 10)

    # ---- 主密码令牌 ----

    def test_get_set_master_password_token(self):
        self.cm.set_master_password_token("abc123")
        self.assertEqual(self.cm.get_master_password_token(), "abc123")

    # ---- 最后活跃模块 ----

    def test_get_set_last_active_module(self):
        self.cm.set_last_active_module("todo")
        self.assertEqual(self.cm.get_last_active_module(), "todo")

    # ---- 搜索历史 ----

    def test_search_history_initially_empty(self):
        self.assertEqual(self.cm.get_search_history(), [])

    def test_add_search_history(self):
        self.cm.add_search_history("Python")
        self.assertIn("Python", self.cm.get_search_history())

    def test_search_history_dedup(self):
        self.cm.add_search_history("Python")
        self.cm.add_search_history("Java")
        self.cm.add_search_history("Python")  # 重复
        history = self.cm.get_search_history()
        self.assertEqual(history[0], "Python")
        self.assertEqual(len([h for h in history if h == "Python"]), 1)

    def test_search_history_max_10(self):
        for i in range(20):
            self.cm.add_search_history(f"keyword_{i}")
        self.assertLessEqual(len(self.cm.get_search_history()), 10)

    def test_search_history_lifo_order(self):
        self.cm.add_search_history("first")
        self.cm.add_search_history("second")
        self.cm.add_search_history("third")
        self.assertEqual(self.cm.get_search_history()[0], "third")

    # ---- 迁移标记 ----

    def test_is_password_migration_pending_default(self):
        self.assertFalse(self.cm.is_password_migration_pending())

    def test_clear_password_migration_flag(self):
        self.cm.set("migration", {"password_pending": True, "version": "1.1"})
        self.assertTrue(self.cm.is_password_migration_pending())
        self.cm.clear_password_migration_flag()
        self.assertFalse(self.cm.is_password_migration_pending())

    # ---- 持久化 ----

    def test_config_written_to_disk(self):
        self.cm.set("persist_test", True)
        self.assertTrue(os.path.exists(Config.CONFIG_PATH))

    def test_config_reloads_correctly(self):
        self.cm.set("reload_test", "hello")
        ConfigManager._instance = None
        cm2 = ConfigManager()
        self.assertEqual(cm2.get("reload_test"), "hello")

    def test_corrupt_json_uses_defaults(self):
        with open(Config.CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write("not valid json {{{")

        ConfigManager._instance = None
        cm = ConfigManager()
        self.assertEqual(cm.get_theme(), "light")  # 回退默认值
