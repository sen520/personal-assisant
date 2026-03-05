# 个人智能助理系统 - 项目规划手册

**版本**: v1.0  
**日期**: 2026-03-05  
**作者**: KimiClaw

---

## 1. 项目概述

### 1.1 项目背景
基于 LangGraph 的智能个人助理系统，支持多用户、长期记忆、任务管理和智能对话。

### 1.2 核心目标
| 目标 | 优先级 | 状态 |
|------|--------|------|
| 🤖 智能对话与任务处理 | P0 | 🚧 进行中 |
| 🧠 长期记忆管理 | P0 | ✅ 已完成单机版 |
| 👥 多用户登录，数据隔离 | P0 | 📋 待开发 |
| 🔐 MySQL 数据库存储 | P0 | 📋 待开发 |
| 📅 日程与提醒 | P1 | 📋 待开发 |
| 🔍 信息检索与整合 | P1 | 📋 待开发 |

### 1.3 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                      用户层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │  Web 前端   │  │  CLI 客户端 │  │  API 消费者     │ │
│  └──────┬──────┘  └──────┬──────┘  └────────┬────────┘ │
└─────────┼────────────────┼──────────────────┼──────────┘
          │                │                  │
          └────────────────┴──────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    API 网关层                            │
│         FastAPI + JWT 认证 + 请求限流                      │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   核心服务层                             │
│  ┌───────────────────────────────────────────────────┐  │
│  │            LangGraph 工作流引擎                     │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │  │
│  │  │  Input  │ │ Intent  │ │ Memory  │ │ Planning│ │  │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘ │  │
│  │       └─────────────┴───────────┴───────────┘     │  │
│  │                        │                          │  │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ │  │
│  │  │Execution│ │Validation│ │MemoryUp │ │ Output  │ │  │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ │  │
│  └───────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    基础设施层                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │   MySQL     │  │  ChromaDB   │  │     Redis       │ │
│  │  (主数据)   │  │  (向量检索) │  │   (缓存/队列)   │ │
│  └─────────────┘  └─────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 技术栈

### 2.1 后端技术
| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 语言 | Python | 3.11+ | 主开发语言 |
| 框架 | FastAPI | ^0.109 | API 服务 |
| 工作流 | LangGraph | ^0.0.40 | 状态机/工作流 |
| ORM | SQLAlchemy | ^2.0 | 数据库操作 |
| 向量 | ChromaDB | ^0.6.0 | 向量存储 |
| 缓存 | Redis | 7.x | 缓存/会话 |
| 认证 | PyJWT | ^2.8 | JWT Token |
| 部署 | Docker | 24.x | 容器化 |

### 2.2 数据库
| 类型 | 数据库 | 用途 |
|------|--------|------|
| 关系型 | MySQL 8.0 | 用户数据、消息、任务 |
| 向量 | ChromaDB | 语义搜索、长期记忆 |
| 缓存 | Redis | 会话缓存、限流计数 |

### 2.3 AI/LLM
| 组件 | 技术 | 用途 |
|------|------|------|
| LLM | OpenAI API / Kimi API | 对话生成、意图分析 |
| Embedding | text-embedding-3-small | 文本向量化 |

---

## 3. 数据库设计

### 3.1 表结构

