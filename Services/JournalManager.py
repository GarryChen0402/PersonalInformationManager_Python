"""日记管理业务逻辑。"""

from datetime import datetime

import Core.Config as Config
from Core.Exceptions import ValidationError
from Core.Storage import JSONFileStorage
from Models.JournalEntry import JournalEntry


class JournalManager:
    """日记条目管理器，按日期唯一。"""

    def __init__(self):
        self.storage = JSONFileStorage(Config.JOURNAL_PATH)

    # ---- 查询 ----

    def get_entry(self, date: str) -> JournalEntry | None:
        """按日期获取日记条目。"""
        self._validate_date(date)
        records = self.storage.query(date=date)
        return JournalEntry.from_dict(records[0]) if records else None

    def get_or_create(self, date: str) -> JournalEntry:
        """获取或创建指定日期的日记条目。"""
        entry = self.get_entry(date)
        if entry:
            return entry
        data = {"date": date, "title": "", "content": "", "word_count": 0}
        saved = self.storage.add(data)
        return JournalEntry.from_dict(saved)

    def get_by_id(self, entry_id: str) -> JournalEntry | None:
        """按 ID 获取日记条目。"""
        record = self.storage.get_by_id(entry_id)
        return JournalEntry.from_dict(record) if record else None

    def get_all(self, order: str = "desc") -> list[JournalEntry]:
        """获取所有日记条目。order: "desc" 按日期倒序 / "asc" 按日期正序。"""
        records = self.storage.get_all()
        reverse = order == "desc"
        records.sort(key=lambda r: r.get("date", ""), reverse=reverse)
        return [JournalEntry.from_dict(r) for r in records]

    def get_by_date_range(self, start_date: str, end_date: str) -> list[JournalEntry]:
        """按日期范围筛选日记条目。"""
        records = self.storage.get_all()
        results = [
            r for r in records
            if start_date <= r.get("date", "") <= end_date
        ]
        results.sort(key=lambda r: r.get("date", ""), reverse=True)
        return [JournalEntry.from_dict(r) for r in results]

    # ---- 保存 ----

    def save_entry(self, date: str, title: str, content: str) -> JournalEntry:
        """保存日记条目。date 已存在则更新，否则创建。"""
        self._validate_date(date)
        word_count = len(content.replace("\n", " ").split()) if content.strip() else 0

        existing = self.get_entry(date)
        if existing:
            updated = self.storage.update(existing.id, {
                "title": title.strip(),
                "content": content,
                "word_count": word_count,
            })
            return JournalEntry.from_dict(updated)
        else:
            data = {
                "date": date,
                "title": title.strip(),
                "content": content,
                "word_count": word_count,
            }
            saved = self.storage.add(data)
            return JournalEntry.from_dict(saved)

    # ---- 删除 ----

    def delete_entry(self, date: str) -> bool:
        """删除指定日期的日记条目。"""
        entry = self.get_entry(date)
        if entry:
            return self.storage.delete(entry.id)
        return False

    # ---- 搜索 ----

    def search(self, keyword: str) -> list[JournalEntry]:
        """按标题和正文搜索日记条目。"""
        if not keyword:
            return []
        kw = keyword.lower()
        all_entries = self.get_all()
        return [
            e for e in all_entries
            if kw in e.title.lower() or kw in e.content.lower()
        ]

    # ---- 统计 ----

    def get_statistics(self) -> dict:
        """获取日记统计信息。"""
        entries = self.get_all()
        total_words = sum(e.word_count for e in entries)
        return {
            "total_entries": len(entries),
            "total_words": total_words,
            "avg_words": round(total_words / len(entries)) if entries else 0,
            "current_streak": self._get_journal_streak(entries),
        }

    def get_dates_with_entries(self) -> set[str]:
        """获取所有有日记的日期集合（用于日历标记）。"""
        entries = self.get_all()
        return {e.date for e in entries}

    def _get_journal_streak(self, entries: list[JournalEntry]) -> int:
        """计算日记连续天数。"""
        if not entries:
            return 0
        today = datetime.now().strftime("%Y-%m-%d")
        date_set = {e.date for e in entries}

        streak = 0
        current = today
        while current in date_set:
            streak += 1
            from datetime import timedelta
            dt = datetime.strptime(current, "%Y-%m-%d") - timedelta(days=1)
            current = dt.strftime("%Y-%m-%d")
        return streak

    # ---- 导出 ----

    def export_single(self, date: str, output_path: str, fmt: str = "md") -> str:
        """导出单篇日记为 Markdown 文件。"""
        entry = self.get_entry(date)
        if not entry:
            raise ValidationError(f"日期 {date} 没有日记条目")

        content = self._to_markdown(entry)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(content)
        return output_path

    def export_range(self, start_date: str, end_date: str,
                     output_path: str, fmt: str = "md") -> str:
        """导出一段时间范围的日记为 Markdown 文件。"""
        entries = self.get_by_date_range(start_date, end_date)
        if not entries:
            raise ValidationError(f"{start_date} 至 {end_date} 没有日记条目")

        parts = [self._to_markdown(e) for e in sorted(entries, key=lambda e: e.date)]
        full = "\n\n---\n\n".join(parts)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full)
        return output_path

    def _to_markdown(self, entry: JournalEntry) -> str:
        """将单篇日记转换为 Markdown 格式。"""
        lines = [
            "---",
            f"date: {entry.date}",
            f"title: \"{entry.title}\"" if entry.title else "",
            f"word_count: {entry.word_count}",
            f"updated_at: {entry.updated_at}",
            "---",
            "",
        ]
        if entry.title:
            lines.append(f"# {entry.title}")
            lines.append("")
        lines.append(entry.content)
        return "\n".join(lines)

    # ---- 校验 ----

    @staticmethod
    def _validate_date(date_str: str) -> None:
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ValidationError("日期格式错误，请使用 YYYY-MM-DD 格式")
