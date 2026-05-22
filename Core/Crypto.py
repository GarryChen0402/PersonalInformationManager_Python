"""SHA-256 流密码加解密工具 — 零外部依赖。"""

import base64
import hashlib
import secrets
import struct

_PBKDF2_ITERATIONS = 100000
_SALT_LENGTH = 16
_NONCE_LENGTH = 16


class SimpleCrypto:
    """使用 PBKDF2 + SHA-256 流密码进行加解密。

    比 base64 安全，比手动实现 AES 简单可靠。
    适用于个人本地使用场景。
    """

    @staticmethod
    def derive_key(master_password: str, salt: bytes) -> bytes:
        """PBKDF2 派生 256 位密钥。"""
        return hashlib.pbkdf2_hmac(
            "sha256",
            master_password.encode("utf-8"),
            salt,
            _PBKDF2_ITERATIONS,
        )

    @staticmethod
    def encrypt(plaintext: str, master_password: str) -> str:
        """加密明文，返回 base64 编码的密文。

        密文格式: base64(salt(16) + nonce(16) + ciphertext)
        """
        salt = secrets.token_bytes(_SALT_LENGTH)
        key = SimpleCrypto.derive_key(master_password, salt)
        nonce = secrets.token_bytes(_NONCE_LENGTH)

        plain_bytes = plaintext.encode("utf-8")
        keystream = SimpleCrypto._generate_keystream(key, nonce, len(plain_bytes))
        ciphertext = bytes(a ^ b for a, b in zip(plain_bytes, keystream))

        return base64.b64encode(salt + nonce + ciphertext).decode()

    @staticmethod
    def decrypt(encoded: str, master_password: str) -> str:
        """解密 base64 编码的密文，返回明文。

        密文格式错误或密码错误时抛出 ValueError。
        """
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

    @staticmethod
    def create_token(master_password: str) -> str:
        """创建验证令牌，用于验证主密码是否正确。"""
        return SimpleCrypto.encrypt("PIM_VALID_TOKEN", master_password)

    @staticmethod
    def verify_token(master_password: str, token: str) -> bool:
        """验证主密码是否与令牌匹配。"""
        try:
            result = SimpleCrypto.decrypt(token, master_password)
            return result == "PIM_VALID_TOKEN"
        except (ValueError, UnicodeDecodeError):
            return False

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
