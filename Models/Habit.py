"""习惯定义模型。"""

from dataclasses import dataclass, asdict, fields


@dataclass
class Habit:
    """习惯定义。"""
    id: str = ""
    name: str = ""
    description: str = ""
    frequency: str = "daily"       # "daily" / "weekly" / "custom"
    custom_days: int = 1           # frequency="custom" 时的间隔天数
    target_count: int = 1          # 每次目标次数
    category: str = ""             # 健康/学习/工作/生活/其他
    color: str = "#4a90d9"         # 热力图主题色
    archived: bool = False
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Habit":
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered)
