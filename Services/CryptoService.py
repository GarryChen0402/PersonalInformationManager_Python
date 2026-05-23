"""加密服务 — 主密码生命周期管理。

v1.2: 新增自动锁定计时器、错误次数限制、密码强度评估。
"""

import json
import os
import threading
import time

import Core.Config as Config
from Core.Crypto import SimpleCrypto
from Core.Exceptions import CryptoError

DEFAULT_AUTO_LOCK_TIMEOUT = 300  # 默认 5 分钟
MAX_FAILED_ATTEMPTS = 5
LOCK_COOLDOWN_SECONDS = 30


class CryptoService:
    """主密码管理服务。

    _master_password 以类变量缓存，仅在程序运行期间有效。
    支持自动锁定（可配置超时）和暴力破解防护。
    """

    _master_password: str | None = None
    _auto_lock_timer: threading.Timer | None = None
    _failed_attempts: int = 0
    _lock_until: float = 0.0

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

    @classmethod
    def get_lock_status(cls) -> dict:
        """获取锁定状态信息。"""
        cooldown = max(0.0, cls._lock_until - time.time())
        return {
            "is_locked": cls._master_password is None,
            "is_configured": cls.is_configured(),
            "failed_attempts": cls._failed_attempts,
            "max_attempts": MAX_FAILED_ATTEMPTS,
            "cooldown_remaining": int(cooldown),
        }

    @classmethod
    def get_password_strength(cls, password: str) -> dict:
        """评估密码强度。"""
        return SimpleCrypto.get_password_strength(password)

    # ---- 锁定/解锁 ----

    @classmethod
    def unlock(cls, master_password: str) -> bool:
        """验证并缓存主密码，成功返回 True。"""
        # 检查冷却期
        if cls._lock_until > time.time():
            remaining = int(cls._lock_until - time.time())
            raise CryptoError(f"已锁定，请 {remaining} 秒后重试")

        token = cls._read_token()
        if not token:
            return False

        if SimpleCrypto.verify_token(master_password, token):
            cls._master_password = master_password
            cls._failed_attempts = 0
            cls._lock_until = 0.0
            cls._start_auto_lock_timer()
            return True

        cls._failed_attempts += 1
        if cls._failed_attempts >= MAX_FAILED_ATTEMPTS:
            cls._lock_until = time.time() + LOCK_COOLDOWN_SECONDS
            raise CryptoError(f"连续 {MAX_FAILED_ATTEMPTS} 次密码错误，已锁定 {LOCK_COOLDOWN_SECONDS} 秒")
        return False

    @classmethod
    def lock(cls) -> None:
        """清除缓存的主密码（锁屏）。"""
        cls._master_password = None
        cls._cancel_auto_lock_timer()

    @classmethod
    def get_key(cls) -> str:
        """获取当前主密码，未解锁则抛出异常。"""
        if cls._master_password is None:
            raise RuntimeError("主密码未解锁，请先调用 unlock()")
        cls._reset_auto_lock_timer()
        return cls._master_password

    # ---- 加密/解密 ----

    @classmethod
    def encrypt(cls, plaintext: str) -> str:
        """用主密码加密明文（默认 v2 格式）。"""
        return SimpleCrypto.encrypt(plaintext, cls.get_key(), version="v2")

    @classmethod
    def decrypt(cls, encoded: str) -> str:
        """用主密码解密密文（自动识别 v1/v2 格式）。"""
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
        cls._start_auto_lock_timer()

    @classmethod
    def change_master_password(cls, old_password: str, new_password: str) -> None:
        """修改主密码。需要旧密码验证，并用新密码重新创建令牌。"""
        if not cls.unlock(old_password):
            raise ValueError("旧密码错误")

        if len(new_password) < 4:
            raise ValueError("新密码长度至少 4 位")

        new_token = SimpleCrypto.create_token(new_password)
        cls._write_token(new_token)
        cls._master_password = new_password
        cls._failed_attempts = 0
        cls._start_auto_lock_timer()

    # ---- 自动锁定 ----

    @classmethod
    def _get_timeout(cls) -> int:
        """从 config 读取自动锁定超时时间（秒），0 表示不自动锁定。"""
        try:
            if not os.path.exists(Config.CONFIG_PATH):
                return DEFAULT_AUTO_LOCK_TIMEOUT
            with open(Config.CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("auto_lock_timeout", DEFAULT_AUTO_LOCK_TIMEOUT)
        except (json.JSONDecodeError, OSError):
            return DEFAULT_AUTO_LOCK_TIMEOUT

    @classmethod
    def _start_auto_lock_timer(cls):
        """根据配置启动自动锁定计时器。"""
        cls._cancel_auto_lock_timer()
        timeout = cls._get_timeout()
        if timeout <= 0:
            return
        cls._auto_lock_timer = threading.Timer(timeout, cls._on_auto_lock)
        cls._auto_lock_timer.daemon = True
        cls._auto_lock_timer.start()

    @classmethod
    def _reset_auto_lock_timer(cls):
        """每次加密/解密操作后重置计时器（活跃则延后锁定）。"""
        cls._cancel_auto_lock_timer()
        timeout = cls._get_timeout()
        if timeout <= 0:
            return
        cls._auto_lock_timer = threading.Timer(timeout, cls._on_auto_lock)
        cls._auto_lock_timer.daemon = True
        cls._auto_lock_timer.start()

    @classmethod
    def _cancel_auto_lock_timer(cls):
        if cls._auto_lock_timer is not None:
            cls._auto_lock_timer.cancel()
            cls._auto_lock_timer = None

    @classmethod
    def _on_auto_lock(cls):
        """自动锁定回调。"""
        cls._master_password = None
        cls._auto_lock_timer = None

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
