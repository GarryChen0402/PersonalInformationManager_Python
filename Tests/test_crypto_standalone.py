"""SimpleCrypto 独立单元测试 — 测试加解密、HMAC、令牌、密码强度。"""

import unittest

from Core.Crypto import SimpleCrypto, CryptoError


class TestSimpleCrypto(unittest.TestCase):
    """SimpleCrypto 的所有方法测试。"""

    # ---- v2 加解密 ----

    def test_encrypt_decrypt_roundtrip(self):
        encrypted = SimpleCrypto.encrypt("hello world", "master123", version="v2")
        self.assertTrue(encrypted.startswith("v2:"))
        decrypted = SimpleCrypto.decrypt(encrypted, "master123")
        self.assertEqual(decrypted, "hello world")

    def test_encrypt_decrypt_unicode(self):
        text = "你好世界！Python 学习笔记 📝"
        encrypted = SimpleCrypto.encrypt(text, "密码1234", version="v2")
        decrypted = SimpleCrypto.decrypt(encrypted, "密码1234")
        self.assertEqual(decrypted, text)

    def test_encrypt_decrypt_empty_string(self):
        encrypted = SimpleCrypto.encrypt("", "master123", version="v2")
        decrypted = SimpleCrypto.decrypt(encrypted, "master123")
        self.assertEqual(decrypted, "")

    def test_encrypt_decrypt_long_text(self):
        text = "A" * 10000
        encrypted = SimpleCrypto.encrypt(text, "master123", version="v2")
        decrypted = SimpleCrypto.decrypt(encrypted, "master123")
        self.assertEqual(decrypted, text)

    def test_v2_tampered_ciphertext_raises(self):
        encrypted = SimpleCrypto.encrypt("secret", "master123", version="v2")
        # 篡改密文：修改最后一个字符
        tampered = encrypted[:-1] + ("A" if encrypted[-1] != "A" else "B")
        with self.assertRaises(CryptoError):
            SimpleCrypto.decrypt(tampered, "master123")

    def test_v2_wrong_password_raises(self):
        encrypted = SimpleCrypto.encrypt("secret", "master123", version="v2")
        with self.assertRaises(CryptoError):
            SimpleCrypto.decrypt(encrypted, "wrongpass")

    def test_v2_wrong_password_detected_by_hmac(self):
        """错误密码应被 HMAC 检测到，而非解密出乱码。"""
        encrypted = SimpleCrypto.encrypt("sensitive_data", "correct_pwd", version="v2")
        with self.assertRaises(CryptoError):
            SimpleCrypto.decrypt(encrypted, "wrong_pwd")

    # ---- v1 向后兼容 ----

    def test_v1_encrypt_decrypt_roundtrip(self):
        encrypted = SimpleCrypto.encrypt("hello", "master123", version="v1")
        self.assertFalse(encrypted.startswith("v2:"))
        decrypted = SimpleCrypto.decrypt(encrypted, "master123")
        self.assertEqual(decrypted, "hello")

    def test_v1_wrong_password_raises(self):
        encrypted = SimpleCrypto.encrypt("hello", "master123", version="v1")
        with self.assertRaises(ValueError):
            SimpleCrypto.decrypt(encrypted, "wrongpass")

    def test_v2_can_decrypt_v1(self):
        """确保 decrypt() 自动检测格式：v2 密码也可解密 v1 数据。"""
        v1_encrypted = SimpleCrypto.encrypt("data", "master123", version="v1")
        decrypted = SimpleCrypto.decrypt(v1_encrypted, "master123")
        self.assertEqual(decrypted, "data")

    def test_v1_can_decrypt_v2(self):
        """确保 decrypt() 自动路由到 _decrypt_v2。"""
        v2_encrypted = SimpleCrypto.encrypt("data", "master123", version="v2")
        decrypted = SimpleCrypto.decrypt(v2_encrypted, "master123")
        self.assertEqual(decrypted, "data")

    # ---- 密钥派生 ----

    def test_derive_key_length(self):
        key = SimpleCrypto.derive_key("master123", b"salt1234567890ab")
        self.assertEqual(len(key), 32)

    def test_derive_keys_length(self):
        enc_key, hmac_key = SimpleCrypto.derive_keys("master123", b"salt1234567890ab")
        self.assertEqual(len(enc_key), 32)
        self.assertEqual(len(hmac_key), 32)

    def test_derive_keys_different_salts(self):
        """不同 salt 应产生不同密钥。"""
        k1, h1 = SimpleCrypto.derive_keys("master123", b"aaaaaaaaaaaaaaaa")
        k2, h2 = SimpleCrypto.derive_keys("master123", b"bbbbbbbbbbbbbbbb")
        self.assertNotEqual(k1, k2)
        self.assertNotEqual(h1, h2)

    def test_derive_keys_different_passwords(self):
        """不同密码应产生不同密钥。"""
        k1, h1 = SimpleCrypto.derive_keys("password1", b"salt1234567890ab")
        k2, h2 = SimpleCrypto.derive_keys("password2", b"salt1234567890ab")
        self.assertNotEqual(k1, k2)
        self.assertNotEqual(h1, h2)

    def test_derive_key_deterministic(self):
        """相同输入应产生相同密钥。"""
        k1 = SimpleCrypto.derive_key("master123", b"salt1234567890ab")
        k2 = SimpleCrypto.derive_key("master123", b"salt1234567890ab")
        self.assertEqual(k1, k2)

    # ---- 令牌 ----

    def test_create_and_verify_token(self):
        token = SimpleCrypto.create_token("master123")
        self.assertTrue(token.startswith("v2:"))
        self.assertTrue(SimpleCrypto.verify_token("master123", token))

    def test_verify_token_wrong_password(self):
        token = SimpleCrypto.create_token("master123")
        self.assertFalse(SimpleCrypto.verify_token("wrongpass", token))

    def test_verify_token_v1_format(self):
        """确保 verify_token 也能处理 v1 格式令牌。"""
        token = SimpleCrypto.encrypt("PIM_VALID_TOKEN", "master123", version="v1")
        self.assertTrue(SimpleCrypto.verify_token("master123", token))

    def test_verify_token_corrupted(self):
        token = SimpleCrypto.create_token("master123")
        corrupted = "v2:AAAA" + token[6:]
        self.assertFalse(SimpleCrypto.verify_token("master123", corrupted))

    # ---- 密码强度 ----

    def test_password_strength_weak(self):
        result = SimpleCrypto.get_password_strength("abc")
        self.assertEqual(result["level"], "weak")
        self.assertEqual(result["score"], 0)

    def test_password_strength_fair(self):
        result = SimpleCrypto.get_password_strength("abcdefgh")
        self.assertEqual(result["level"], "fair")

    def test_password_strength_very_strong(self):
        result = SimpleCrypto.get_password_strength("MyP@ssw0rd!2024")
        self.assertIn(result["level"], ["strong", "very_strong"])
        self.assertGreaterEqual(result["score"], 3)

    def test_password_strength_empty(self):
        result = SimpleCrypto.get_password_strength("")
        self.assertEqual(result["level"], "weak")
        self.assertEqual(result["score"], 0)

    # ---- 密钥流 ----

    def test_generate_keystream_length(self):
        key = b"k" * 32
        nonce = b"n" * 16
        for length in [1, 32, 100, 1024]:
            ks = SimpleCrypto._generate_keystream(key, nonce, length)
            self.assertEqual(len(ks), length)

    def test_generate_keystream_deterministic(self):
        key = b"k" * 32
        nonce = b"n" * 16
        ks1 = SimpleCrypto._generate_keystream(key, nonce, 100)
        ks2 = SimpleCrypto._generate_keystream(key, nonce, 100)
        self.assertEqual(ks1, ks2)
