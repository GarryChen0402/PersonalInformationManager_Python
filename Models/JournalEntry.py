"""日记条目模型。"""

from dataclasses import dataclass, asdict, fields


@dataclass
class JournalEntry:
    """日记条目，按日期唯一。"""
    id: str = ""
    date: str = ""              # YYYY-MM-DD（唯一）
    title: str = ""
    content: str = ""
    word_count: int = 0
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "JournalEntry":
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)
