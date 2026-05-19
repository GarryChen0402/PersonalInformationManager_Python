"""KnowledgeManager 单元测试。"""

import os
import tempfile
import unittest

import Core.Config as Config
from Core.Exceptions import ValidationError
from Services.KnowledgeManager import KnowledgeManager


class TestKnowledgeManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmpdir = tempfile.mkdtemp()
        cls.orig_knowledge = Config.KNOWLEDGE_PATH
        cls.orig_books = Config.BOOKS_DIR
        Config.KNOWLEDGE_PATH = os.path.join(cls.tmpdir, "knowledge.json")
        Config.BOOKS_DIR = os.path.join(cls.tmpdir, "books")

    @classmethod
    def tearDownClass(cls):
        Config.KNOWLEDGE_PATH = cls.orig_knowledge
        Config.BOOKS_DIR = cls.orig_books
        for root, dirs, files in os.walk(cls.tmpdir, topdown=False):
            for f in files:
                os.unlink(os.path.join(root, f))
            for d in dirs:
                os.rmdir(os.path.join(root, d))
        os.rmdir(cls.tmpdir)

    def setUp(self):
        if os.path.exists(Config.KNOWLEDGE_PATH):
            os.remove(Config.KNOWLEDGE_PATH)
        self.manager = KnowledgeManager()

    # ==== 笔记 ====

    def test_create_note(self):
        note = self.manager.create_note(
            "测试笔记", "技术", ["Python", "Tkinter"], "这是内容"
        )
        self.assertEqual(note.item_type, "note")
        self.assertEqual(note.title, "测试笔记")
        self.assertEqual(note.category, "技术")
        self.assertEqual(note.keywords, ["Python", "Tkinter"])
        self.assertEqual(note.content, "这是内容")

    def test_create_note_empty_title(self):
        with self.assertRaises(ValidationError):
            self.manager.create_note("  ", "技术", [])

    def test_create_note_default_category(self):
        note = self.manager.create_note("Note", "未知类别", [])
        self.assertEqual(note.category, "其他")

    def test_update_note(self):
        note = self.manager.create_note("原标题", "技术", [])
        updated = self.manager.update_note(note.id, title="新标题", content="新内容")
        self.assertEqual(updated.title, "新标题")
        self.assertEqual(updated.content, "新内容")

    def test_update_note_empty_title(self):
        note = self.manager.create_note("标题", "技术", [])
        with self.assertRaises(ValidationError):
            self.manager.update_note(note.id, title="  ")

    # ==== 电子书 ====

    def test_validate_pdf_valid(self):
        tmp_pdf = os.path.join(self.tmpdir, "valid.pdf")
        with open(tmp_pdf, "wb") as f:
            f.write(b"%PDF-1.4\n%some content")
        self.manager._validate_pdf(tmp_pdf)

    def test_validate_pdf_invalid(self):
        tmp_file = os.path.join(self.tmpdir, "not_pdf.txt")
        with open(tmp_file, "wb") as f:
            f.write(b"Hello World")
        with self.assertRaises(ValidationError):
            self.manager._validate_pdf(tmp_file)

    def test_validate_pdf_nonexistent(self):
        with self.assertRaises(ValidationError):
            self.manager._validate_pdf("/nonexistent/file.pdf")

    def test_import_ebook(self):
        tmp_pdf = os.path.join(self.tmpdir, "test.pdf")
        with open(tmp_pdf, "wb") as f:
            f.write(b"%PDF-1.4\n%content")

        ebook = self.manager.import_ebook(
            tmp_pdf, "Python指南", "技术", ["Python", "编程"]
        )
        self.assertEqual(ebook.item_type, "ebook")
        self.assertEqual(ebook.title, "Python指南")
        self.assertEqual(ebook.keywords, ["Python", "编程"])
        self.assertTrue(ebook.file_path)
        self.assertGreater(ebook.file_size, 0)

        # 文件已复制到 books 目录
        abs_path = self.manager.get_ebook_file_path(ebook.id)
        self.assertIsNotNone(abs_path)
        self.assertTrue(os.path.exists(abs_path))

    def test_import_ebook_auto_title(self):
        tmp_pdf = os.path.join(self.tmpdir, "PythonGuide.pdf")
        with open(tmp_pdf, "wb") as f:
            f.write(b"%PDF-1.4\n%content")

        ebook = self.manager.import_ebook(tmp_pdf, "", "技术", [])
        self.assertEqual(ebook.title, "PythonGuide")

    def test_import_ebook_nonexistent(self):
        with self.assertRaises(ValidationError):
            self.manager.import_ebook("/no/file.pdf", "Title", "技术", [])

    # ==== 搜索与筛选 ====

    def test_search(self):
        self.manager.create_note("Python笔记", "技术", ["Python"], "学Python")
        self.manager.create_note("读书笔记", "读书", ["阅读"], "读了一本书")
        results = self.manager.search("python")
        self.assertEqual(len(results), 1)
        results2 = self.manager.search("读了")
        self.assertEqual(len(results2), 1)

    def test_get_by_category(self):
        self.manager.create_note("N1", "技术", [])
        self.manager.create_note("N2", "生活", [])
        results = self.manager.get_by_category("技术")
        self.assertEqual(len(results), 1)

    def test_get_all_by_type(self):
        self.manager.create_note("N1", "技术", [])
        self.manager.create_note("N2", "生活", [])
        notes = self.manager.get_all(item_type="note")
        ebooks = self.manager.get_all(item_type="ebook")
        self.assertEqual(len(notes), 2)
        self.assertEqual(len(ebooks), 0)

    # ==== 统计 ====

    def test_statistics(self):
        self.manager.create_note("N1", "技术", ["Python"])
        self.manager.create_note("N2", "技术", ["Java"])
        stats = self.manager.get_statistics()
        self.assertEqual(stats["total_notes"], 2)
        self.assertEqual(stats["total_ebooks"], 0)
        self.assertEqual(stats["by_category"]["技术"], 2)

    def test_get_all_keywords(self):
        self.manager.create_note("N1", "技术", ["Python", "GUI"])
        self.manager.create_note("N2", "生活", ["Python"])
        kw = self.manager.get_all_keywords()
        self.assertIn("Python", kw)
        self.assertIn("GUI", kw)

    # ==== 删除 ====

    def test_delete_note(self):
        note = self.manager.create_note("Del", "技术", [])
        self.assertTrue(self.manager.delete_item(note.id))
        self.assertIsNone(self.manager.get_by_id(note.id))

    def test_delete_ebook_with_file(self):
        tmp_pdf = os.path.join(self.tmpdir, "to_delete.pdf")
        with open(tmp_pdf, "wb") as f:
            f.write(b"%PDF-1.4\n%content")

        ebook = self.manager.import_ebook(tmp_pdf, "Del", "技术", [])
        abs_path = self.manager.get_ebook_file_path(ebook.id)
        self.assertTrue(os.path.exists(abs_path))

        self.assertTrue(self.manager.delete_item(ebook.id, delete_file=True))
        self.assertFalse(os.path.exists(abs_path))


if __name__ == "__main__":
    unittest.main()
