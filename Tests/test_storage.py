"""JSONFileStorage 单元测试。"""

import json
import os
import tempfile
import unittest

from Core.Storage import JSONFileStorage
from Core.Exceptions import DataLoadError, DataSaveError, RecordNotFoundError


class TestJSONFileStorage(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.path = os.path.join(self.tmpdir, "test.json")
        self.storage = JSONFileStorage(self.path)

    def tearDown(self):
        for f in os.listdir(self.tmpdir):
            os.unlink(os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def test_auto_create_file(self):
        self.assertTrue(os.path.exists(self.path))

    def test_get_all_empty(self):
        self.assertEqual(self.storage.get_all(), [])

    def test_add_record(self):
        record = self.storage.add({"name": "test"})
        self.assertIn("id", record)
        self.assertIn("created_at", record)
        self.assertEqual(record["name"], "test")

    def test_get_by_id(self):
        record = self.storage.add({"name": "find_me"})
        found = self.storage.get_by_id(record["id"])
        self.assertEqual(found["name"], "find_me")

    def test_get_by_id_not_found(self):
        self.assertIsNone(self.storage.get_by_id("nonexistent"))

    def test_query(self):
        self.storage.add({"type": "A", "val": 1})
        self.storage.add({"type": "B", "val": 2})
        self.storage.add({"type": "A", "val": 3})
        results = self.storage.query(type="A")
        self.assertEqual(len(results), 2)

    def test_query_no_match(self):
        results = self.storage.query(nonexistent_field="x")
        self.assertEqual(results, [])

    def test_search(self):
        self.storage.add({"name": "Hello World"})
        self.storage.add({"name": "Goodbye"})
        results = self.storage.search("name", "hello")
        self.assertEqual(len(results), 1)

    def test_update(self):
        record = self.storage.add({"name": "old"})
        updated = self.storage.update(record["id"], {"name": "new"})
        self.assertEqual(updated["name"], "new")
        self.assertIn("updated_at", updated)

    def test_update_not_found(self):
        with self.assertRaises(RecordNotFoundError):
            self.storage.update("nonexistent", {"name": "x"})

    def test_delete(self):
        record = self.storage.add({"name": "del"})
        self.assertTrue(self.storage.delete(record["id"]))
        self.assertIsNone(self.storage.get_by_id(record["id"]))

    def test_delete_not_found(self):
        self.assertFalse(self.storage.delete("nonexistent"))

    def test_count(self):
        self.assertEqual(self.storage.count(), 0)
        self.storage.add({"a": 1})
        self.storage.add({"a": 2})
        self.assertEqual(self.storage.count(), 2)

    def test_corrupt_json(self):
        with open(self.path, "w", encoding="utf-8") as f:
            f.write("not valid json")
        with self.assertRaises(DataLoadError):
            self.storage._load()

    def test_atomic_write(self):
        self.storage.add({"data": "important"})
        tmp_path = self.path + ".tmp"
        self.assertFalse(os.path.exists(tmp_path),
                         "tmp file should be cleaned up after save")

    def test_persistence(self):
        record = self.storage.add({"persist": True})
        storage2 = JSONFileStorage(self.path)
        found = storage2.get_by_id(record["id"])
        self.assertEqual(found["persist"], True)


if __name__ == "__main__":
    unittest.main()
