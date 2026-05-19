"""密码管理业务逻辑 — base64 编解码。"""

import base64

import Core.Config as Config
from Core.Exceptions import ValidationError
from Core.Storage import JSONFileStorage
from Models.Password import PasswordEntry


class PasswordManager:
    """密码管理器，密码字段以 base64 编码存储。"""

    def __init__(self):
        self.storage = JSONFileStorage(Config.PASSWORD_PATH)

    @staticmethod
    def _encode(plain: str) -> str:
        return base64.b64encode(plain.encode("utf-8")).decode()

    @staticmethod
    def _decode(encoded: str) -> str:
        return base64.b64decode(encoded.encode()).decode("utf-8")

    # ---- 增 ----

    def add_entry(self, platform: str, url: str, username: str,
                  password: str, note: str = "") -> PasswordEntry:
        """添加密码条目，密码自动编码。"""
        if not platform.strip():
            raise ValidationError("平台名称不能为空")
        if not password:
            raise ValidationError("密码不能为空")

        record = {
            "platform": platform.strip(),
            "url": url.strip(),
            "username": username.strip(),
            "password": self._encode(password),
            "note": note.strip(),
        }
        saved = self.storage.add(record)
        return PasswordEntry.from_dict(saved)

    # ---- 查 ----

    def get_all(self) -> list[PasswordEntry]:
        """获取所有条目（密码已编码）。"""
        records = self.storage.get_all()
        records.sort(key=lambda r: r.get("updated_at", r.get("created_at", "")), reverse=True)
        return [PasswordEntry.from_dict(r) for r in records]

    def get_by_id(self, entry_id: str) -> PasswordEntry | None:
        record = self.storage.get_by_id(entry_id)
        return PasswordEntry.from_dict(record) if record else None

    def search(self, keyword: str) -> list[PasswordEntry]:
        """按平台/网址/账号模糊搜索。"""
        all_records = self.storage.get_all()
        kw = keyword.lower()
        results = [
            r for r in all_records
            if kw in r.get("platform", "").lower()
            or kw in r.get("url", "").lower()
            or kw in r.get("username", "").lower()
        ]
        results.sort(key=lambda r: r.get("updated_at", r.get("created_at", "")), reverse=True)
        return [PasswordEntry.from_dict(r) for r in results]

    def get_decrypted_password(self, entry_id: str) -> str:
        """获取指定条目的明文密码。"""
        record = self.storage.get_by_id(entry_id)
        if not record:
            raise ValidationError("记录不存在")
        return self._decode(record["password"])

    # ---- 改 ----

    def update_entry(self, entry_id: str, **updates) -> PasswordEntry:
        """更新条目。若 password 字段存在则自动编码。"""
        if "password" in updates and updates["password"]:
            updates["password"] = self._encode(updates["password"])
        elif "password" in updates:
            del updates["password"]  # 空密码不更新

        if "platform" in updates and not updates["platform"].strip():
            raise ValidationError("平台名称不能为空")

        updated = self.storage.update(entry_id, updates)
        return PasswordEntry.from_dict(updated)

    # ---- 删 ----

    def delete_entry(self, entry_id: str) -> bool:
        return self.storage.delete(entry_id)

    def count(self) -> int:
        return self.storage.count()
