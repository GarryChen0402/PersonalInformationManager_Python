"""知识条目数据模型 — 统一管理笔记和电子书。"""

from dataclasses import dataclass, asdict, fields, field


@dataclass
class KnowledgeItem:
    """知识条目，通过 item_type 区分笔记(note)和电子书(ebook)。"""

    id: str = ""
    item_type: str = "note"          # "note" 或 "ebook"
    title: str = ""
    category: str = ""               # 技术/生活/读书/工作/其他
    keywords: list = field(default_factory=list)
    # 笔记专用
    content: str = ""
    # 电子书专用
    file_path: str = ""              # PDF 相对路径 books/xxx.pdf
    file_size: int = 0               # 文件大小（字节）
    # 时间戳
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "KnowledgeItem":
        valid_fields = {f.name for f in fields(cls)}
        filtered = {k: v for k, v in data.items() if k in valid_fields}
        # 确保 keywords 是列表
        if "keywords" in filtered and not isinstance(filtered["keywords"], list):
            filtered["keywords"] = []
        return cls(**filtered)
