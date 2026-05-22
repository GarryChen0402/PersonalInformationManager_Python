"""应用配置数据模型。"""

from dataclasses import dataclass, asdict, fields, field


@dataclass
class AppConfig:
    """应用配置，存储用户偏好和状态。"""

    theme: str = "light"
    font_size: int = 10
    master_password_token: str = ""
    last_active_module: str = "profile"
    search_history: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AppConfig":
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        if "search_history" in filtered and not isinstance(filtered["search_history"], list):
            filtered["search_history"] = []
        return cls(**filtered)