```sql
-- 数据库: personal_assistant
-- 字符集: utf8mb4

-- ============================================
-- 1. 用户表 (users)
-- ============================================
CREATE TABLE users (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL COMMENT '用户名',
    email VARCHAR(100) COMMENT '邮箱',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    avatar_url VARCHAR(500) COMMENT '头像URL',
    is_active BOOLEAN DEFAULT TRUE COMMENT '是否激活',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    last_login TIMESTAMP NULL COMMENT '最后登录时间',
    
    UNIQUE KEY uk_username (username),
    UNIQUE KEY uk_email (email),
    KEY idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- ============================================
-- 2. 用户画像表 (user_profiles)
-- ============================================
CREATE TABLE user_profiles (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '画像ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    display_name VARCHAR(100) COMMENT '显示名称',
    preferred_language VARCHAR(10) DEFAULT 'zh' COMMENT '偏好语言',
    communication_style VARCHAR(20) DEFAULT 'concise' COMMENT '沟通风格',
    tech_background JSON COMMENT '技术背景标签',
    common_tasks JSON COMMENT '常用任务',
    active_hours JSON COMMENT '活跃时段',
    timezone VARCHAR(50) DEFAULT 'Asia/Shanghai' COMMENT '时区',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_user_id (user_id),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户画像表';

-- ============================================
-- 3. 会话表 (sessions)
-- ============================================
CREATE TABLE sessions (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '会话ID',
    session_id VARCHAR(64) NOT NULL COMMENT '会话标识',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    title VARCHAR(200) COMMENT '会话标题',
    status ENUM('active', 'paused', 'closed') DEFAULT 'active' COMMENT '状态',
    context_summary TEXT COMMENT '上下文摘要',
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '开始时间',
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '最后活跃',
    ended_at TIMESTAMP NULL COMMENT '结束时间',
    metadata JSON COMMENT '扩展元数据',
    
    UNIQUE KEY uk_session_id (session_id),
    KEY idx_user_sessions (user_id, status, last_active),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='会话表';

-- ============================================
-- 4. 消息表 (messages) - 短期记忆
-- ============================================
CREATE TABLE messages (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '消息ID',
    session_id BIGINT UNSIGNED NOT NULL COMMENT '会话ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    message_uuid VARCHAR(64) NOT NULL COMMENT '消息UUID',
    role ENUM('user', 'assistant', 'system') NOT NULL COMMENT '角色',
    content TEXT NOT NULL COMMENT '内容',
    tokens_used INT UNSIGNED DEFAULT 0 COMMENT '使用Token数',
    latency_ms INT UNSIGNED COMMENT '响应延迟(ms)',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
    metadata JSON COMMENT '扩展信息',
    
    UNIQUE KEY uk_message_uuid (message_uuid),
    KEY idx_session_time (session_id, timestamp),
    KEY idx_user_time (user_id, timestamp),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息表';

-- ============================================
-- 5. 长期记忆表 (memories)
-- ============================================
CREATE TABLE memories (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '记忆ID',
    memory_id VARCHAR(64) NOT NULL COMMENT '记忆标识',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    content TEXT NOT NULL COMMENT '记忆内容',
    category ENUM('fact', 'event', 'preference', 'task', 'note') 
        DEFAULT 'fact' COMMENT '类别',
    importance TINYINT UNSIGNED DEFAULT 3 COMMENT '重要程度(1-5)',
    embedding_id VARCHAR(128) COMMENT '向量存储ID',
    source_session_id BIGINT UNSIGNED COMMENT '来源会话',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    last_accessed TIMESTAMP NULL COMMENT '最后访问',
    access_count INT UNSIGNED DEFAULT 0 COMMENT '访问次数',
    expires_at TIMESTAMP NULL COMMENT '过期时间',
    metadata JSON COMMENT '扩展信息',
    
    UNIQUE KEY uk_memory_id (memory_id),
    KEY idx_user_category (user_id, category),
    KEY idx_user_importance (user_id, importance),
    KEY idx_created_at (created_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (source_session_id) REFERENCES sessions(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='长期记忆表';

-- ============================================
-- 6. 任务表 (tasks)
-- ============================================
CREATE TABLE tasks (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID',
    task_id VARCHAR(64) NOT NULL COMMENT '任务标识',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    parent_task_id BIGINT UNSIGNED COMMENT '父任务ID',
    title VARCHAR(200) NOT NULL COMMENT '标题',
    description TEXT COMMENT '描述',
    status ENUM('pending', 'in_progress', 'completed', 'cancelled', 'failed') 
        DEFAULT 'pending' COMMENT '状态',
    priority TINYINT UNSIGNED DEFAULT 3 COMMENT '优先级(1-5)',
    tags JSON COMMENT '标签',
    due_date TIMESTAMP NULL COMMENT '截止日期',
    remind_at TIMESTAMP NULL COMMENT '提醒时间',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    started_at TIMESTAMP NULL COMMENT '开始时间',
    completed_at TIMESTAMP NULL COMMENT '完成时间',
    metadata JSON COMMENT '扩展信息',
    
    UNIQUE KEY uk_task_id (task_id),
    KEY idx_user_status (user_id, status),
    KEY idx_user_priority (user_id, priority),
    KEY idx_due_date (due_date),
    KEY idx_remind_at (remind_at),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (parent_task_id) REFERENCES tasks(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='任务表';

-- ============================================
-- 7. 对话摘要表 (conversation_summaries)
-- ============================================
CREATE TABLE conversation_summaries (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '摘要ID',
    session_id BIGINT UNSIGNED NOT NULL COMMENT '会话ID',
    user_id BIGINT UNSIGNED NOT NULL COMMENT '用户ID',
    summary_content TEXT NOT NULL COMMENT '摘要内容',
    summary_level TINYINT DEFAULT 2 COMMENT '摘要级别(1-3)',
    message_count INT UNSIGNED DEFAULT 0 COMMENT '包含消息数',
    start_time TIMESTAMP NOT NULL COMMENT '起始时间',
    end_time TIMESTAMP NOT NULL COMMENT '结束时间',
    key_points JSON COMMENT '关键要点',
    extracted_memories JSON COMMENT '提取的记忆ID',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    
    KEY idx_session_level (session_id, summary_level),
    KEY idx_user_time (user_id, start_time),
    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='对话摘要表';

-- ============================================
-- 8. 系统配置表 (system_configs)
-- ============================================
CREATE TABLE system_configs (
    id BIGINT UNSIGNED PRIMARY KEY AUTO_INCREMENT COMMENT '配置ID',
    config_key VARCHAR(100) NOT NULL COMMENT '配置键',
    config_value TEXT COMMENT '配置值',
    description VARCHAR(500) COMMENT '描述',
    is_encrypted BOOLEAN DEFAULT FALSE COMMENT '是否加密',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    
    UNIQUE KEY uk_config_key (config_key)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='系统配置表';
```

