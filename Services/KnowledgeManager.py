"""知识管理业务逻辑 — 笔记 + 电子书。"""

import os
import shutil
import subprocess
import uuid
import sys

from Core.Config import KNOWLEDGE_PATH, BOOKS_DIR
from Core.Exceptions import ValidationError
from Core.Storage import JSONFileStorage
from Models.Knowledge import KnowledgeItem


class KnowledgeManager:
    """知识管理器，统一管理笔记和电子书。"""

    VALID_CATEGORIES = ["技术", "生活", "读书", "工作", "其他"]

    def __init__(self):
        self.storage = JSONFileStorage(KNOWLEDGE_PATH)
        os.makedirs(BOOKS_DIR, exist_ok=True)

    # ==== 通用 ====

    def get_all(self, item_type: str | None = None) -> list[KnowledgeItem]:
        """获取所有知识条目，可按类型筛选。按更新时间倒序。"""
        records = self.storage.get_all()
        if item_type:
            records = [r for r in records if r.get("item_type") == item_type]
        records.sort(key=lambda r: r.get("updated_at", r.get("created_at", "")), reverse=True)
        return [KnowledgeItem.from_dict(r) for r in records]

    def get_by_id(self, item_id: str) -> KnowledgeItem | None:
        record = self.storage.get_by_id(item_id)
        return KnowledgeItem.from_dict(record) if record else None

    def get_by_category(self, category: str, item_type: str | None = None) -> list[KnowledgeItem]:
        """按类别筛选。"""
        records = self.storage.query(category=category)
        if item_type:
            records = [r for r in records if r.get("item_type") == item_type]
        records.sort(key=lambda r: r.get("updated_at", r.get("created_at", "")), reverse=True)
        return [KnowledgeItem.from_dict(r) for r in records]

    def search(self, keyword: str) -> list[KnowledgeItem]:
        """按标题、关键词、内容模糊搜索。"""
        all_records = self.storage.get_all()
        kw = keyword.lower()
        results = []
        for r in all_records:
            title = r.get("title", "").lower()
            keywords = " ".join(r.get("keywords", [])).lower()
            content = r.get("content", "").lower()
            if kw in title or kw in keywords or kw in content:
                results.append(r)
        results.sort(key=lambda r: r.get("updated_at", r.get("created_at", "")), reverse=True)
        return [KnowledgeItem.from_dict(r) for r in results]

    def delete_item(self, item_id: str, delete_file: bool = False) -> bool:
        """删除知识条目。若为电子书且 delete_file=True，同时删除 PDF 文件。"""
        record = self.storage.get_by_id(item_id)
        if record and record.get("item_type") == "ebook" and delete_file:
            file_path = record.get("file_path", "")
            if file_path:
                abs_path = os.path.join(os.path.dirname(KNOWLEDGE_PATH), file_path)
                if os.path.exists(abs_path):
                    os.remove(abs_path)
        return self.storage.delete(item_id)

    def get_all_categories(self, item_type: str | None = None) -> list[str]:
        records = self.storage.get_all()
        if item_type:
            records = [r for r in records if r.get("item_type") == item_type]
        return sorted({r.get("category", "") for r in records if r.get("category")})

    def get_all_keywords(self) -> list[str]:
        records = self.storage.get_all()
        all_kw = set()
        for r in records:
            for kw in r.get("keywords", []):
                all_kw.add(kw)
        return sorted(all_kw)

    def get_statistics(self) -> dict:
        records = self.storage.get_all()
        notes = [r for r in records if r.get("item_type") == "note"]
        ebooks = [r for r in records if r.get("item_type") == "ebook"]

        by_category = {}
        for r in records:
            cat = r.get("category", "其他")
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total_notes": len(notes),
            "total_ebooks": len(ebooks),
            "by_category": by_category,
            "all_keywords": self.get_all_keywords(),
        }

    # ==== 笔记 ====

    def create_note(self, title: str, category: str, keywords: list[str],
                    content: str = "") -> KnowledgeItem:
        """创建文本笔记。"""
        if not title.strip():
            raise ValidationError("笔记标题不能为空")

        record = {
            "item_type": "note",
            "title": title.strip(),
            "category": category if category in self.VALID_CATEGORIES else "其他",
            "keywords": list(keywords),
            "content": content,
            "file_path": "",
            "file_size": 0,
        }
        saved = self.storage.add(record)
        return KnowledgeItem.from_dict(saved)

    def update_note(self, note_id: str, **updates) -> KnowledgeItem:
        """更新笔记内容。"""
        if "title" in updates and not updates["title"].strip():
            raise ValidationError("笔记标题不能为空")
        # 移除电子书专用字段
        updates.pop("file_path", None)
        updates.pop("file_size", None)
        updates["item_type"] = "note"
        updated = self.storage.update(note_id, updates)
        return KnowledgeItem.from_dict(updated)

    # ==== 电子书 ====

    def import_ebook(self, source_path: str, title: str, category: str,
                     keywords: list[str]) -> KnowledgeItem:
        """导入 PDF 电子书：
        1. 校验 PDF 文件头
        2. 复制到 Data/books/ 目录
        3. 创建元数据保存
        """
        if not os.path.exists(source_path):
            raise ValidationError("源文件不存在")

        # 校验 PDF 文件头
        self._validate_pdf(source_path)

        if not title.strip():
            title = os.path.splitext(os.path.basename(source_path))[0]

        file_size = os.path.getsize(source_path)

        # 生成目标文件名 (避免冲突)
        ext = os.path.splitext(source_path)[1] or ".pdf"
        target_name = f"{uuid.uuid4().hex}{ext}"
        target_path = os.path.join(BOOKS_DIR, target_name)

        shutil.copy2(source_path, target_path)

        # 存储相对路径
        relative_path = os.path.join("books", target_name)

        record = {
            "item_type": "ebook",
            "title": title.strip(),
            "category": category if category in self.VALID_CATEGORIES else "其他",
            "keywords": list(keywords),
            "content": "",
            "file_path": relative_path,
            "file_size": file_size,
        }
        saved = self.storage.add(record)
        return KnowledgeItem.from_dict(saved)

    def update_ebook_info(self, ebook_id: str, **updates) -> KnowledgeItem:
        """更新电子书元数据（标题、类别、关键词），不修改文件。"""
        updates.pop("content", None)
        updates.pop("file_path", None)
        updates.pop("file_size", None)
        updates["item_type"] = "ebook"
        updated = self.storage.update(ebook_id, updates)
        return KnowledgeItem.from_dict(updated)

    def open_ebook(self, ebook_id: str) -> None:
        """调用系统默认程序打开 PDF 文件。"""
        file_path = self.get_ebook_file_path(ebook_id)
        if not file_path:
            raise ValidationError("找不到对应的 PDF 文件")

        if sys.platform == "win32":
            os.startfile(file_path)
        elif sys.platform == "darwin":
            subprocess.run(["open", file_path])
        else:
            subprocess.run(["xdg-open", file_path])

    def get_ebook_file_path(self, ebook_id: str) -> str | None:
        """获取电子书 PDF 文件的绝对路径。"""
        record = self.storage.get_by_id(ebook_id)
        if not record or record.get("item_type") != "ebook":
            return None

        relative_path = record.get("file_path", "")
        if not relative_path:
            return None

        abs_path = os.path.join(os.path.dirname(KNOWLEDGE_PATH), relative_path)
        if os.path.exists(abs_path):
            return abs_path
        return None

    @staticmethod
    def _validate_pdf(file_path: str) -> None:
        """校验文件是否为有效 PDF（检查文件头 %PDF）。"""
        try:
            with open(file_path, "rb") as f:
                header = f.read(4)
                if header != b"%PDF":
                    raise ValidationError("所选文件不是有效的 PDF 文件")
        except OSError as e:
            raise ValidationError(f"无法读取文件: {e}") from e
