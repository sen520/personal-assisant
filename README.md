# Personal Assistant

基于 LangGraph 的个人智能助理系统。

## 功能特性

- 🤖 智能对话与任务处理
- 🧠 长期记忆管理
- 📅 日程与提醒
- 🔍 信息检索与整合
- 📝 知识库管理

## 项目结构

```
personal-assistant/
├── src/
│   ├── graph/          # LangGraph 工作流定义
│   ├── nodes/          # 功能节点
│   ├── state/          # 状态管理
│   ├── tools/          # 工具集合
│   ├── utils/          # 工具函数
│   └── config/         # 配置管理
├── tests/              # 测试用例
├── memory/             # 记忆存储
├── prompts/            # 提示词模板
└── logs/               # 日志文件
```

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
```

## 配置

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

## 代码检查

项目使用 **Pylint** 进行代码质量检查。

### 提交前自动检查

每次 `git commit` 会自动运行 pylint 检查：
- 评分低于 **8.0** 会阻止提交
- 仅检查变更的 Python 文件

```bash
# 正常提交（自动检查）
git commit -m "feat: xxx"

# 强制提交（跳过检查，不推荐）
git commit -m "feat: xxx" --no-verify
```

### 手动检查

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 检查所有文件
pylint src/ --rcfile=.pylintrc

# 检查指定文件
pylint src/memory/system.py

# 使用脚本检查
python scripts/lint.py --all
```

### 检查规则

- 最大行长度: **120** 字符
- 评分阈值: **8.0/10**
- 忽略目录: `migrations/`, `alembic/`, `tests/`, `venv/`

配置文件: `.pylintrc`