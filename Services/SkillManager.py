"""技能管理业务逻辑。"""

import Core.Config as Config
from Core.Exceptions import ValidationError
from Core.Storage import JSONFileStorage
from Models.Skill import Skill


class SkillManager:
    """技能管理器，提供技能的增删改查与统计。"""

    VALID_CATEGORIES = ["编程语言", "框架", "工具", "语言", "其他"]

    def __init__(self):
        self.storage = JSONFileStorage(Config.SKILL_PATH)

    # ---- 增 ----

    def add_skill(self, name: str, category: str, level: int,
                  hours_spent: float, description: str = "") -> Skill:
        """添加新技能，返回 Skill 对象。"""
        if not name.strip():
            raise ValidationError("技能名称不能为空")
        if level < 1 or level > 5:
            raise ValidationError("熟练度必须在 1-5 之间")

        record = {
            "name": name.strip(),
            "category": category if category in self.VALID_CATEGORIES else "其他",
            "level": int(level),
            "hours_spent": float(hours_spent),
            "description": description.strip(),
        }
        saved = self.storage.add(record)
        return Skill.from_dict(saved)

    # ---- 查 ----

    def get_all(self) -> list[Skill]:
        """获取所有技能，按熟练度降序排列。"""
        records = self.storage.get_all()
        records.sort(key=lambda r: r.get("level", 0), reverse=True)
        return [Skill.from_dict(r) for r in records]

    def get_by_id(self, skill_id: str) -> Skill | None:
        """按 ID 获取技能。"""
        record = self.storage.get_by_id(skill_id)
        return Skill.from_dict(record) if record else None

    def get_by_category(self, category: str) -> list[Skill]:
        """按类别筛选技能。"""
        records = self.storage.query(category=category)
        records.sort(key=lambda r: r.get("level", 0), reverse=True)
        return [Skill.from_dict(r) for r in records]

    def search(self, keyword: str) -> list[Skill]:
        """按名称和描述模糊搜索。"""
        all_records = self.storage.get_all()
        kw = keyword.lower()
        results = [
            r for r in all_records
            if kw in r.get("name", "").lower()
            or kw in r.get("description", "").lower()
        ]
        results.sort(key=lambda r: r.get("level", 0), reverse=True)
        return [Skill.from_dict(r) for r in results]

    # ---- 改 ----

    def update_skill(self, skill_id: str, **updates) -> Skill:
        """更新技能字段，返回更新后的 Skill。"""
        if "level" in updates:
            level = updates["level"]
            if level < 1 or level > 5:
                raise ValidationError("熟练度必须在 1-5 之间")
            updates["level"] = int(level)
        if "hours_spent" in updates:
            updates["hours_spent"] = float(updates["hours_spent"])
        if "name" in updates and not updates["name"].strip():
            raise ValidationError("技能名称不能为空")

        updated = self.storage.update(skill_id, updates)
        return Skill.from_dict(updated)

    # ---- 删 ----

    def delete_skill(self, skill_id: str) -> bool:
        """删除技能，返回是否成功。"""
        return self.storage.delete(skill_id)

    # ---- 统计 ----

    def get_all_categories(self) -> list[str]:
        """获取所有已使用的类别（去重）。"""
        records = self.storage.get_all()
        categories = sorted({r.get("category", "") for r in records if r.get("category")})
        return categories

    def get_statistics(self) -> dict:
        """获取技能统计数据。"""
        records = self.storage.get_all()
        total = len(records)
        if total == 0:
            return {
                "total": 0, "by_category": {},
                "total_hours": 0.0, "avg_level": 0.0
            }

        by_category = {}
        total_hours = 0.0
        total_level = 0

        for r in records:
            cat = r.get("category", "其他")
            by_category[cat] = by_category.get(cat, 0) + 1
            total_hours += r.get("hours_spent", 0)
            total_level += r.get("level", 1)

        return {
            "total": total,
            "by_category": by_category,
            "total_hours": total_hours,
            "avg_level": round(total_level / total, 1),
        }
