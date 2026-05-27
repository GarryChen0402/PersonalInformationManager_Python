# Personal Information Manager (PIM) — v1.3

基于 Python PySide6 (Qt) 的个人信息管理器，除 PySide6 外零外部依赖。

## 功能模块

- **个人档案** — 管理姓名、联系方式、社交账号、个人简介等
- **状态管理** — 每日记录心情、精力、专注度、体重、睡眠，折线图趋势 + 年度热力图
- **技能管理** — 管理技能名称、类别、熟练度(1-5)、学习时长，雷达图类别分布
- **知识管理** — 笔记管理 + PDF 电子书管理，柱状图类别统计，支持 Markdown 导出
- **待办事项** — 优先级/类别/截止日期管理，逾期高亮，批量操作，支持 iCalendar 导出
- **习惯追踪** — 每日/每周/自定义频率打卡，连续天数统计，年度热力图
- **日记** — 月历导航 + 富文本编辑，自动保存，情绪关联，Markdown 导出
- **密码管理** — HMAC 认证加密存储（v2），主密码保护，自动锁定，暴力破解防护
- **数据管理** — 全量备份/恢复，选择性模块恢复，CSV 导入导出
- **数据概览** — 仪表盘卡片网格，迷你趋势图，点击卡片可跳转
- **全局搜索** — 跨 8 个模块搜索（Ctrl+Shift+F），防抖 300ms，结果按模块分组
- **主题系统** — 5 套主题切换（Ctrl+T），导航栏折叠，字体缩放（Ctrl+= / Ctrl+-）

## 运行

```bash
# 安装依赖（仅首次）
pip install PySide6

# 开发模式直接运行
python main.py

# 运行所有测试（282 个）
python -m unittest discover Tests -v

# 运行单个模块测试
python -m unittest Tests.test_storage -v
python -m unittest Tests.test_habit_manager -v
```

## 打包为可执行文件

```bash
# 安装 PyInstaller（仅首次）
pip install pyinstaller

# 构建（输出到 dist/PIM/）
pyinstaller --onedir --windowed --name "PIM" --clean main.py
```

构建产物在 `dist/PIM/` 目录，将该文件夹整体复制即可分发运行。

## 项目结构

