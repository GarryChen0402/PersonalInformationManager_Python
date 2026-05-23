"""数据迁移：v1.0 → v1.1 → v1.2。"""

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
    """确保 config.json 存在并包含最新默认配置，返回当前配置。"""
    config = _load_json(Config.CONFIG_PATH) or {}
    defaults = {
        "theme": "light",
        "font_size": 10,
        "font_family": "TkDefaultFont",
        "master_password_token": "",
        "last_active_module": "profile",
        "search_history": [],
        "auto_lock_timeout": 300,
        "window_geometry": "",
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
            if decoded.isprintable():
                return True
        except Exception:
            pass
    return False


def _detect_v1_passwords() -> bool:
    """检测 passwords.json 中是否存在 v1 加密格式（无版本头，无 HMAC）的密码。"""
    data = _load_json(Config.PASSWORD_PATH)
    if not data or not isinstance(data, list) or len(data) == 0:
        return False

    for entry in data:
        pwd = entry.get("password", "")
        if not pwd:
            continue
        if pwd.startswith("v2:"):
            continue
        # base64 格式已在 _detect_base64_passwords 中单独处理
        import base64
        try:
            decoded = base64.b64decode(pwd.encode()).decode("utf-8")
            if decoded.isprintable():
                continue  # 这是 base64 格式
        except Exception:
            pass
        # 不是 v2 也不是 base64，那就是 v1 格式
        try:
            base64.b64decode(pwd)
            return True
        except Exception:
            pass
    return False


def run_migrations() -> dict:
    """运行所有必要的迁移，返回迁移状态报告。"""
    report: dict[str, str | bool] = {}

    config = _ensure_config()
    current_version = config.get("migration", {}).get("version", "1.0")

    if current_version >= "1.2":
        report["config_version"] = current_version
        report["migration_needed"] = False
        return report

    # ---- v1.0 → v1.1 迁移 ----
    if current_version < "1.1":
        has_base64 = _detect_base64_passwords()
        config["migration"]["version"] = "1.1"
        config["migration"]["password_pending"] = has_base64
        _save_json(Config.CONFIG_PATH, config)
        report["base64_detected"] = has_base64

    # ---- v1.1 → v1.2 迁移 ----
    has_v1 = _detect_v1_passwords()
    has_base64_v2 = _detect_base64_passwords()

    config["migration"]["version"] = "1.2"
    config["migration"]["password_v2_pending"] = has_v1 or has_base64_v2

    # 确保 v1.2 新增配置项存在
    for key, value in {
        "auto_lock_timeout": 300,
        "font_family": "TkDefaultFont",
        "window_geometry": "",
    }.items():
        if key not in config:
            config[key] = value

    _save_json(Config.CONFIG_PATH, config)

    report["config_version"] = "1.2"
    report["password_v2_pending"] = has_v1 or has_base64_v2
    report["v1_passwords_detected"] = has_v1
    report["base64_passwords_detected"] = has_base64_v2
    report["migration_needed"] = has_v1 or has_base64_v2
    return report
