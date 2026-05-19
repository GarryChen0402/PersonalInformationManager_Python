"""个人档案数据模型。"""

from dataclasses import dataclass, asdict, fields


@dataclass
class Profile:
    """个人基本身份信息。"""

    name: str = ""
    gender: str = ""       # 男/女/其他
    birthday: str = ""     # YYYY-MM-DD
    phone: str = ""
    email: str = ""
    address: str = ""
    wechat: str = ""
    qq: str = ""
    github: str = ""
    blog: str = ""
    bio: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Profile":
        valid_fields = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in valid_fields})
