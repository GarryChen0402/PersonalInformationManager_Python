"""应用配置管理器。"""

import json
import os

import Core.Config as Config


class ConfigManager:
    """应用配置单例管理器。"""

    _instance: "ConfigManager | None" = None

    def __new__(cls) -> "ConfigManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.config_path = Config.CONFIG_PATH
        self._data: dict = self._load()

    def _load(self) -> dict:
        """从文件加载配置。"""
        if not os.path.exists(self.config_path):
            return self._defaults()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            # 合并默认值
            defaults = self._defaults()
            for key, value in defaults.items():
                if key not in data:
                    data[key] = value
            return data
        except (json.JSONDecodeError, OSError):
            return self._defaults()

    def _save(self) -> None:
        """原子写入配置到文件。"""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        tmp = self.config_path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            os.replace(tmp, self.config_path)
        except OSError:
            pass

    @staticmethod
    def _defaults() -> dict:
        return {
            "theme": "light",
            "font_size": 10,
            "master_password_token": "",
            "last_active_module": "profile",
            "search_history": [],
            "migration": {"version": "1.0"},
        }

    # ---- 通用访问 ----

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def set(self, key: str, value) -> None:
        self._data[key] = value
        self._save()

    # ---- 便捷方法 ----

    def get_theme(self) -> str:
        return self._data.get("theme", "light")

    def set_theme(self, theme: str) -> None:
        self._data["theme"] = theme
        self._save()

    def get_font_size(self) -> int:
        return self._data.get("font_size", 10)

    def set_font_size(self, size: int) -> None:
        self._data["font_size"] = max(8, min(16, size))
        self._save()

    def get_master_password_token(self) -> str:
        return self._data.get("master_password_token", "")

    def set_master_password_token(self, token: str) -> None:
        self._data["master_password_token"] = token
        self._save()

    def get_last_active_module(self) -> str:
        return self._data.get("last_active_module", "profile")

    def set_last_active_module(self, module_name: str) -> None:
        self._data["last_active_module"] = module_name
        self._save()

    def get_search_history(self) -> list[str]:
        return self._data.get("search_history", [])

    def add_search_history(self, keyword: str) -> None:
        history = self._data.get("search_history", [])
        if keyword in history:
            history.remove(keyword)
        history.insert(0, keyword)
        self._data["search_history"] = history[:10]
        self._save()

    def is_password_migration_pending(self) -> bool:
        return self._data.get("migration", {}).get("password_pending", False)

    def clear_password_migration_flag(self) -> None:
        if "migration" in self._data:
            self._data["migration"]["password_pending"] = False
            self._save()

    def get_window_geometry(self) -> str:
        return self._data.get("window_geometry", "")

    def set_window_geometry(self, geometry: str) -> None:
        self._data["window_geometry"] = geometry
        self._save()

    def get_font_family(self) -> str:
        return self._data.get("font_family", "Microsoft YaHei")

    def set_font_family(self, family: str) -> None:
        self._data["font_family"] = family
        self._save()
