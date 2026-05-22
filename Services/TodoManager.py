"""待办事项管理业务逻辑。"""

from datetime import datetime

import Core.Config as Config
from Core.Exceptions import ValidationError
from Core.Storage import JSONFileStorage
from Models.TodoItem import TodoItem

PRIORITY_ORDER = {"high": 0, "mid": 1, "low": 2}


class TodoManager:
    """待办事项管理器，提供增删改查与完成切换。"""

    VALID_CATEGORIES = ["工作", "学习", "生活", "其他"]
    VALID_PRIORITIES = ["high", "mid", "low"]

    def __init__(self):
        self.storage = JSONFileStorage(Config.TODO_PATH)

    # ---- 增 ----

    def add_todo(self, title: str, description: str = "",
                 priority: str = "mid", due_date: str = "",
                 category: str = "") -> TodoItem:
        if not title.strip():
            raise ValidationError("待办标题不能为空")
        if priority not in self.VALID_PRIORITIES:
            raise ValidationError(f"优先级必须是 {'/'.join(self.VALID_PRIORITIES)}")
        if due_date:
            try:
                datetime.strptime(due_date, "%Y-%m-%d")
            except ValueError:
                raise ValidationError("日期格式错误，请使用 YYYY-MM-DD 格式")

        record = {
            "title": title.strip(),
            "description": description.strip(),
            "priority": priority,
            "due_date": due_date.strip(),
            "category": category if category in self.VALID_CATEGORIES else "",
            "completed": False,
            "completed_at": "",
        }
        saved = self.storage.add(record)
        return TodoItem.from_dict(saved)

    # ---- 查 ----

    def get_all(self, status: str | None = None) -> list[TodoItem]:
        """获取所有待办。status: "active" / "completed" / None(全部)。"""
        records = self.storage.get_all()
        if status == "active":
            records = [r for r in records if not r.get("completed", False)]
        elif status == "completed":
            records = [r for r in records if r.get("completed", False)]
        return self._sort([TodoItem.from_dict(r) for r in records])

    def get_by_id(self, todo_id: str) -> TodoItem | None:
        record = self.storage.get_by_id(todo_id)
        return TodoItem.from_dict(record) if record else None

    def get_by_category(self, category: str, status: str | None = None) -> list[TodoItem]:
        items = self.get_all(status=status)
        return [i for i in items if i.category == category]

    def search(self, keyword: str) -> list[TodoItem]:
        all_items = self.get_all()
        kw = keyword.lower()
        results = [i for i in all_items
                   if kw in i.title.lower() or kw in i.description.lower()]
        return results

    # ---- 改 ----

    def update_todo(self, todo_id: str, **updates) -> TodoItem:
        if "title" in updates and not updates["title"].strip():
            raise ValidationError("待办标题不能为空")
        if "priority" in updates and updates["priority"] not in self.VALID_PRIORITIES:
            raise ValidationError(f"优先级必须是 {'/'.join(self.VALID_PRIORITIES)}")
        if "due_date" in updates and updates["due_date"]:
            try:
                datetime.strptime(updates["due_date"], "%Y-%m-%d")
            except ValueError:
                raise ValidationError("日期格式错误，请使用 YYYY-MM-DD 格式")

        updated = self.storage.update(todo_id, updates)
        return TodoItem.from_dict(updated)

    def toggle_complete(self, todo_id: str) -> TodoItem:
        item = self.get_by_id(todo_id)
        if not item:
            raise ValidationError("待办事项不存在")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if item.completed:
            updated = self.storage.update(todo_id, {
                "completed": False, "completed_at": ""
            })
        else:
            updated = self.storage.update(todo_id, {
                "completed": True, "completed_at": now
            })
        return TodoItem.from_dict(updated)

    # ---- 删 ----

    def delete_todo(self, todo_id: str) -> bool:
        return self.storage.delete(todo_id)

    def batch_delete_completed(self) -> int:
        records = self.storage.get_all()
        count = 0
        for r in records:
            if r.get("completed", False):
                self.storage.delete(r["id"])
                count += 1
        return count

    # ---- 统计 ----

    def get_statistics(self) -> dict:
        records = self.storage.get_all()
        total = len(records)
        completed = sum(1 for r in records if r.get("completed", False))
        active = total - completed
        overdue = sum(1 for r in records
                      if not r.get("completed") and r.get("due_date")
                      and r["due_date"] < datetime.now().strftime("%Y-%m-%d"))
        return {
            "total": total,
            "active": active,
            "completed": completed,
            "overdue": overdue,
        }

    def get_overdue(self) -> list[TodoItem]:
        today = datetime.now().strftime("%Y-%m-%d")
        records = self.storage.get_all()
        overdue = [r for r in records
                   if not r.get("completed") and r.get("due_date")
                   and r["due_date"] < today]
        return self._sort([TodoItem.from_dict(r) for r in overdue])

    # ---- 辅助 ----

    @staticmethod
    def _sort(items: list[TodoItem]) -> list[TodoItem]:
        """排序：逾期优先 → 优先级 → 截止日期 → 创建时间倒序。"""
        def sort_key(item: TodoItem):
            overdue = 1 if item.is_overdue() else 0
            prio = PRIORITY_ORDER.get(item.priority, 2)
            due = item.due_date or "9999-12-31"
            created = item.created_at or ""
            return (-overdue, prio, due, created)
        items.sort(key=sort_key)
        return items
