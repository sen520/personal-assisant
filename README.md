# 🤖 Personal Assistant

基于 LangGraph 的智能个人助理系统，支持多用户、长期记忆、任务管理和智能对话。

## ✨ 功能特性

- 🤖 **智能对话** - 基于 DeepSeek-V3 的自然语言对话
- 🧠 **长期记忆** - 自动存储和检索用户偏好、重要信息
- 📋 **任务管理** - 创建、完成、删除任务
- 👥 **多用户支持** - 数据隔离，每个用户独立存储
- 🌐 **Web 界面** - 现代化的单页应用界面
- 🔌 **RESTful API** - 完整的 API 接口

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置你的 API Key
```

### 3. 启动服务

```bash
python main.py
```

### 4. 访问

- **前端界面**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

## 📁 项目结构

```
personal-assistant/
├── src/
│   ├── api/              # FastAPI 接口层
│   │   ├── main.py       # API 主入口
│   │   └── __init__.py
│   ├── db/               # 数据库层
│   │   ├── models.py     # SQLAlchemy ORM 模型
│   │   ├── repository.py # 数据访问层
│   │   └── memory_system.py  # 记忆系统
│   ├── graph/            # LangGraph 工作流
│   │   ├── workflow_db.py    # 数据库版工作流
│   │   └── __init__.py
│   ├── nodes/            # 工作流节点
│   │   ├── nodes_db.py   # 数据库版节点
│   │   └── __init__.py
│   ├── tools/            # 工具集合
│   │   ├── tools.py      # 工具实现
│   │   └── __init__.py
│   ├── llm/              # LLM 客户端
│   │   └── __init__.py
│   ├── memory/           # 内存版记忆（旧）
│   ├── models/           # 数据模型定义
│   ├── config/           # 配置管理
│   └── state/            # 状态管理
├── static/               # 前端静态文件
│   ├── index.html        # 前端页面
│   ├── style.css         # 样式表
│   └── app.js            # 前端逻辑
├── tests/                # 测试用例
├── docker/               # Docker 配置
├── docker-compose.yml    # Docker Compose 配置
├── requirements.txt      # Python 依赖
├── main.py               # 主入口
└── README.md             # 本文件
```

## 🔧 配置说明

编辑 `.env` 文件配置以下选项：

```bash
# LLM API 配置（硅基流动）
LLM_PROVIDER=openai
LLM_MODEL=deepseek-ai/DeepSeek-V3
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.siliconflow.cn/v1

# 数据库配置
DB_USER=root
DB_PASSWORD=password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=personal_assistant

# SQLite 模式（开发/测试用）
USE_SQLITE=true
SQLITE_PATH=./data/app.db
```

## 🌐 API 接口

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录

### 会话
- `POST /api/sessions` - 创建会话
- `GET /api/sessions` - 会话列表

### 聊天
- `POST /api/chat` - 发送消息
- `GET /api/sessions/{id}/messages` - 获取消息

### 记忆
- `POST /api/memories` - 创建记忆
- `GET /api/memories` - 记忆列表
- `DELETE /api/memories/{id}` - 删除记忆

### 任务
- `POST /api/tasks` - 创建任务
- `GET /api/tasks` - 任务列表
- `PATCH /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务

## 🧪 测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python tests/test_db.py
python tests/test_api.py
python tests/test_workflow.py
```

## 🐳 Docker 部署

```bash
# 启动所有服务（MySQL + Redis + ChromaDB + App）
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

## 📝 开发规范

### 代码检查
项目使用 **Pylint** 进行代码质量检查。

```bash
# 提交前自动检查（推荐）
git commit -m "feat: xxx"

# 手动检查
pylint src/ --rcfile=.pylintrc
```

### Git 提交规范
```
【code by kimiclaw】<type>: <message>

type:
  - feat: 新功能
  - fix: 修复
  - docs: 文档
  - style: 格式
  - refactor: 重构
  - test: 测试
  - chore: 其他
```

## 🗺️ 路线图

- [x] 基础对话
- [x] 长期记忆
- [x] 任务管理
- [x] 多用户支持
- [x] Web 界面
- [x] RESTful API
- [x] JWT 认证
- [x] 请求限流
- [x] Redis 缓存
- [x] 结构化日志
- [ ] 向量语义检索
- [ ] 文件上传/知识库
- [ ] 定时提醒
- [ ] 多 LLM 支持

## 📄 License

MIT License

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [FastAPI](https://fastapi.tiangolo.com/)
- [DeepSeek](https://deepseek.com/)
