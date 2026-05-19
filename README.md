# Personal Information Manager (PIM)

基于 Python Tkinter 的个人信息管理器，零外部依赖，仅使用 Python 标准库。

## 功能模块

- **个人档案** — 管理姓名、联系方式、社交账号、个人简介等
- **状态管理** — 每日记录心情、精力、专注度、体重、睡眠，支持按周/月统计
- **技能管理** — 管理技能名称、类别、熟练度(1-5)、学习时长，支持分类统计
- **知识管理** — 笔记管理 + PDF 电子书管理，支持类别和关键词标签
- **密码管理** — base64 编码存储密码，支持搜索和复制
- **数据管理** — 全量备份/恢复，支持选择性模块恢复
- **数据概览** — 仪表盘卡片网格，展示各模块统计概览

## 运行

```
python main.py
```

## 项目结构

```
PersonalInformationManager_Python/
├── main.py              # 入口
├── Core/                # 基础设施层
│   ├── Config.py        # 路径配置
│   ├── Storage.py       # JSON 文件存储基类
│   └── Exceptions.py    # 自定义异常
├── Models/              # 数据模型层 (dataclass)
│   ├── Profile.py
│   ├── Skill.py
│   ├── Status.py
│   ├── Knowledge.py
│   └── Password.py
├── Services/            # 业务逻辑层
│   ├── ProfileManager.py
│   ├── SkillManager.py
│   ├── StatusManager.py
│   ├── KnowledgeManager.py
│   ├── PasswordManager.py
│   └── BackupManager.py
├── Views/               # GUI 视图层 (Tkinter)
│   ├── App.py           # 主窗口
│   ├── NavFrame.py      # 左侧导航
│   ├── DashboardPage.py # 仪表盘
│   ├── ProfilePage.py
│   ├── SkillPage.py
│   ├── StatusPage.py
│   ├── KnowledgePage.py
│   ├── PasswordPage.py
│   ├── BackupPage.py
│   └── Widgets.py       # 通用控件
├── Data/                # 数据存储目录 (自动创建)
├── Tests/               # 单元测试与集成测试
└── Docs/                # 需求与设计文档
```

## 测试

```bash
# 运行所有测试
python -m unittest discover Tests -v

# 运行单个模块测试
python -m unittest Tests.test_storage -v
python -m unittest Tests.test_skill_manager -v
```
