"""PasswordManager 单元测试。"""

import os
import tempfile
import unittest

import Core.Config as Config
from Core.Exceptions import ValidationError
from Services.PasswordManager import PasswordManager


class TestPasswordManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.orig_path = Config.PASSWORD_PATH
        Config.PASSWORD_PATH = os.path.join(cls.tmpdir, "passwords.json")

    @classmethod
    def tearDownClass(cls):
        Config.PASSWORD_PATH = cls.orig_path
        for f in os.listdir(cls.tmpdir):
            os.unlink(os.path.join(cls.tmpdir, f))
        os.rmdir(cls.tmpdir)

    def setUp(self):
        if os.path.exists(Config.PASSWORD_PATH):
            os.remove(Config.PASSWORD_PATH)
        self.manager = PasswordManager()

    def test_encode_decode(self):
        encoded = self.manager._encode("mypassword")
        self.assertNotEqual(encoded, "mypassword")
        decoded = self.manager._decode(encoded)
        self.assertEqual(decoded, "mypassword")

    def test_add_entry(self):
        entry = self.manager.add_entry(
            "GitHub", "https://github.com", "user", "secret123"
        )
        self.assertEqual(entry.platform, "GitHub")
        self.assertEqual(entry.url, "https://github.com")
        self.assertEqual(entry.username, "user")
        self.assertNotEqual(entry.password, "secret123")

    def test_add_entry_empty_platform(self):
        with self.assertRaises(ValidationError):
            self.manager.add_entry("  ", "", "", "pass")

    def test_add_entry_empty_password(self):
        with self.assertRaises(ValidationError):
            self.manager.add_entry("Site", "", "", "")

    def test_get_decrypted_password(self):
        entry = self.manager.add_entry("Site", "", "user", "plain123")
        decrypted = self.manager.get_decrypted_password(entry.id)
        self.assertEqual(decrypted, "plain123")

    def test_get_decrypted_password_not_found(self):
        with self.assertRaises(ValidationError):
            self.manager.get_decrypted_password("nonexistent")

    def test_update_entry(self):
        entry = self.manager.add_entry("Old", "", "user", "oldpass")
        updated = self.manager.update_entry(entry.id, platform="New", password="newpass")
        self.assertEqual(updated.platform, "New")
        decrypted = self.manager.get_decrypted_password(entry.id)
        self.assertEqual(decrypted, "newpass")

    def test_update_entry_empty_password_skipped(self):
        entry = self.manager.add_entry("Site", "", "user", "origpass")
        updated = self.manager.update_entry(entry.id, platform="New", password="")
        decrypted = self.manager.get_decrypted_password(entry.id)
        self.assertEqual(decrypted, "origpass")

    def test_update_entry_empty_platform(self):
        entry = self.manager.add_entry("Site", "", "user", "pass")
        with self.assertRaises(ValidationError):
            self.manager.update_entry(entry.id, platform="  ")

    def test_delete_entry(self):
        entry = self.manager.add_entry("Del", "", "", "pass")
        self.assertTrue(self.manager.delete_entry(entry.id))

    def test_search(self):
        self.manager.add_entry("GitHub", "https://github.com", "octocat", "pass")
        self.manager.add_entry("Gmail", "https://mail.google.com", "user", "pass")
        results = self.manager.search("github")
        self.assertEqual(len(results), 1)
        results2 = self.manager.search("user")
        self.assertEqual(len(results2), 1)

    def test_count(self):
        self.assertEqual(self.manager.count(), 0)
        self.manager.add_entry("A", "", "", "p")
        self.manager.add_entry("B", "", "", "p")
        self.assertEqual(self.manager.count(), 2)

    def test_get_all(self):
        self.manager.add_entry("B", "", "", "p")
        self.manager.add_entry("A", "", "", "p")
        entries = self.manager.get_all()
        self.assertEqual(len(entries), 2)


if __name__ == "__main__":
    unittest.main()
