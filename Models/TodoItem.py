"""待办事项数据模型。"""

from dataclasses import dataclass, asdict, fields
from datetime import datetime


@dataclass
class TodoItem:
    """待办事项记录。"""

    id: str = ""
    title: str = ""
    description: str = ""
    priority: str = "mid"       # high / mid / low
    due_date: str = ""          # YYYY-MM-DD
    category: str = ""          # 工作/学习/生活/其他
    completed: bool = False
    completed_at: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TodoItem":
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})

    def is_overdue(self) -> bool:
        if self.completed or not self.due_date:
            return False
        from datetime import datetime
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            return self.due_date < today
        except ValueError:
            return False
