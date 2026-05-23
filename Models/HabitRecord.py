"""习惯打卡记录模型。"""

from dataclasses import dataclass, asdict, fields


@dataclass
class HabitRecord:
    """习惯打卡记录。"""
    id: str = ""
    habit_id: str = ""
    date: str = ""                 # YYYY-MM-DD
    count: int = 0                 # 实际完成次数
    note: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "HabitRecord":
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)
