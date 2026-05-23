"""DataMigration 单元测试 — 补全 v1.1 测试盲区。"""

import json
import os
import unittest

from Tests.test_base import PIMTestCase
import Core.Config as Config
from Core.DataMigration import (
    run_migrations, _ensure_config, _detect_base64_passwords,
    _detect_v1_passwords, _load_json, _save_json,
)


class TestDataMigration(PIMTestCase):
    """数据迁移全流程测试。"""

    @classmethod
    def _data_paths(cls):
        return {
            "CONFIG_PATH": "config.json",
            "PASSWORD_PATH": "passwords.json",
        }

    # ---- _load_json / _save_json ----

    def test_load_json_nonexistent(self):
        self.assertIsNone(_load_json("/nonexistent/file.json"))

    def test_load_json_corrupt(self):
        path = self.get_temp_path("corrupt.json")
        with open(path, "w", encoding="utf-8") as f:
            f.write("not json")
        self.assertIsNone(_load_json(path))

    def test_save_and_load_roundtrip(self):
        path = self.get_temp_path("roundtrip.json")
        _save_json(path, {"key": "value"})
        data = _load_json(path)
        self.assertEqual(data, {"key": "value"})

    # ---- _ensure_config ----

    def test_ensure_config_creates_defaults(self):
        config = _ensure_config()
        self.assertEqual(config["theme"], "light")
        self.assertEqual(config["font_size"], 10)
        self.assertEqual(config["migration"]["version"], "1.0")

        # v1.2 新增字段
        self.assertIn("auto_lock_timeout", config)
        self.assertIn("font_family", config)
        self.assertIn("window_geometry", config)

    def test_ensure_config_preserves_existing(self):
        _save_json(Config.CONFIG_PATH, {"theme": "dark", "migration": {"version": "1.0"}})
        config = _ensure_config()
        self.assertEqual(config["theme"], "dark")
        # 补充缺失字段
        self.assertEqual(config["font_size"], 10)

    # ---- _detect_base64_passwords ----

    def test_detect_base64_no_file(self):
        self.assertFalse(_detect_base64_passwords())

    def test_detect_base64_empty_list(self):
        _save_json(Config.PASSWORD_PATH, [])
        self.assertFalse(_detect_base64_passwords())

    def test_detect_base64_positive(self):
        import base64
        encoded = base64.b64encode(b"test_password").decode()
        _save_json(Config.PASSWORD_PATH, [
            {"password": encoded}
        ])
        self.assertTrue(_detect_base64_passwords())

    def test_detect_base64_negative_v2(self):
        _save_json(Config.PASSWORD_PATH, [
            {"password": "v2:dGVzdA=="}
        ])
        self.assertFalse(_detect_base64_passwords())

    def test_detect_base64_empty_password(self):
        _save_json(Config.PASSWORD_PATH, [
            {"password": ""},
            {"password": "v2:something"},
        ])
        self.assertFalse(_detect_base64_passwords())

    # ---- _detect_v1_passwords ----

    def test_detect_v1_no_file(self):
        self.assertFalse(_detect_v1_passwords())

    def test_detect_v1_empty_list(self):
        _save_json(Config.PASSWORD_PATH, [])
        self.assertFalse(_detect_v1_passwords())

    def test_detect_v1_positive(self):
        """v1 格式：base64 但解码后不是可打印文本（随机加密数据）。"""
        import base64
        # 模拟 v1 加密数据：随机字节 base64 编码后不是可打印文本
        random_data = bytes([0x00, 0xFF, 0x8B, 0x7C, 0x1A, 0xE3, 0x99, 0x44,
                             0xD5, 0x01, 0xFE, 0xCA, 0x33, 0x8E, 0x72, 0xBB])
        encoded = base64.b64encode(random_data).decode()
        _save_json(Config.PASSWORD_PATH, [
            {"password": encoded}
        ])
        self.assertTrue(_detect_v1_passwords())

    def test_detect_v1_negative_v2(self):
        _save_json(Config.PASSWORD_PATH, [
            {"password": "v2:dGVzdA=="}
        ])
        self.assertFalse(_detect_v1_passwords())

    def test_detect_v1_negative_base64(self):
        import base64
        encoded = base64.b64encode(b"hello").decode()
        _save_json(Config.PASSWORD_PATH, [
            {"password": encoded}  # 这是 base64 格式（可打印 ASCII）
        ])
        self.assertFalse(_detect_v1_passwords())

    # ---- run_migrations ----

    def test_run_migrations_no_config(self):
        report = run_migrations()
        self.assertEqual(report["config_version"], "1.2")
        self.assertFalse(report.get("migration_needed", False))

    def test_run_migrations_already_v1_2(self):
        _save_json(Config.CONFIG_PATH, {
            "theme": "light",
            "font_size": 10,
            "migration": {"version": "1.2"},
        })
        report = run_migrations()
        self.assertFalse(report["migration_needed"])

    def test_run_migrations_from_v1_0_with_base64(self):
        import base64
        encoded = base64.b64encode(b"test_pass").decode()
        _save_json(Config.PASSWORD_PATH, [
            {"password": encoded}
        ])
        _save_json(Config.CONFIG_PATH, {
            "theme": "light",
            "migration": {"version": "1.0"},
        })

        report = run_migrations()
        self.assertEqual(report["config_version"], "1.2")
        self.assertTrue(report.get("base64_passwords_detected", False))

    def test_run_migrations_creates_new_config_keys(self):
        run_migrations()
        config = _load_json(Config.CONFIG_PATH)
        self.assertIn("auto_lock_timeout", config)
        self.assertIn("font_family", config)
        self.assertIn("window_geometry", config)
        self.assertEqual(config["migration"]["version"], "1.2")