### 3.2 数据隔离策略

1. **表级隔离**：所有表均包含 `user_id` 字段
2. **查询隔离**：所有业务查询必须包含 `WHERE user_id = ?`
3. **级联删除**：外键约束 `ON DELETE CASCADE`
4. **索引优化**：每个表按 `user_id` + 常用查询字段建立索引

---

## 4. 项目结构

```
personal-assistant/
├── src/
│   ├── main.py                    # 主入口
│   ├── api/                       # API 服务
│   │   ├── __init__.py
│   │   ├── app.py                 # FastAPI 应用
│   │   ├── deps.py                # 依赖注入
│   │   ├── routers/
│   │   │   ├── auth.py            # 认证路由
│   │   │   ├── chat.py            # 对话路由
│   │   │   ├── memory.py          # 记忆路由
│   │   │   └── task.py            # 任务路由
│   │   └── middleware/
│   │       ├── auth.py            # JWT 中间件
│   │       └── rate_limit.py      # 限流中间件
│   ├── core/                      # 核心业务
│   │   ├── assistant.py           # 主助理类
│   │   ├── session.py             # 会话管理
│   │   └── user.py                # 用户管理
│   ├── graph/                     # LangGraph 工作流
│   │   ├── builder.py             # 图构建器
│   │   ├── edges.py               # 边/路由
│   │   └── nodes/                 # 8个工作流节点
│   │       ├── __init__.py
│   │       ├── input.py
│   │       ├── intent.py
│   │       ├── memory.py
│   │       ├── planning.py
│   │       ├── execution.py
│   │       ├── validation.py
│   │       ├── memory_update.py
│   │       └── output.py
│   ├── memory/                    # 记忆系统
│   │   ├── __init__.py
│   │   ├── system.py              # 统一入口
│   │   ├── short_term.py          # 短期记忆
│   │   ├── long_term.py           # 长期记忆
│   │   ├── vector_store.py        # 向量存储
│   │   ├── user_profile.py        # 用户画像
│   │   └── constraints.py         # 约束检查
│   ├── models/                    # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py                # 基础模型
│   │   └── database.py            # ORM 模型
│   ├── db/                        # 数据库
│   │   ├── __init__.py
│   │   ├── connection.py          # 连接池
│   │   ├── migrations/            # Alembic 迁移
│   │   └── repositories/          # 数据仓库
│   ├── llm/                       # LLM 客户端
│   │   ├── __init__.py
│   │   ├── client.py              # 统一客户端
│   │   ├── embeddings.py          # 嵌入模型
│   │   └── prompts/               # 提示词模板
│   ├── auth/                      # 认证模块
│   │   ├── __init__.py
│   │   ├── jwt.py                 # JWT 工具
│   │   ├── password.py            # 密码处理
│   │   └── permissions.py         # 权限控制
│   ├── tools/                     # 工具集
│   │   ├── __init__.py
│   │   ├── base.py                # 工具基类
│   │   ├── search.py              # 搜索工具
│   │   ├── task_manager.py        # 任务管理
│   │   └── file_ops.py            # 文件操作
│   ├── utils/                     # 工具函数
│   │   ├── __init__.py
│   │   ├── logger.py              # 日志配置
│   │   ├── text_processor.py      # 文本处理
│   │   └── validators.py          # 验证器
│   └── config/                    # 配置
│       ├── __init__.py
│       ├── settings.py            # 配置类
│       └── constants.py           # 常量
├── tests/                         # 测试
│   ├── unit/                      # 单元测试
│   ├── integration/               # 集成测试
│   └── conftest.py                # pytest 配置
├── sql/                           # SQL 脚本
│   └── init.sql                   # 数据库初始化
├── docker/                        # Docker 配置
│   ├── mysql/
│   │   └── Dockerfile
│   ├── chroma/
│   │   └── Dockerfile
│   └── redis/
│       └── Dockerfile
├── docker-compose.yml             # Docker Compose
├── alembic.ini                    # Alembic 配置
├── pytest.ini                     # pytest 配置
├── requirements.txt               # 依赖
├── pyproject.toml                 # 项目配置
├── README.md                      # 项目说明
├── tips.md                        # 待办事项
└── plan.md                        # 本规划手册
```

---

## 5. 开发计划

