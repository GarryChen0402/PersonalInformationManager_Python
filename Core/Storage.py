"""JSON 文件存储基类，提供通用 CRUD 操作。"""

import json
import os
import uuid
from datetime import datetime
from typing import Any

from .Exceptions import DataLoadError, DataSaveError, RecordNotFoundError


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class JSONFileStorage:
    """JSON 文件存储基类，每个实例管理一个 JSON 文件。"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        if not os.path.exists(file_path):
            self._save([])

    def _load(self) -> list[dict]:
        """从文件加载数据，返回字典列表。"""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as e:
            raise DataLoadError(f"数据文件格式错误 ({self.file_path}): {e}") from e

    def _save(self, data: list[dict]) -> None:
        """原子写入：先写临时文件，成功后再替换原文件。"""
        tmp_path = self.file_path + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(tmp_path, self.file_path)
        except OSError as e:
            raise DataSaveError(f"保存数据失败: {e}") from e

    # ---- 查询 ----

    def get_all(self) -> list[dict]:
        """获取所有记录。"""
        return self._load()

    def get_by_id(self, record_id: str) -> dict | None:
        """根据 ID 查询单条记录。"""
        for record in self._load():
            if record.get("id") == record_id:
                return record
        return None

    def query(self, **filters: Any) -> list[dict]:
        """按字段条件筛选记录，多个条件为 AND 关系。"""
        results = self._load()
        for field, value in filters.items():
            results = [r for r in results if r.get(field) == value]
        return results

    def search(self, field: str, keyword: str) -> list[dict]:
        """按指定字段模糊搜索（大小写不敏感）。"""
        keyword_lower = keyword.lower()
        return [
            r for r in self._load()
            if keyword_lower in str(r.get(field, "")).lower()
        ]

    # ---- 增删改 ----

    def add(self, record: dict) -> dict:
        """新增记录，自动添加 id 和 created_at，返回完整记录。"""
        data = self._load()
        record["id"] = str(uuid.uuid4())
        record["created_at"] = _now()
        data.append(record)
        self._save(data)
        return record

    def update(self, record_id: str, updates: dict) -> dict:
        """更新记录，返回更新后的完整记录。找不到记录则抛出 RecordNotFoundError。"""
        data = self._load()
        for record in data:
            if record.get("id") == record_id:
                record.update(updates)
                record["updated_at"] = _now()
                self._save(data)
                return record
        raise RecordNotFoundError(f"记录 {record_id} 不存在")

    def delete(self, record_id: str) -> bool:
        """删除记录，返回是否成功。"""
        data = self._load()
        for i, record in enumerate(data):
            if record.get("id") == record_id:
                data.pop(i)
                self._save(data)
                return True
        return False

    def count(self) -> int:
        """返回记录总数。"""
        return len(self._load())
