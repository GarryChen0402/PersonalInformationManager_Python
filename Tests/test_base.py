"""共享测试基类 — 为所有 PIM 测试提供统一的 setUp/tearDown 模式。"""

import os
import shutil
import tempfile
import unittest

import Core.Config as Config


class PIMTestCase(unittest.TestCase):
    """所有 PIM 测试的共享基类。

    自动创建临时目录并重定向 Config.* 路径，测试完成后恢复。
    子类只需覆盖 `_data_paths()` 返回需要重定向的路径映射。
    """

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.mkdtemp()
        cls._original_paths = {}
        cls._backup_original_paths()

    @classmethod
    def tearDownClass(cls):
        cls._restore_all_paths()
        if os.path.exists(cls._temp_dir):
            shutil.rmtree(cls._temp_dir, ignore_errors=True)

    @classmethod
    def _data_paths(cls) -> dict[str, str]:
        """返回需要重定向的路径映射 {attr_name: relative_filename}。

        子类覆盖此方法以指定需要隔离的数据文件。
        示例:
            return {"SKILL_PATH": "skills.json"}
        """
        return {}

    @classmethod
    def _backup_original_paths(cls):
        """备份并重定向 Config 路径。"""
        for attr_name, filename in cls._data_paths().items():
            original = getattr(Config, attr_name, None)
            if original:
                cls._original_paths[attr_name] = original
                setattr(Config, attr_name, os.path.join(cls._temp_dir, filename))
        # 同时重定向 DATA/BACKUP/BOOKS 目录
        for dir_attr in ["DATA_DIR", "BACKUP_DIR", "BOOKS_DIR"]:
            original = getattr(Config, dir_attr, None)
            if original:
                cls._original_paths[dir_attr] = original
        cls._ensure_temp_dirs()

    @classmethod
    def _ensure_temp_dirs(cls):
        """在临时目录中创建必要的子目录。"""
        for dir_attr in ["BACKUP_DIR", "BOOKS_DIR"]:
            if dir_attr in cls._original_paths:
                temp_path = os.path.join(cls._temp_dir, os.path.basename(
                    cls._original_paths[dir_attr]))
                setattr(Config, dir_attr, temp_path)
                os.makedirs(temp_path, exist_ok=True)
        if "DATA_DIR" in cls._original_paths:
            setattr(Config, "DATA_DIR", cls._temp_dir)
            os.makedirs(os.path.join(cls._temp_dir, "books"), exist_ok=True)
            os.makedirs(os.path.join(cls._temp_dir, "backups"), exist_ok=True)

    @classmethod
    def _restore_all_paths(cls):
        """恢复所有原始路径。"""
        for attr_name, original in cls._original_paths.items():
            setattr(Config, attr_name, original)

    def setUp(self):
        """每个测试方法前清理数据文件。"""
        self._clean_data_files()

    def _clean_data_files(self):
        """删除临时目录中的 JSON 数据文件。"""
        for attr_name, filename in self._data_paths().items():
            filepath = getattr(Config, attr_name, None)
            if filepath and os.path.exists(filepath):
                os.remove(filepath)

    def get_temp_path(self, filename: str) -> str:
        """获取临时目录下的文件路径。"""
        return os.path.join(self._temp_dir, filename)