```
PersonalInformationManager_Python/
├── main.py                 # 入口
├── Core/                   # 基础设施层
│   ├── Config.py           # 路径配置（兼容 PyInstaller）
│   ├── Storage.py          # JSON 文件存储基类（原子写入）
│   ├── Crypto.py           # PBKDF2 + HMAC-SHA256 认证加密（v1/v2 兼容）
│   ├── DataMigration.py    # v1.0 → v1.1 → v1.2 数据迁移
│   └── Exceptions.py       # 自定义异常层次
├── Models/                 # 数据模型层 (@dataclass)
│   ├── Profile.py          # 个人档案
│   ├── Skill.py            # 技能
│   ├── Status.py           # 每日状态
│   ├── Knowledge.py        # 知识条目（笔记/电子书）
│   ├── Password.py         # 密码条目
│   ├── TodoItem.py         # 待办事项
│   ├── Habit.py            # 习惯定义（频率/目标次数/分类/颜色）
│   ├── HabitRecord.py      # 习惯打卡记录
│   ├── JournalEntry.py     # 日记条目（按日期唯一）
│   └── AppConfig.py        # 应用配置（主题/字体/主密码令牌）
├── Services/               # 业务逻辑层
│   ├── ProfileManager.py   # 档案管理（单例模式）
│   ├── SkillManager.py     # 技能 CRUD + 统计 + CSV 导入导出
│   ├── StatusManager.py    # 状态记录 + 日期范围筛选 + CSV 导出
│   ├── KnowledgeManager.py # 笔记 + PDF 电子书管理 + Markdown 导出
│   ├── PasswordManager.py  # HMAC 认证加密存储 + v1→v2 渐进迁移
│   ├── TodoManager.py      # 待办 CRUD + 逾期检测 + iCalendar/CSV 导出
│   ├── HabitManager.py     # 习惯 CRUD + 打卡 + 连续统计 + 热力图
│   ├── JournalManager.py   # 日记 CRUD + 按日期唯一 + 搜索 + Markdown 导出
│   ├── CryptoService.py    # 主密码生命周期（解锁/自动锁定/暴力破解防护）
│   ├── ConfigManager.py    # 应用配置读写（单例模式）
│   └── BackupManager.py    # 全量备份 + 选择性恢复
├── Views/                  # GUI 视图层 (PySide6)
│   ├── App.py              # QMainWindow + 状态栏时钟 + 窗口持久化 + 5 套主题 + 快捷键
│   ├── NavFrame.py         # 左侧导航栏 QListWidget + 折叠/展开
│   ├── BasePage.py         # 页面公共基类 QTableWidget（右键菜单/选中/高亮/列排序）
│   ├── DashboardPage.py    # 仪表盘（QGridLayout 卡片网格 + MiniChart QPainter）
│   ├── ProfilePage.py      # 个人档案 QFormLayout 表单
│   ├── SkillPage.py        # 技能管理表格 + RadarChart/BarChart QPainter 图表
│   ├── StatusPage.py       # 状态管理表格 + LineChart + CalendarHeatmap
│   ├── KnowledgePage.py    # 知识管理 QTabWidget（笔记/电子书）+ BarChart
│   ├── TodoPage.py         # 待办事项表格（优先级/逾期颜色标记）
│   ├── HabitPage.py        # 习惯追踪 QSplitter（左栏列表 + 右栏详情 + 热力图）
│   ├── JournalPage.py      # 日记 QSplitter（左侧 CalendarNav + 右侧编辑器 + 情绪关联）
│   ├── PasswordPage.py     # 密码管理表格 + 主密码设置/解锁对话框
│   ├── BackupPage.py       # 备份管理 + 选择性恢复 QDialog
│   ├── GlobalSearchBar.py  # 全局搜索栏 QTreeWidget 下拉结果面板
│   ├── ChartWidgets.py     # QPainter 图表（LineChart/BarChart/RadarChart/MiniChart/CalendarHeatmap）
│   ├── Themes.py           # 5 套 Qt Stylesheet 主题定义
│   └── Widgets.py          # 通用控件（SearchBar/FormDialog/DateRangePicker/KeywordEntry/CalendarNav 等）
├── Tests/                  # 测试（282 tests）
│   ├── test_base.py        # 共享测试基类（自动临时目录 + 路径重定向）
│   ├── test_storage.py
│   ├── test_profile_manager.py
│   ├── test_skill_manager.py
│   ├── test_status_manager.py
│   ├── test_knowledge_manager.py
│   ├── test_password_manager.py
│   ├── test_todo_manager.py
│   ├── test_habit_manager.py
│   ├── test_crypto_service.py
│   ├── test_crypto_standalone.py
│   ├── test_config_manager.py
│   ├── test_data_migration.py
│   ├── test_models.py
│   ├── test_global_search.py
│   ├── test_backup_manager.py
│   └── test_integration.py
├── Docs/                   # 需求与设计文档
│   ├── v1.1/               # v1.1 升级文档
│   ├── v1.2/               # v1.2 升级文档
│   │   ├── 01-需求分析文档.md
│   │   ├── 02-系统设计文档.md
│   │   └── 03-开发步骤与规划文档.md
│   └── v1.3/               # v1.3 Tkinter → PySide6 迁移文档
│       ├── 01-需求分析文档.md
│       ├── 02-系统设计文档.md
│       └── 03-开发步骤与规划文档.md
├── Data/                   # 运行时数据（自动创建）
└── dist/                   # 打包输出（构建后生成）
```

## 技术要点

- **PySide6 (Qt for Python)** — LGPL 授权，跨平台原生 GUI 框架，替代原 Tkinter 实现
- **Qt Stylesheet 主题** — 5 套主题（浅色/深色/Solarized Light/Solarized Dark/Nord），类 CSS 语法
- **QPainter 自绘图表** — 折线图/柱状图/雷达图/MiniChart/日历热力图（GitHub 贡献图风格），tooltip 交互
- **Qt Signals & Slots** — 响应式事件处理，替代 Tkinter 回调模式
- **JSON 持久化** — 原子写入（tmp 文件 + `os.replace`），自动 UUID 和时间戳
- **4 层架构** — View → Service → Model → Storage（仅 View 层重写，后端零改动）
- **路径动态解析** — 兼容 `python main.py` 和 PyInstaller 打包两种运行方式
- **认证加密** — PBKDF2（100,000 次迭代）+ Encrypt-then-MAC（HMAC-SHA256），版本化密文（v1/v2 向后兼容）
- **安全特性** — 自动锁定（可配置超时）、暴力破解防护（5 次失败锁定 30 秒）、密码强度检测
- **PDF 电子书** — 文件头校验（`%PDF`），自动复制到 `Data/books/` 管理
- **连续天数统计** — 支持 daily/weekly/custom 三种频率，隔天断签检测
- **全局搜索** — QTimer 300ms 防抖，跨 8 个模块搜索，QTreeWidget 分组显示结果
- **快捷键** — Ctrl+Shift+F 全局搜索、Ctrl+N 新建、Ctrl+T 切换主题、Ctrl+=/- 字体缩放、Ctrl+1~9 导航切换
- **v1.3 迁移** — Tkinter View 层 6,100 行全部重写为 PySide6，Model/Service/Storage 层零改动，282 测试全部通过
