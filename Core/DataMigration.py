"""v1.0 → v1.1 数据迁移。"""

import json
import os

import Core.Config as Config


def _load_json(path: str) -> dict | None:
    """加载 JSON 文件，失败返回 None。"""
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _save_json(path: str, data: dict) -> None:
    """保存 JSON 文件（原子写入）。"""
    tmp = path + ".tmp"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _ensure_config() -> dict:
    """确保 config.json 存在并包含默认配置，返回当前配置。"""
    config = _load_json(Config.CONFIG_PATH) or {}
    defaults = {
        "theme": "light",
        "font_size": 10,
        "master_password_token": "",
        "last_active_module": "profile",
        "search_history": [],
        "migration": {"version": "1.0"},
    }
    changed = False
    for key, value in defaults.items():
        if key not in config:
            config[key] = value
            changed = True
    if changed:
        _save_json(Config.CONFIG_PATH, config)
    return config


def _detect_base64_passwords() -> bool:
    """检测 passwords.json 中是否存在旧 base64 格式的密码。"""
    import base64

    data = _load_json(Config.PASSWORD_PATH)
    if not data or not isinstance(data, list) or len(data) == 0:
        return False

    for entry in data:
        pwd = entry.get("password", "")
        if not pwd:
            continue
        try:
            decoded = base64.b64decode(pwd.encode()).decode("utf-8")
            # 如果能成功解码为可打印文本，说明是旧 base64 格式
            if decoded.isprintable():
                return True
        except Exception:
            pass
    return False


def run_migrations() -> dict:
    """运行所有必要的迁移，返回迁移状态报告。"""
    report: dict[str, str | bool] = {}

    # 1. 确保配置文件存在
    config = _ensure_config()
    current_version = config.get("migration", {}).get("version", "1.0")

    if current_version >= "1.1":
        report["config_version"] = current_version
        report["migration_needed"] = False
        return report

    # 2. 检测是否需要密码迁移
    has_base64 = _detect_base64_passwords()

    # 3. 更新版本标记
    config["migration"]["version"] = "1.1"
    config["migration"]["password_pending"] = has_base64
    _save_json(Config.CONFIG_PATH, config)

    report["config_version"] = "1.1"
    report["password_pending"] = has_base64
    report["migration_needed"] = has_base64
    return report
