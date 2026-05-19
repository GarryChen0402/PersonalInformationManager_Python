"""密码条目数据模型。"""

from dataclasses import dataclass, asdict, fields


@dataclass
class PasswordEntry:
    """账号密码记录。password 字段以 base64 编码存储。"""

    id: str = ""
    platform: str = ""      # 平台名称
    url: str = ""           # 网址
    username: str = ""      # 账号
    password: str = ""      # base64 编码后的密码
    note: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "PasswordEntry":
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})
