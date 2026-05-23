"""CryptoService 单元测试。"""

import os
import tempfile
import unittest

import Core.Config as Config
from Core.Exceptions import CryptoError
from Services.CryptoService import CryptoService


class TestCryptoService(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.orig_config_path = Config.CONFIG_PATH
        Config.CONFIG_PATH = os.path.join(cls.tmpdir, "config.json")

    @classmethod
    def tearDownClass(cls):
        Config.CONFIG_PATH = cls.orig_config_path
        # Reset CryptoService state
        CryptoService.lock()
        for f in os.listdir(cls.tmpdir):
            os.unlink(os.path.join(cls.tmpdir, f))
        os.rmdir(cls.tmpdir)

    def setUp(self):
        CryptoService.lock()
        if os.path.exists(Config.CONFIG_PATH):
            os.remove(Config.CONFIG_PATH)

    # ---- 初始状态 ----

    def test_not_configured_initially(self):
        self.assertFalse(CryptoService.is_configured())

    def test_not_unlocked_initially(self):
        self.assertFalse(CryptoService.is_unlocked())

    def test_get_key_unlocked_raises(self):
        with self.assertRaises(RuntimeError):
            CryptoService.get_key()

    # ---- 设置主密码 ----

    def test_setup_master_password(self):
        CryptoService.setup_master_password("test1234", "test1234")
        self.assertTrue(CryptoService.is_configured())
        self.assertTrue(CryptoService.is_unlocked())

    def test_setup_mismatched_passwords(self):
        with self.assertRaises(ValueError):
            CryptoService.setup_master_password("test1234", "different")

    def test_setup_short_password(self):
        with self.assertRaises(ValueError):
            CryptoService.setup_master_password("abc", "abc")

    # ---- 解锁/锁定 ----

    def test_unlock_correct_password(self):
        CryptoService.setup_master_password("test1234", "test1234")
        CryptoService.lock()
        self.assertFalse(CryptoService.is_unlocked())
        self.assertTrue(CryptoService.unlock("test1234"))
        self.assertTrue(CryptoService.is_unlocked())

    def test_unlock_wrong_password(self):
        CryptoService.setup_master_password("test1234", "test1234")
        CryptoService.lock()
        self.assertFalse(CryptoService.unlock("wrong_pwd"))
        self.assertFalse(CryptoService.is_unlocked())

    def test_unlock_without_setup(self):
        self.assertFalse(CryptoService.unlock("anything"))

    # ---- 加密/解密 ----

    def test_encrypt_decrypt(self):
        CryptoService.setup_master_password("test1234", "test1234")
        plain = "my_secret_password"
        encrypted = CryptoService.encrypt(plain)
        self.assertNotEqual(encrypted, plain)
        decrypted = CryptoService.decrypt(encrypted)
        self.assertEqual(decrypted, plain)

    def test_decrypt_with_wrong_key(self):
        CryptoService.setup_master_password("test1234", "test1234")
        encrypted = CryptoService.encrypt("secret")
        # Change master password
        CryptoService.lock()
        CryptoService.setup_master_password("newpass", "newpass")
        with self.assertRaises((ValueError, CryptoError)):
            CryptoService.decrypt(encrypted)

    def test_encrypt_without_unlock_raises(self):
        with self.assertRaises(RuntimeError):
            CryptoService.encrypt("secret")

    # ---- 修改主密码 ----

    def test_change_master_password(self):
        CryptoService.setup_master_password("oldpass", "oldpass")
        encrypted = CryptoService.encrypt("my_data")

        CryptoService.change_master_password("oldpass", "newpass")
        self.assertTrue(CryptoService.is_unlocked())

        # Old encrypted data cannot be decrypted with new key
        with self.assertRaises((ValueError, CryptoError)):
            CryptoService.decrypt(encrypted)

    def test_change_wrong_old_password(self):
        CryptoService.setup_master_password("oldpass", "oldpass")
        with self.assertRaises(ValueError):
            CryptoService.change_master_password("wrong", "newpass")

    # ---- 令牌持久化 ----

    def test_token_persists_across_instances(self):
        CryptoService.setup_master_password("test1234", "test1234")
        CryptoService.lock()

        # Simulate restart: lock clears the cached password
        self.assertFalse(CryptoService.is_unlocked())
        # But the token should still be readable
        self.assertTrue(CryptoService.is_configured())
        # And we can unlock with the correct password
        self.assertTrue(CryptoService.unlock("test1234"))

    # ---- 令牌完整生命周期 ----

    def test_full_lifecycle(self):
        # Setup
        CryptoService.setup_master_password("mypassword", "mypassword")
        self.assertTrue(CryptoService.is_configured())
        self.assertTrue(CryptoService.is_unlocked())

        # Encrypt
        encrypted = CryptoService.encrypt("top_secret")
        self.assertIsNotNone(encrypted)

        # Lock
        CryptoService.lock()
        self.assertFalse(CryptoService.is_unlocked())

        # Unlock
        self.assertTrue(CryptoService.unlock("mypassword"))

        # Decrypt
        self.assertEqual(CryptoService.decrypt(encrypted), "top_secret")


if __name__ == "__main__":
    unittest.main()
