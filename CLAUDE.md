# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 项目概述

个人信息管理器 (PIM) — 一个用于管理个人信息的 Python Tkinter GUI 应用程序。这是一个 Python 学习项目。除 Python 标准库外零外部依赖。

## 架构

4 层架构：**View → Service → Model → Storage**

- **`main.py`** — 入口点。调用 `ensure_directories()` 然后启动 Tkinter `App`。
- **`Core/`** — 基础设施：`Config.py`（路径常量、`ensure_directories()`）、`Storage.py`（带原子写入的 JSONFileStorage 基类）、`Exceptions.py`（PIMException 层次结构）。
- **`Models/`** — Python `@dataclass` 类，带有 `from_dict()`/`to_dict()` 方法。通过 `__init__.py` 重新导出。
- **`Services/`** — 业务逻辑管理器。每个通过 `Config.SKILL_PATH`（模块引用，不在导入时捕获）引用路径。通过 `__init__.py` 重新导出。
- **`Views/`** — Tkinter GUI 页面。`App.py`（主窗口 + 状态栏）、`NavFrame.py`（左侧导航 150px）、各模块页面、`Widgets.py`（共享控件）。
- **`Data/`** — 自动创建的数据目录：`books/`、`backups/`，以及各模块的 JSON 文件。
- **`Tests/`** — 单元测试和集成测试（100 个测试，零依赖）。

## 关键模式

- **零依赖** — 仅使用标准库。无需 pip install。
- **JSON 持久化** — `JSONFileStorage` 基类提供 CRUD、搜索、查询功能。通过临时文件 + `os.replace()` 实现原子写入。自动生成 UUID id 和时间戳。
- **路径引用** — 所有服务管理器以模块方式导入 `Core.Config`，并动态引用 `Config.SKILL_PATH` 等（而非在导入时通过 `from Core.Config import SKILL_PATH` 捕获）。这使得测试可以通过修改 `Config` 属性来重定向数据路径。
- **Profile 是单例** — 存储为 JSON 对象（非列表）。ProfileManager 有自己的 `_load`/`_save` 方法。
- **密码编码** — base64 编码/解码（非加密，仅作混淆）。
- **PDF 处理** — 头部验证（`b"%PDF"` 检查），以 UUID 文件名复制到 `Data/books/`，通过 `os.startfile`/`subprocess` 打开。
- **同日状态** — 为已有日期添加状态记录会自动更新现有记录。
- **GUI 模式** — 页面接收 `set_status` 可调用对象（非原始 Label）。通过 `pack_forget()`/`pack()` 切换页面。DashboardPage 还接收 `navigate` 回调。
- **Views/Widgets.py** — 共享控件：SearchBar、FormDialog（Toplevel 模态框）、ConfirmDialog、DateRangePicker、StatsBar、KeywordEntry（标签芯片）。
- **知识模型** — 单一的 `KnowledgeItem`，带有 `item_type` 字段（"note"/"ebook"）。统一的分类/关键词系统。
- **备份** — 完整 JSON 备份，支持按模块选择性恢复。BackupManager 使用 `_module_paths()` 函数（非模块级字典）动态解析路径。
- **测试** — 使用临时目录。在 `setUpClass`/`tearDownClass` 中重定向 `Config.*` 路径。在 `setUp` 中调用 `os.remove()` 以确保干净状态。
- **无 setup.py、requirements.txt 或虚拟环境** — 直接通过 `python main.py` 运行。
