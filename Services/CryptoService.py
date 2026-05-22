"""加密服务 — 主密码生命周期管理。"""

import json
import os

import Core.Config as Config
from Core.Crypto import SimpleCrypto


class CryptoService:
    """主密码管理服务。

    _master_password 以类变量缓存，仅在程序运行期间有效。
    锁屏或退出程序后需重新输入主密码。
    """

    _master_password: str | None = None

    # ---- 状态查询 ----

    @classmethod
    def is_unlocked(cls) -> bool:
        """主密码是否已解锁。"""
        return cls._master_password is not None

    @classmethod
    def is_configured(cls) -> bool:
        """是否已设置主密码（config 中是否有验证令牌）。"""
        token = cls._read_token()
        return bool(token)

    # ---- 锁定/解锁 ----

    @classmethod
    def unlock(cls, master_password: str) -> bool:
        """验证并缓存主密码，成功返回 True。"""
        token = cls._read_token()
        if not token:
            return False
        if SimpleCrypto.verify_token(master_password, token):
            cls._master_password = master_password
            return True
        return False

    @classmethod
    def lock(cls) -> None:
        """清除缓存的主密码（锁屏）。"""
        cls._master_password = None

    @classmethod
    def get_key(cls) -> str:
        """获取当前主密码，未解锁则抛出异常。"""
        if cls._master_password is None:
            raise RuntimeError("主密码未解锁，请先调用 unlock()")
        return cls._master_password

    # ---- 加密/解密 ----

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """用主密码加密明文。"""
        return SimpleCrypto.encrypt(plaintext, cls.get_key())

    @classmethod
    def decrypt(cls, encoded: str) -> str:
        """用主密码解密密文。"""
        return SimpleCrypto.decrypt(encoded, cls.get_key())

    # ---- 主密码设置/修改 ----

    @classmethod
    def setup_master_password(cls, password: str, confirm: str) -> None:
        """首次设置主密码。"""
        if password != confirm:
            raise ValueError("两次输入的密码不一致")
        if len(password) < 4:
            raise ValueError("主密码长度至少 4 位")

        token = SimpleCrypto.create_token(password)
        cls._write_token(token)
        cls._master_password = password

    @classmethod
    def change_master_password(cls, old_password: str, new_password: str) -> None:
        """修改主密码。需要旧密码验证，并用新密码重新创建令牌。"""
        if not cls.unlock(old_password):
            raise ValueError("旧密码错误")

        if len(new_password) < 4:
            raise ValueError("新密码长度至少 4 位")

        # 创建新令牌
        new_token = SimpleCrypto.create_token(new_password)
        cls._write_token(new_token)
        cls._master_password = new_password

    # ---- 令牌持久化 ----

    @staticmethod
    def _read_token() -> str:
        """从 config.json 读取验证令牌。"""
        if not os.path.exists(Config.CONFIG_PATH):
            return ""
        try:
            with open(Config.CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("master_password_token", "")
        except (json.JSONDecodeError, OSError):
            return ""

    @staticmethod
    def _write_token(token: str) -> None:
        """将验证令牌写入 config.json（保留其他字段）。"""
        data = {}
        if os.path.exists(Config.CONFIG_PATH):
            try:
                with open(Config.CONFIG_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except (json.JSONDecodeError, OSError):
                data = {}

        data["master_password_token"] = token
        data.setdefault("migration", {})["password"] = True

        os.makedirs(os.path.dirname(Config.CONFIG_PATH), exist_ok=True)
        with open(Config.CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
