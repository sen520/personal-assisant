# 项目进展与待办事项

## 📅 日期：2026-03-05

---

## 🎯 项目目标

基于 LangGraph 的个人智能助理系统，支持：
- 🤖 智能对话与任务处理
- 🧠 长期记忆管理（短期+长期+用户画像）
- 👥 **多用户登录使用，用户间数据完全隔离**
- 🔐 **MySQL 数据库存储**
- 📅 日程与提醒
- 🔍 信息检索与整合

---

## ✅ 已完成

### 1. 项目初始化
- [x] 创建项目基础结构
- [x] 配置 pyproject.toml、requirements.txt
- [x] 配置 Git 仓库（main + develop 分支）
- [x] 配置远程仓库（GitHub PR 工作流）

### 2. Docker 环境
- [x] ChromaDB Dockerfile
- [x] docker-compose.yml（ChromaDB + Redis）
- [x] Docker 使用文档
- [ ] ~~启动 ChromaDB 容器~~（网络问题，待后续）

### 3. 记忆系统（核心功能 - 单机版）
- [x] 数据模型（Message, Task, MemoryItem, Intent 等）
- [x] 短期记忆（滑动窗口 + 智能压缩 + 关键节点）
- [x] 长期记忆（向量存储 + 语义检索）
- [x] 用户画像管理
- [x] 约束检查（敏感信息/危险命令/行为准则）
- [x] 统一入口 MemorySystem 类

---

## 📝 待办事项

### 🔴 高优先级（架构调整）

#### 1. 多用户架构改造
- [ ] 用户认证系统（登录/注册/Token）
- [ ] 用户会话管理
- [ ] 数据隔离层（按 user_id 过滤）
- [ ] 权限控制

#### 2. MySQL 数据库迁移
- [ ] 设计数据库表结构（见下方 Schema）
- [ ] 安装 MySQL 驱动（pymysql/sqlalchemy）
- [ ] 数据库连接池配置
- [ ] 数据模型 ORM 映射
- [ ] 数据库迁移脚本（Alembic）
- [ ] 数据从 SQLite 迁移到 MySQL

#### 3. Docker 环境更新
- [ ] MySQL Dockerfile
- [ ] 更新 docker-compose.yml（添加 MySQL 服务）
- [ ] 数据库初始化脚本

### 🟡 高优先级（功能开发）

#### 4. LangGraph 工作流节点（8个）
- [ ] `input.py` - 输入预处理节点
- [ ] `intent.py` - 意图分析节点
- [ ] `memory.py` - 记忆检索节点（需适配多用户）
- [ ] `planning.py` - 工作流规划节点
- [ ] `execution.py` - 执行节点
- [ ] `validation.py` - 验证节点
- [ ] `memory_update.py` - 记忆更新节点（需适配多用户）
- [ ] `output.py` - 输出生成节点

#### 5. LLM 客户端集成
- [ ] LLM 客户端封装
- [ ] 嵌入模型
- [ ] 提示词模板系统

### 🟢 中优先级

#### 6. API 服务
- [ ] FastAPI 接口封装
- [ ] RESTful API 设计
- [ ] WebSocket 实时对话

#### 7. 工具集实现
- [ ] 搜索工具
- [ ] 任务管理工具
- [ ] 时间/日程工具

### ⚪ 低优先级

#### 8. 测试与文档
- [ ] 单元测试
- [ ] 集成测试
- [ ] API 文档

---

## 🗄️ MySQL 数据库设计

### 数据库名：`personal_assistant`

### 表结构

```sql
-- 1. 用户表
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMP NULL
);

-- 2. 用户画像表
CREATE TABLE user_profiles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT UNIQUE NOT NULL,
    name VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'zh',
    communication_style VARCHAR(20) DEFAULT 'concise',
    tech_background JSON,
    common_tasks JSON,
    active_hours JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. 会话表
CREATE TABLE sessions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    metadata JSON,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_sessions (user_id, status)
);

-- 4. 消息表（短期记忆）
CREATE TABLE messages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    user_id INT NOT NULL,
    role VARCHAR(20) NOT NULL,  -- user/assistant/system
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSON,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_session_messages (session_id, timestamp)
);

-- 5. 长期记忆表
CREATE TABLE memories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    memory_id VARCHAR(64) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(20) DEFAULT 'general',  -- fact/event/preference/task
    importance INT DEFAULT 3,
    embedding VECTOR(768),  -- 向量存储（需启用向量插件）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_accessed TIMESTAMP NULL,
    access_count INT DEFAULT 0,
    metadata JSON,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_memories (user_id, category),
    INDEX idx_memories_importance (user_id, importance)
);

-- 6. 任务表
CREATE TABLE tasks (
    id INT PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(64) UNIQUE NOT NULL,
    user_id INT NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    priority INT DEFAULT 3,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP NULL,
    completed_at TIMESTAMP NULL,
    tags JSON,
    metadata JSON,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_tasks (user_id, status),
    INDEX idx_tasks_priority (user_id, priority)
);

-- 7. 对话摘要表（中期记忆）
CREATE TABLE conversation_summaries (
    id INT PRIMARY KEY AUTO_INCREMENT,
    session_id INT NOT NULL,
    user_id INT NOT NULL,
    summary_content TEXT NOT NULL,
    level INT DEFAULT 2,  -- 1=最近, 2=中期, 3=早期
    message_count INT DEFAULT 0,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    key_points JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
```

### 数据隔离策略

1. **表级隔离**：所有表都有 `user_id` 字段
2. **查询过滤**：所有查询必须带 `WHERE user_id = ?`
3. **外键约束**：级联删除，用户删除时清理所有数据
4. **索引优化**：按 user_id 建立索引，确保查询性能

---

## 🐛 已知问题

- Docker Hub 连接超时，ChromaDB 容器无法启动
  - 方案1：等有代理时再启动
  - 方案2：使用本地 SQLite 方案（已实现，可用）

---

## 💡 设计决策记录

1. **记忆分层**：短期（会话级）+ 长期（持久化）+ 用户画像
2. **长对话处理**：滑动窗口 + 智能摘要 + 关键节点
3. **安全检查**：敏感信息过滤 + 危险命令检测 + 输出验证
4. **Git 工作流**：develop 分支开发 → PR → main 合并
5. **多用户隔离**：表级 user_id 字段 + 查询过滤 + 外键级联
6. **数据库选择**：MySQL 8.0 + 向量插件（或单独 ChromaDB 存向量）

---

## 🎯 下一步建议

1. **先设计 MySQL Schema** 并创建初始化脚本
2. **搭建 MySQL Docker 环境**（本地或服务器）
3. **实现用户认证模块**（注册/登录/JWT）
4. **改造记忆系统** 支持多用户和 MySQL
5. **实现工作流节点**

---

*最后更新：2026-03-05*
