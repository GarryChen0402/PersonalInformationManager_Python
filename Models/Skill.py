"""技能数据模型。"""

from dataclasses import dataclass, asdict, fields


@dataclass
class Skill:
    """个人技能记录。"""

    id: str = ""
    name: str = ""
    category: str = ""       # 编程语言/框架/工具/语言/其他
    level: int = 1           # 熟练度 1-5
    hours_spent: float = 0.0 # 累计学习时长
    description: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Skill":
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})
