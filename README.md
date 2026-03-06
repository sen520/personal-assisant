# 🤖 Personal Assistant

基于 LangGraph 的智能个人助理系统，支持多用户、长期记忆、任务管理、智能对话、定时提醒、知识库、多LLM支持等完整功能。

**状态**: ✅ 项目已完成 (100%)  
**版本**: v3.0  
**日期**: 2026-03-06

---

## ✨ 功能特性

### 核心功能 (P0)
- 🤖 **智能对话** - 基于 DeepSeek-V3 的自然语言对话
- 🧠 **长期记忆** - 自动存储和检索用户偏好、重要信息（MySQL/SQLite）
- 📋 **任务管理** - 创建、完成、删除任务
- 👥 **多用户支持** - JWT 认证，数据完全隔离
- 🌐 **Web 界面** - 现代化的 SPA 单页应用

### 高级功能 (P1)
- 🔌 **RESTful API** - 30+ 个完整接口
- 🚦 **请求限流** - 防刷保护（SlowAPI）
- ⚡ **Redis 缓存** - 响应缓存，自动降级
- 📝 **结构化日志** - 请求追踪 + JSON 输出

### 扩展功能 (P2)
- 🔍 **向量语义检索** - ChromaDB 语义搜索
- 📅 **定时提醒** - APScheduler 定时任务
- 📁 **文件上传/知识库** - RAG 文档检索（PDF/Word/TXT/Markdown/JSON/CSV）
- 🔄 **多 LLM 支持** - 17+ 模型切换（GPT-4、Claude、Kimi、DeepSeek、通义千问等）

### 管理功能 (P3)
- 📊 **数据导出** - PDF/Markdown/JSON 格式
- 🎛️ **管理后台** - 用户管理 + 系统监控

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/sen520/personal-assistant.git
cd personal-assistant
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置你的 API Key
```

### 4. 启动服务

```bash
python main.py
```

### 5. 访问

- **前端界面**: http://localhost:8000
- **API 文档**: http://localhost:8000/docs

---

## 📁 项目结构

```
personal-assistant/
├── src/
│   ├── api/              # FastAPI 接口层
│   │   ├── main.py       # API 主入口（30+ 接口）
│   │   └── __init__.py
│   ├── db/               # 数据库层
│   │   ├── models.py     # SQLAlchemy ORM 模型（8个表）
│   │   ├── repository.py # 数据访问层
│   │   ├── memory_system.py  # 记忆系统
│   │   └── connection.py # 连接池
│   ├── graph/            # LangGraph 工作流
│   │   ├── workflow_db.py    # 数据库版工作流
│   │   └── __init__.py
│   ├── nodes/            # 工作流节点
│   │   ├── nodes_db.py   # 数据库版节点
│   │   └── __init__.py
│   ├── tools/            # 工具集合
│   │   ├── tools.py      # 7个工具实现
│   │   └── __init__.py
│   ├── llm/              # LLM 客户端
│   │   └── __init__.py   # 多模型支持
│   ├── utils/            # 工具函数
│   │   ├── cache.py      # Redis 缓存
│   │   ├── vector_store.py   # 向量存储
│   │   ├── scheduler.py  # 定时任务
│   │   ├── document_parser.py  # 文档解析
│   │   ├── knowledge_base.py   # 知识库
│   │   ├── model_manager.py    # 模型管理
│   │   ├── data_exporter.py    # 数据导出
│   │   ├── admin_service.py    # 管理后台
│   │   └── logging.py    # 结构化日志
│   ├── config/           # 配置管理
│   ├── models/           # 数据模型定义
│   └── state/            # 状态管理
├── static/               # 前端静态文件
│   ├── index.html        # 前端页面
│   ├── style.css         # 样式表
│   ├── app.js            # 前端逻辑
│   ├── style_reminders.css   # 提醒样式
│   ├── style_models.css      # 模型样式
│   ├── app_reminders.js      # 提醒功能
│   └── app_models.js         # 模型切换
├── tests/                # 测试用例
│   ├── test_integration.py   # 集成测试
│   ├── test_db.py        # 数据库测试
│   ├── test_api.py       # API 测试
│   └── ...
├── docker/               # Docker 配置
├── data/                 # SQLite 数据目录
├── docker-compose.yml    # Docker Compose 配置
├── requirements.txt      # Python 依赖
├── main.py               # 主入口
├── plan.md               # 项目规划手册
├── tips.md               # 待办事项
└── README.md             # 本文件
```

---

## 🔧 配置说明

编辑 `.env` 文件配置以下选项：

```bash
# ============================================
# LLM API 配置（硅基流动 - 推荐）
# ============================================
LLM_PROVIDER=openai
LLM_MODEL=deepseek-ai/DeepSeek-V3
LLM_API_KEY=your_api_key_here
LLM_BASE_URL=https://api.siliconflow.cn/v1

# 嵌入模型
EMBEDDING_MODEL=BAAI/bge-large-zh-v1.5

# ============================================
# 数据库配置
# ============================================
# SQLite 模式（开发/测试用，默认）
USE_SQLITE=true
SQLITE_PATH=./data/app.db

# 或 MySQL（生产环境）
# USE_SQLITE=false
# DB_USER=root
# DB_PASSWORD=password
# DB_HOST=localhost
# DB_PORT=3306
# DB_NAME=personal_assistant

