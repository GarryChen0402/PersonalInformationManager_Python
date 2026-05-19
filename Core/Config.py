"""项目路径配置与初始化。"""

import os
import sys

# 项目根目录 — 兼容 PyInstaller 打包
if getattr(sys, "frozen", False):
    # 打包后 exe 与 Data/ 同级
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 开发模式：Config.py 在 Core/ 下，上溯一层即为项目根目录
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 数据目录
DATA_DIR = os.path.join(BASE_DIR, "Data")
BOOKS_DIR = os.path.join(DATA_DIR, "books")
BACKUP_DIR = os.path.join(DATA_DIR, "backups")

# 各模块 JSON 数据文件路径
PROFILE_PATH = os.path.join(DATA_DIR, "profile.json")
STATUS_PATH = os.path.join(DATA_DIR, "status.json")
SKILL_PATH = os.path.join(DATA_DIR, "skills.json")
KNOWLEDGE_PATH = os.path.join(DATA_DIR, "knowledge.json")
PASSWORD_PATH = os.path.join(DATA_DIR, "passwords.json")


def ensure_directories() -> None:
    """首次运行时创建所有必需的目录。"""
    os.makedirs(BOOKS_DIR, exist_ok=True)
    os.makedirs(BACKUP_DIR, exist_ok=True)
