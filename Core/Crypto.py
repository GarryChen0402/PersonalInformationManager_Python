"""SHA-256 流密码加解密工具 — 零外部依赖。

v1.2: 新增 HMAC 认证加密 (v2 格式) + 密码强度评估。
"""

import base64
import hashlib
import hmac
import secrets
import struct

from Core.Exceptions import CryptoError

_PBKDF2_ITERATIONS = 100000
_SALT_LENGTH = 16
_NONCE_LENGTH = 16
_HMAC_LENGTH = 32
_DERIVED_KEY_LENGTH = 64  # 前 32 字节 enc_key，后 32 字节 hmac_key

VERSION_PREFIX_V2 = "v2:"


class SimpleCrypto:
    """使用 PBKDF2 + SHA-256 流密码进行加解密。

    v1 格式（向后兼容）: base64(salt + nonce + ciphertext)
    v2 格式（默认）: "v2:" + base64(salt + nonce + ciphertext + hmac)
    """

    @staticmethod
    def derive_key(master_password: str, salt: bytes) -> bytes:
        """PBKDF2 派生 256 位密钥（v1 兼容，仅返回加密密钥）。"""
        return hashlib.pbkdf2_hmac(
            "sha256",
            master_password.encode("utf-8"),
            salt,
            _PBKDF2_ITERATIONS,
        )

    @staticmethod
    def derive_keys(master_password: str, salt: bytes) -> tuple[bytes, bytes]:
        """PBKDF2 派生 64 字节密钥 (前 32: enc_key, 后 32: hmac_key)。"""
        key_material = hashlib.pbkdf2_hmac(
            "sha256",
            master_password.encode("utf-8"),
            salt,
            _PBKDF2_ITERATIONS,
            dklen=_DERIVED_KEY_LENGTH,
        )
        return key_material[:32], key_material[32:]

    @staticmethod
    def encrypt(plaintext: str, master_password: str, version: str = "v2") -> str:
        """加密明文，默认 v2 格式（含 HMAC）。"""
        if version == "v2":
            return SimpleCrypto._encrypt_v2(plaintext, master_password)
        else:
            return SimpleCrypto._encrypt_v1(plaintext, master_password)

    @staticmethod
    def decrypt(encoded: str, master_password: str) -> str:
        """解密密文，自动识别 v1/v2 格式。"""
        if encoded.startswith(VERSION_PREFIX_V2):
            return SimpleCrypto._decrypt_v2(encoded, master_password)
        else:
            return SimpleCrypto._decrypt_v1(encoded, master_password)

    @staticmethod
    def create_token(master_password: str) -> str:
        """创建验证令牌（v2 格式加密固定字符串）。"""
        return SimpleCrypto.encrypt("PIM_VALID_TOKEN", master_password, version="v2")

    @staticmethod
    def verify_token(master_password: str, token: str) -> bool:
        """验证主密码是否与令牌匹配。自动处理 v1/v2 格式。"""
        try:
            result = SimpleCrypto.decrypt(token, master_password)
            return result == "PIM_VALID_TOKEN"
        except (ValueError, CryptoError, UnicodeDecodeError):
            return False

    @staticmethod
    def get_password_strength(password: str) -> dict:
        """评估密码强度。返回 {level: str, score: int}。

        score: 0-4 -> level: "weak"/"fair"/"medium"/"strong"/"very_strong"
        """
        score = 0
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if any(c.islower() for c in password) and any(c.isupper() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 0.5
        if any(not c.isalnum() for c in password):
            score += 0.5

        score = int(score)
        levels = {0: "weak", 1: "fair", 2: "medium", 3: "strong", 4: "very_strong"}
        return {"level": levels.get(score, "weak"), "score": score}

    # ---- v1 加解密（向后兼容） ----

    @staticmethod
    def _encrypt_v1(plaintext: str, master_password: str) -> str:
        """v1 加密（无 HMAC）。"""
        salt = secrets.token_bytes(_SALT_LENGTH)
        key = SimpleCrypto.derive_key(master_password, salt)
        nonce = secrets.token_bytes(_NONCE_LENGTH)

        plain_bytes = plaintext.encode("utf-8")
        keystream = SimpleCrypto._generate_keystream(key, nonce, len(plain_bytes))
        ciphertext = bytes(a ^ b for a, b in zip(plain_bytes, keystream))

        return base64.b64encode(salt + nonce + ciphertext).decode()

    @staticmethod
    def _decrypt_v1(encoded: str, master_password: str) -> str:
        """v1 解密（无 HMAC 验证）。"""
        try:
            data = base64.b64decode(encoded)
        except Exception as e:
            raise ValueError("密文格式错误") from e

        if len(data) < _SALT_LENGTH + _NONCE_LENGTH + 1:
            raise ValueError("密文数据不完整")

        salt = data[:_SALT_LENGTH]
        nonce = data[_SALT_LENGTH:_SALT_LENGTH + _NONCE_LENGTH]
        ciphertext = data[_SALT_LENGTH + _NONCE_LENGTH:]

        key = SimpleCrypto.derive_key(master_password, salt)
        keystream = SimpleCrypto._generate_keystream(key, nonce, len(ciphertext))
        plain_bytes = bytes(a ^ b for a, b in zip(ciphertext, keystream))

        try:
            return plain_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise ValueError("主密码错误或数据已损坏") from e

    # ---- v2 加解密（含 HMAC 认证） ----

    @staticmethod
    def _encrypt_v2(plaintext: str, master_password: str) -> str:
        """v2 加密：Encrypt-then-MAC。"""
        salt = secrets.token_bytes(_SALT_LENGTH)
        enc_key, hmac_key = SimpleCrypto.derive_keys(master_password, salt)
        nonce = secrets.token_bytes(_NONCE_LENGTH)

        plain_bytes = plaintext.encode("utf-8")
        keystream = SimpleCrypto._generate_keystream(enc_key, nonce, len(plain_bytes))
        ciphertext = bytes(a ^ b for a, b in zip(plain_bytes, keystream))

        # HMAC-SHA256(nonce + ciphertext)
        mac = hmac.new(hmac_key, nonce + ciphertext, hashlib.sha256).digest()

        payload = salt + nonce + ciphertext + mac
        return VERSION_PREFIX_V2 + base64.b64encode(payload).decode()

    @staticmethod
    def _decrypt_v2(encoded: str, master_password: str) -> str:
        """v2 解密：先验证 HMAC，再解密。"""
        if not encoded.startswith(VERSION_PREFIX_V2):
            raise CryptoError("不是 v2 格式密文")

        try:
            data = base64.b64decode(encoded[len(VERSION_PREFIX_V2):])
        except Exception as e:
            raise CryptoError("密文格式错误") from e

        min_length = _SALT_LENGTH + _NONCE_LENGTH + _HMAC_LENGTH
        if len(data) < min_length:
            raise CryptoError("密文数据不完整")

        salt = data[:_SALT_LENGTH]
        nonce = data[_SALT_LENGTH:_SALT_LENGTH + _NONCE_LENGTH]
        mac = data[-_HMAC_LENGTH:]
        ciphertext = data[_SALT_LENGTH + _NONCE_LENGTH:-_HMAC_LENGTH]

        enc_key, hmac_key = SimpleCrypto.derive_keys(master_password, salt)

        # 验证 HMAC
        expected_mac = hmac.new(hmac_key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            raise CryptoError("主密码错误或密文已被篡改")

        keystream = SimpleCrypto._generate_keystream(enc_key, nonce, len(ciphertext))
        plain_bytes = bytes(a ^ b for a, b in zip(ciphertext, keystream))

        try:
            return plain_bytes.decode("utf-8")
        except UnicodeDecodeError as e:
            raise CryptoError("解密后数据损坏") from e

    # ---- 密钥流生成 ----

    @staticmethod
    def _generate_keystream(key: bytes, nonce: bytes, length: int) -> bytes:
        """使用 SHA-256 生成指定长度的密钥流（counter 模式）。"""
        keystream = b""
        counter = 0
        while len(keystream) < length:
            keystream += hashlib.sha256(
                key + nonce + struct.pack(">I", counter)
            ).digest()
            counter += 1
        return keystream[:length]