# ============================================
# JWT 配置
# ============================================
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRE_DAYS=7

# ============================================
# Redis 配置（可选）
# ============================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
# REDIS_PASSWORD=

# ============================================
# 其他配置
# ============================================
PROJECT_NAME=personal-assistant
DEBUG=false
LOG_LEVEL=INFO
```

---

## 🌐 API 接口

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录

### 会话接口
- `POST /api/sessions` - 创建会话
- `GET /api/sessions` - 会话列表
- `GET /api/sessions/{id}/messages` - 消息历史

### 聊天接口
- `POST /api/chat` - 发送消息（限流 30/分钟）

### 记忆接口
- `POST /api/memories` - 创建记忆
- `GET /api/memories` - 记忆列表（支持语义搜索）
- `POST /api/memories/search` - 语义搜索
- `DELETE /api/memories/{id}` - 删除记忆

### 任务接口
- `POST /api/tasks` - 创建任务
- `GET /api/tasks` - 任务列表
- `PATCH /api/tasks/{id}` - 更新任务
- `DELETE /api/tasks/{id}` - 删除任务

### 提醒接口
- `POST /api/reminders` - 创建提醒
- `GET /api/reminders` - 提醒列表
- `POST /api/reminders/{id}/snooze` - 推迟提醒
- `POST /api/reminders/{id}/dismiss` - 关闭提醒
- `DELETE /api/reminders/{id}` - 删除提醒

### 模型接口
- `GET /api/models` - 获取可用模型列表（17+）
- `GET /api/models/current` - 获取当前模型
- `POST /api/models/select` - 切换模型
- `POST /api/models/compare` - 模型对比

### 知识库接口
- `POST /api/knowledge/upload` - 上传文档
- `GET /api/knowledge/documents` - 文档列表
- `GET /api/knowledge/documents/{id}` - 文档详情
- `DELETE /api/knowledge/documents/{id}` - 删除文档
- `POST /api/knowledge/search` - RAG 检索

### 导出接口
- `GET /api/export/session/{id}` - 导出单会话
- `GET /api/export/sessions` - 导出所有会话
- `GET /api/export/memories` - 导出记忆
- `GET /api/export/tasks` - 导出任务
- `GET /api/export/all` - 完整备份

### 管理后台接口
- `GET /api/admin/stats` - 系统统计
- `GET /api/admin/users` - 用户列表
- `GET /api/admin/users/{id}` - 用户详情
- `POST /api/admin/users/{id}/toggle` - 启用/禁用用户

### 运维接口
- `GET /health` - 健康检查
- `GET /health/live` - 存活探针
- `GET /health/ready` - 就绪探针

**完整 API 文档**: http://localhost:8000/docs

---

## 🧪 测试

```bash
# 运行集成测试
python3 tests/test_integration.py

# 使用 pytest 运行所有测试
python3 -m pytest tests/ -v

# 运行特定测试
python3 tests/test_db.py
python3 tests/test_api.py
```

### 测试结果

| 测试类型 | 通过 | 总计 |
|---------|------|------|
| 集成测试 | 6 | 6 ✅ |
| API 测试 | 2 | 6 |
| 数据库测试 | 2 | 4 |

---

## 🐳 Docker 部署

### 方式 1: Docker Compose（推荐）

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app

# 停止服务
docker-compose down
```

### 方式 2: 单独启动

```bash
# 启动 MySQL
docker run -d \
  --name mysql \
  -e MYSQL_ROOT_PASSWORD=password \
  -e MYSQL_DATABASE=personal_assistant \
  -p 3306:3306 \
  mysql:8.0

# 启动 Redis（可选）
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# 启动应用
python main.py
```

---

## 📝 开发规范

### 代码检查

项目使用 **Pylint** 进行代码质量检查。

```bash
# 提交前自动检查
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

### 分支管理

- `main` - 生产分支
- `develop` - 开发分支
- `feature/*` - 功能分支

---

## 🗺️ 路线图

### ✅ 已完成 (100%)

- [x] 基础对话
- [x] 长期记忆
- [x] 任务管理
- [x] 多用户支持
- [x] Web 界面
- [x] RESTful API (30+ 接口)
- [x] JWT 认证
- [x] 请求限流
- [x] Redis 缓存
- [x] 结构化日志
- [x] 向量语义检索
- [x] 文件上传/知识库
- [x] 定时提醒
- [x] 多 LLM 支持 (17+ 模型)
- [x] 数据导出
- [x] 管理后台

### 可选扩展

- [ ] 移动端适配（PWA）
- [ ] 语音输入/输出

---

## 📊 项目统计

| 指标 | 数值 |
|------|------|
| **完成度** | 100% |
| **API 接口** | 30个 |
| **功能模块** | 21个 |
| **支持模型** | 17+ |
| **代码行数** | ~12,000行 |
| **数据库表** | 8个 |
| **Git 提交** | ~45次 |

---

## 📄 License

MIT License

---

## 🙏 致谢

- [LangGraph](https://github.com/langchain-ai/langgraph)
- [FastAPI](https://fastapi.tiangolo.com/)
- [DeepSeek](https://deepseek.com/)
- [SiliconFlow](https://siliconflow.com/)

---

**项目文档**
- [项目规划手册](./plan.md)
- [待办事项](./tips.md)

**最后更新**: 2026-03-06
