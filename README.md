# Personal Information Manager (PIM) — v1.1

基于 Python Tkinter 的个人信息管理器，零外部依赖，仅使用 Python 标准库（打包工具除外）。

## 功能模块

- **个人档案** — 管理姓名、联系方式、社交账号、个人简介等
- **状态管理** — 每日记录心情、精力、专注度、体重、睡眠，折线图趋势可视化
- **技能管理** — 管理技能名称、类别、熟练度(1-5)、学习时长，雷达图类别分布
- **知识管理** — 笔记管理 + PDF 电子书管理，柱状图类别统计
- **待办事项** — 优先级/类别/截止日期管理，逾期高亮，批量操作
- **密码管理** — AES 流密码加密存储，主密码保护，支持搜索和复制
- **数据管理** — 全量备份/恢复，选择性模块恢复，CSV 导入导出
- **数据概览** — 仪表盘卡片网格，迷你趋势图，点击卡片可跳转
- **全局搜索** — 跨模块搜索（Ctrl+Shift+F），防抖 300ms，结果按模块分组
- **主题系统** — 浅色/深色主题切换（Ctrl+T），字体缩放（Ctrl+= / Ctrl+-）

## 运行

```bash
# 开发模式直接运行
python main.py

# 运行所有测试（159 个）
python -m unittest discover Tests -v

# 运行单个模块测试
python -m unittest Tests.test_storage -v
python -m unittest Tests.test_skill_manager -v
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
│   ├── Config.py           # 路径配置 + 主题配色（兼容 PyInstaller）
│   ├── Storage.py          # JSON 文件存储基类（原子写入）
│   ├── Crypto.py           # SHA-256 + XOR 流密码加解密
│   ├── DataMigration.py    # v1.0 → v1.1 数据迁移
│   └── Exceptions.py       # 自定义异常层次
├── Models/                 # 数据模型层 (@dataclass)
│   ├── Profile.py          # 个人档案
│   ├── Skill.py            # 技能
│   ├── Status.py           # 每日状态
│   ├── Knowledge.py        # 知识条目（笔记/电子书）
│   ├── Password.py         # 密码条目
│   ├── TodoItem.py         # 待办事项
│   └── AppConfig.py        # 应用配置（主题/字体/主密码令牌）
├── Services/               # 业务逻辑层
│   ├── ProfileManager.py   # 档案管理（单例模式）
│   ├── SkillManager.py     # 技能 CRUD + 统计 + CSV 导入导出
│   ├── StatusManager.py    # 状态记录 + 日期范围筛选 + CSV 导出
│   ├── KnowledgeManager.py # 笔记 + PDF 电子书管理 + CSV 导出
│   ├── PasswordManager.py  # AES 流密码加密存储
│   ├── TodoManager.py      # 待办 CRUD + 逾期检测 + 批量操作 + CSV 导入导出
│   ├── CryptoService.py    # 主密码生命周期管理（解锁/锁定/修改）
│   ├── ConfigManager.py    # 应用配置读写（单例模式）
│   └── BackupManager.py    # 全量备份 + 选择性恢复
├── Views/                  # GUI 视图层 (Tkinter)
│   ├── App.py              # 主窗口 + 状态栏 + 主题/快捷键/字体缩放
│   ├── NavFrame.py         # 左侧导航栏 + 全局搜索嵌入
│   ├── BasePage.py         # 页面公共基类（右键菜单/选中/高亮）
│   ├── DashboardPage.py    # 仪表盘（卡片网格 + MiniChart）
│   ├── ProfilePage.py      # 个人档案表单
│   ├── SkillPage.py        # 技能管理表格 + 雷达图
│   ├── StatusPage.py       # 状态管理表格 + 折线图趋势
│   ├── KnowledgePage.py    # 知识管理（Notebook 双 Tab）+ 柱状图
│   ├── TodoPage.py         # 待办事项表格（优先级/逾期颜色标记）
│   ├── PasswordPage.py     # 密码管理表格（需主密码解锁）
│   ├── BackupPage.py       # 备份管理 + 选择性恢复对话框
│   ├── GlobalSearchBar.py  # 全局搜索栏 + 下拉结果面板
│   ├── ChartWidgets.py     # Canvas 图表组件（折线/柱状/雷达/迷你图）
│   └── Widgets.py          # 通用控件库（SearchBar/FormDialog/CSVPreviewDialog 等）
├── Tests/                  # 测试（159 tests）
│   ├── test_storage.py
│   ├── test_profile_manager.py
│   ├── test_skill_manager.py
│   ├── test_status_manager.py
│   ├── test_knowledge_manager.py
│   ├── test_password_manager.py
│   ├── test_todo_manager.py
│   ├── test_crypto_service.py
│   ├── test_global_search.py
│   ├── test_backup_manager.py
│   └── test_integration.py
├── Docs/                   # 需求与设计文档
│   ├── 01-需求分析文档.md
│   ├── 02-系统设计文档.md
│   ├── 03-开发步骤与规划文档.md
│   └── v1.1/               # v1.1 升级文档
│       ├── 01-需求分析文档.md
│       ├── 02-系统设计文档.md
│       └── 03-开发步骤与规划文档.md
├── Data/                   # 运行时数据（自动创建）
└── dist/                   # 打包输出（构建后生成）
```

## 技术要点

- **零依赖** — 仅使用 Python 标准库，无需 pip install
- **JSON 持久化** — 原子写入（tmp 文件 + `os.replace`），自动 UUID 和时间戳
- **4 层架构** — View → Service → Model → Storage
- **路径动态解析** — 兼容 `python main.py` 和 PyInstaller 打包两种运行方式
- **PDF 电子书** — 文件头校验（`%PDF`），自动复制到 `Data/books/` 管理
- **流密码加密** — SHA-256 + XOR 流密码，PBKDF2 密钥派生（100,000 次迭代），主密码内存缓存
- **主题系统** — 浅色/深色双主题，`apply_theme()` 递归遍历所有子控件
- **Canvas 图表** — 折线图/柱状图/雷达图/MiniChart，相对坐标绘制，跨平台一致
- **全局搜索** — 300ms 防抖，跨 6 个模块并行搜索，结果按模块分组（最多 20 条）
- **快捷键** — Ctrl+Shift+F 全局搜索、Ctrl+N 新建、Ctrl+T 切换主题、Ctrl+=/- 字体缩放、Ctrl+1~8 导航切换
