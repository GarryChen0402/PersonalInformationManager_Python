"""个人档案管理业务逻辑。"""

import csv
import json
import os
from datetime import datetime

import Core.Config as Config
from Core.Exceptions import DataLoadError, DataSaveError
from Models.Profile import Profile


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ProfileManager:
    """个人档案管理器，档案以单例 JSON 对象存储。"""

    def __init__(self):
        self.data_path = Config.PROFILE_PATH

    def _load(self) -> dict:
        """从文件加载档案，文件不存在或损坏时返回空字典。"""
        if not os.path.exists(self.data_path):
            return {}
        try:
            with open(self.data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError) as e:
            raise DataLoadError(f"加载档案失败: {e}") from e

    def _save(self, data: dict) -> None:
        """原子写入档案到文件。"""
        tmp_path = self.data_path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.data_path)
        except OSError as e:
            raise DataSaveError(f"保存档案失败: {e}") from e

    def get_profile(self) -> Profile:
        """获取当前档案，未创建时返回空 Profile。"""
        data = self._load()
        return Profile.from_dict(data)

    def update_profile(self, **kwargs) -> Profile:
        """更新档案字段并保存。首次创建自动设置 created_at。"""
        data = self._load()
        if not data:
            data["created_at"] = _now()

        # 只更新 Profile 中存在的字段
        valid_fields = {f.name for f in Profile.__dataclass_fields__.values()}  # noqa: F821
        for key, value in kwargs.items():
            if key in valid_fields:
                data[key] = value

        data["updated_at"] = _now()
        self._save(data)
        return Profile.from_dict(data)

    def export_profile(self, output_path: str) -> None:
        """导出档案为独立 JSON 文件。"""
        data = self._load()
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise DataSaveError(f"导出档案失败: {e}") from e

    def get_summary(self) -> dict:
        """返回档案完整性统计。"""
        profile = self.get_profile()
        fields = [
            "name", "gender", "birthday", "phone", "email",
            "address", "wechat", "qq", "github", "blog", "bio"
        ]
        filled = sum(1 for f in fields if getattr(profile, f, ""))
        return {
            "filled": filled,
            "total": len(fields),
            "last_updated": profile.updated_at or "从未更新",
        }

    def export_csv(self, path: str) -> None:
        """导出档案为 CSV 文件（单行，字段为列）。"""
        profile = self.get_profile()
        fields = ["name", "gender", "birthday", "phone", "email",
                  "address", "wechat", "qq", "github", "blog", "bio"]
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(fields)
            writer.writerow([getattr(profile, f, "") for f in fields])
