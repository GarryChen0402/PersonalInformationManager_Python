"""状态记录数据模型。"""

from dataclasses import dataclass, asdict, fields


@dataclass
class StatusRecord:
    """日常状态记录。"""

    id: str = ""
    date: str = ""           # YYYY-MM-DD
    mood: int = 3            # 心情 1-5
    energy: int = 3          # 精力 1-5
    focus: int = 3           # 专注度 1-5
    weight: float = 0.0      # 体重 kg
    sleep_hours: float = 0.0 # 睡眠时长
    note: str = ""
    created_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "StatusRecord":
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})
