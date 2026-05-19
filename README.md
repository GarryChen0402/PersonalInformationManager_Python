# Personal Information Manager (PIM)

基于 Python Tkinter 的个人信息管理器，零外部依赖，仅使用 Python 标准库（打包工具除外）。

## 功能模块

- **个人档案** — 管理姓名、联系方式、社交账号、个人简介等
- **状态管理** — 每日记录心情、精力、专注度、体重、睡眠，支持按周/月统计
- **技能管理** — 管理技能名称、类别、熟练度(1-5)、学习时长，支持分类统计
- **知识管理** — 笔记管理 + PDF 电子书管理，支持类别和关键词标签
- **密码管理** — base64 编码存储密码，支持搜索和复制
- **数据管理** — 全量备份/恢复，支持选择性模块恢复
- **数据概览** — 仪表盘卡片网格，展示各模块统计概览，点击卡片可跳转

## 运行

```bash
# 开发模式直接运行
python main.py

# 运行所有测试（100 个）
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
│   ├── Config.py           # 路径配置（兼容 PyInstaller）
│   ├── Storage.py          # JSON 文件存储基类（原子写入）
│   └── Exceptions.py       # 自定义异常层次
├── Models/                 # 数据模型层 (@dataclass)
│   ├── Profile.py          # 个人档案
│   ├── Skill.py            # 技能
│   ├── Status.py           # 每日状态
│   ├── Knowledge.py        # 知识条目（笔记/电子书）
│   └── Password.py         # 密码条目
├── Services/               # 业务逻辑层
│   ├── ProfileManager.py   # 档案管理（单例模式）
│   ├── SkillManager.py     # 技能 CRUD + 统计
│   ├── StatusManager.py    # 状态记录 + 日期范围筛选
│   ├── KnowledgeManager.py # 笔记 + PDF 电子书管理
│   ├── PasswordManager.py  # base64 编解码
│   └── BackupManager.py    # 全量备份 + 选择性恢复
├── Views/                  # GUI 视图层 (Tkinter)
│   ├── App.py              # 主窗口 + 状态栏
│   ├── NavFrame.py         # 左侧导航栏（150px）
│   ├── DashboardPage.py    # 仪表盘（3×2 卡片网格）
│   ├── ProfilePage.py      # 个人档案表单
│   ├── SkillPage.py        # 技能管理表格
│   ├── StatusPage.py       # 状态管理表格（颜色标签）
│   ├── KnowledgePage.py    # 知识管理（ttk.Notebook 双 Tab）
│   ├── PasswordPage.py     # 密码管理表格
│   ├── BackupPage.py       # 备份管理 + 选择性恢复对话框
│   └── Widgets.py          # 通用控件库
├── Tests/                  # 测试（100 tests）
│   ├── test_storage.py     # JSONFileStorage CRUD
│   ├── test_profile_manager.py
│   ├── test_skill_manager.py
│   ├── test_status_manager.py
│   ├── test_knowledge_manager.py
│   ├── test_password_manager.py
│   ├── test_backup_manager.py
│   └── test_integration.py # 全功能集成测试
├── Docs/                   # 需求与设计文档
│   ├── 01-需求分析文档.md
│   ├── 02-系统设计文档.md
│   └── 03-开发步骤与规划文档.md
├── Data/                   # 运行时数据（自动创建）
└── dist/                   # 打包输出（构建后生成）
```

## 技术要点

- **零依赖** — 仅使用 Python 标准库，无需 pip install
- **JSON 持久化** — 原子写入（tmp 文件 + `os.replace`），自动 UUID 和时间戳
- **4 层架构** — View → Service → Model → Storage
- **路径动态解析** — 兼容 `python main.py` 和 PyInstaller 打包两种运行方式
- **PDF 电子书** — 文件头校验（`%PDF`），自动复制到 `Data/books/` 管理
- **密码编码** — base64 存储（非加密，仅防明文浏览）
