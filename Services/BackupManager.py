"""数据备份与恢复业务逻辑。"""

import json
import os
from datetime import datetime

import Core.Config as Config
from Core.Exceptions import BackupError, DataLoadError

def _module_paths():
    return {
        "profile": Config.PROFILE_PATH,
        "skills": Config.SKILL_PATH,
        "status": Config.STATUS_PATH,
        "knowledge": Config.KNOWLEDGE_PATH,
        "passwords": Config.PASSWORD_PATH,
    }


class BackupManager:
    """备份管理器。"""

    def __init__(self):
        os.makedirs(Config.BACKUP_DIR, exist_ok=True)

    def create_backup(self) -> str:
        """创建全量备份，返回备份文件路径。"""
        backup_data = {}
        for module_name, path in _module_paths().items():
            try:
                if os.path.exists(path):
                    with open(path, "r", encoding="utf-8") as f:
                        backup_data[module_name] = json.load(f)
                else:
                    backup_data[module_name] = {} if module_name == "profile" else []
            except (json.JSONDecodeError, OSError) as e:
                raise BackupError(f"读取 {module_name} 数据失败: {e}") from e

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.json"
        filepath = os.path.join(Config.BACKUP_DIR, filename)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise BackupError(f"写入备份文件失败: {e}") from e

        return filepath

    def restore_backup(self, backup_path: str,
                       modules: list[str] | None = None) -> dict:
        """从备份恢复数据。

        modules: 要恢复的模块列表，为 None 则恢复全部。
        返回 {"success": [...], "failed": [...]}
        """
        if not os.path.exists(backup_path):
            raise BackupError(f"备份文件不存在: {backup_path}")

        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            raise BackupError(f"读取备份文件失败: {e}") from e

        if modules is None:
            modules = list(_module_paths().keys())

        result = {"success": [], "failed": []}

        for module_name in modules:
            if module_name not in _module_paths():
                result["failed"].append(f"{module_name}: 未知模块")
                continue
            if module_name not in backup_data:
                result["failed"].append(f"{module_name}: 备份中无此模块数据")
                continue

            target_path = _module_paths()[module_name]
            try:
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as f:
                    json.dump(backup_data[module_name], f,
                              ensure_ascii=False, indent=2)
                result["success"].append(module_name)
            except OSError as e:
                result["failed"].append(f"{module_name}: {e}")

        return result

    def list_backups(self) -> list[dict]:
        """列出所有备份文件，按时间倒序。"""
        backups = []
        if not os.path.exists(Config.BACKUP_DIR):
            return backups

        for filename in os.listdir(Config.BACKUP_DIR):
            if filename.startswith("backup_") and filename.endswith(".json"):
                filepath = os.path.join(Config.BACKUP_DIR, filename)
                stat = os.stat(filepath)
                backups.append({
                    "path": filepath,
                    "name": filename,
                    "size": stat.st_size,
                    "created_at": datetime.fromtimestamp(
                        stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                })

        backups.sort(key=lambda b: b["name"], reverse=True)
        return backups

    def delete_backup(self, backup_path: str) -> bool:
        """删除指定备份文件。"""
        try:
            if os.path.exists(backup_path):
                os.remove(backup_path)
                return True
            return False
        except OSError:
            return False

    def get_backup_info(self, backup_path: str) -> dict | None:
        """获取备份文件概览。"""
        try:
            with open(backup_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        info = {}
        for module_name, content in data.items():
            if isinstance(content, list):
                info[module_name] = len(content)
            elif isinstance(content, dict):
                info[module_name] = "已备份" if content else "空"
        return info
