"""密码管理业务逻辑 — 流密码加密存储。"""

import base64

import Core.Config as Config
from Core.Exceptions import ValidationError
from Core.Storage import JSONFileStorage
from Models.Password import PasswordEntry
from Services.CryptoService import CryptoService


class PasswordManager:
    """密码管理器，密码字段以流密码加密存储。"""

    def __init__(self):
        self.storage = JSONFileStorage(Config.PASSWORD_PATH)

    @staticmethod
    def _is_base64_format(encoded: str) -> bool:
        """检测密码是否为旧的 base64 格式。"""
        try:
            decoded = base64.b64decode(encoded.encode()).decode("utf-8")
            return decoded.isprintable() or len(decoded) > 0
        except Exception:
            return False

    def _encode(self, plain: str) -> str:
        return CryptoService.encrypt(plain)

    def _decode(self, encoded: str) -> str:
        return CryptoService.decrypt(encoded)

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

    # ---- 迁移 ----

    def migrate_from_base64(self) -> int:
        """将旧 base64 编码的密码迁移到新加密格式。返回迁移条目数。"""
        records = self.storage.get_all()
        migrated = 0
        for record in records:
            pwd = record.get("password", "")
            if not pwd:
                continue
            if self._is_base64_format(pwd):
                try:
                    plain = base64.b64decode(pwd.encode()).decode("utf-8")
                    record["password"] = self._encode(plain)
                    migrated += 1
                except Exception:
                    continue

        if migrated > 0:
            self.storage._save(records)
        return migrated

    def re_encrypt_all(self, old_password: str) -> int:
        """主密码变更后重新加密所有条目。返回重新加密的条目数。"""
        records = self.storage.get_all()
        count = 0
        for record in records:
            pwd = record.get("password", "")
            if not pwd:
                continue
            # 用旧密码解密
            cached = CryptoService._master_password
            CryptoService._master_password = old_password
            try:
                plain = CryptoService.decrypt(pwd)
                # 恢复当前主密码后重新加密
                CryptoService._master_password = cached
                record["password"] = self._encode(plain)
                count += 1
            except Exception:
                CryptoService._master_password = cached
                continue

        if count > 0:
            self.storage._save(records)
        return count