### Phase 1: 基础设施 (2周)
- [ ] MySQL 数据库搭建
- [ ] Docker 环境配置
- [ ] 数据库 ORM 建模
- [ ] 用户认证模块
- [ ] 数据迁移脚本

### Phase 2: 记忆系统改造 (1周)
- [ ] 适配多用户架构
- [ ] 短期记忆 MySQL 化
- [ ] 长期记忆整合
- [ ] 用户画像管理

### Phase 3: 核心工作流 (2周)
- [ ] LangGraph 节点实现
- [ ] LLM 客户端集成
- [ ] 状态管理机制
- [ ] 端到端测试

### Phase 4: API 服务 (1周)
- [ ] FastAPI 接口开发
- [ ] WebSocket 支持
- [ ] 文档生成
- [ ] 接口测试

### Phase 5: 工具与优化 (1周)
- [ ] 工具集实现
- [ ] 性能优化
- [ ] 监控日志
- [ ] 部署文档

---

## 6. 部署架构

```
                    ┌─────────────────┐
                    │   Nginx/ALB     │
                    │   负载均衡       │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
       ┌──────▼──────┐ ┌────▼────┐  ┌──────▼──────┐
       │  API 服务   │ │ API 服务 │  │  API 服务   │
       │  Instance 1 │ │Instance 2│  │  Instance N │
       └──────┬──────┘ └────┬────┘  └──────┬──────┘
              │             │              │
              └─────────────┼──────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
┌──────▼──────┐    ┌────────▼────────┐   ┌──────▼──────┐
│   MySQL     │    │    ChromaDB     │   │    Redis    │
│  (主从复制)  │    │   (向量存储)     │   │  (集群模式)  │
└─────────────┘    └─────────────────┘   └─────────────┘
```

### 环境配置

| 环境 | MySQL | ChromaDB | Redis | 实例数 |
|------|-------|----------|-------|--------|
| Dev | 单机 | 单机 | 单机 | 1 |
| Test | 单机 | 单机 | 单机 | 1 |
| Prod | 主从 | 集群 | 集群 | 3+ |

---

## 7. 接口规范

### 7.1 认证接口

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
POST /api/v1/auth/refresh
GET  /api/v1/auth/me
```

### 7.2 对话接口

```http
POST   /api/v1/chat/sessions          # 创建会话
GET    /api/v1/chat/sessions          # 获取会话列表
GET    /api/v1/chat/sessions/{id}     # 获取会话详情
POST   /api/v1/chat/sessions/{id}/messages  # 发送消息
GET    /api/v1/chat/sessions/{id}/messages  # 获取消息历史
WS     /api/v1/chat/stream            # WebSocket 流式对话
DELETE /api/v1/chat/sessions/{id}     # 删除会话
```

### 7.3 记忆接口

```http
GET    /api/v1/memories               # 搜索记忆
POST   /api/v1/memories               # 创建记忆
GET    /api/v1/memories/{id}          # 获取记忆
PUT    /api/v1/memories/{id}          # 更新记忆
DELETE /api/v1/memories/{id}          # 删除记忆
```

### 7.4 任务接口

```http
GET    /api/v1/tasks                  # 获取任务列表
POST   /api/v1/tasks                  # 创建任务
GET    /api/v1/tasks/{id}             # 获取任务详情
PUT    /api/v1/tasks/{id}             # 更新任务
DELETE /api/v1/tasks/{id}             # 删除任务
POST   /api/v1/tasks/{id}/complete    # 完成任务
```

---

## 8. 风险评估

| 风险 | 可能性 | 影响 | 应对措施 |
|------|--------|------|----------|
| 数据泄露 | 低 | 高 | 加密存储、访问控制、审计日志 |
| 性能瓶颈 | 中 | 中 | 缓存、索引优化、读写分离 |
| LLM 服务不可用 | 中 | 高 | 多 LLM 备份、降级策略 |
| 数据丢失 | 低 | 高 | 定期备份、主从复制 |
| 并发问题 | 中 | 中 | 锁机制、事务隔离 |

---

## 9. 附录

### 9.1 命名规范

- **表名**: 小写下划线，复数形式（如 `user_profiles`）
- **字段名**: 小写下划线（如 `created_at`）
- **索引名**: `idx_表名_字段名`
- **外键名**: `fk_表名_关联表名`

### 9.2 Git 工作流

```
main (生产分支)
  ↑
develop (开发分支)
  ↑
feature/xxx (功能分支)
  ↑
  PR → Code Review → Merge
```

### 9.3 提交规范

```
【code by kimiclaw】<type>: <subject>

types:
  feat: 新功能
  fix: 修复
  docs: 文档
  style: 格式
  refactor: 重构
  test: 测试
  chore: 构建/工具
```

---

*文档版本: v1.0*  
*最后更新: 2026-03-05*
