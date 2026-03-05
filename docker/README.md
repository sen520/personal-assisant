# Docker 服务配置

## 服务列表

### 1. MySQL - 主数据库 ⭐
用于存储用户数据、会话、消息、记忆等核心数据。

**Dockerfile**: `docker/mysql/Dockerfile`  
**初始化脚本**: `docker/mysql/init.sql`

**启动命令**:
```bash
# 启动 MySQL
docker-compose up -d mysql

# 或使用 docker run
docker run -d \
  --name assistant-mysql \
  -p 3306:3306 \
  -v mysql_data:/var/lib/mysql \
  -e MYSQL_ROOT_PASSWORD=root_password \
  -e MYSQL_DATABASE=personal_assistant \
  -e MYSQL_USER=assistant \
  -e MYSQL_PASSWORD=assistant_password \
  mysql:8.0
```

**访问信息**:
- 主机: localhost:3306
- 数据库: personal_assistant
- 用户名: assistant / assistant
- root 密码: root_password

**连接测试**:
```bash
# 进入容器
mysql -h localhost -P 3306 -u assistant -p

# 或使用 docker exec
docker exec -it assistant-mysql mysql -u assistant -p
```

### 2. ChromaDB - 向量数据库
用于存储长期记忆的向量数据，提供语义搜索能力。

**Dockerfile**: `docker/chroma/Dockerfile`

**启动命令**:
```bash
# 使用 docker-compose
docker-compose up -d chromadb

# 或使用 docker run
docker run -d \
  --name chromadb \
  -p 8000:8000 \
  -v chroma_data:/chroma/chroma \
  chromadb/chroma:0.6.0 \
  --host 0.0.0.0 --port 8000 --path /chroma/chroma
```

**访问地址**: http://localhost:8000

### 3. Redis - 缓存服务
用于短期记忆缓存、会话管理、限流计数等。

**镜像**: redis:7-alpine

**启动命令**:
```bash
docker-compose up -d redis
```

**访问地址**: localhost:6379

---

## 使用说明

### 启动所有服务
```bash
cd /root/.openclaw/workspace/code/personal-assistant
docker-compose up -d
```

**启动顺序**:
1. MySQL（先启动，健康检查通过后）
2. Redis（并行启动）
3. ChromaDB（依赖 MySQL）

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
# MySQL 日志
docker-compose logs -f mysql

# ChromaDB 日志
docker-compose logs -f chromadb

# Redis 日志
docker-compose logs -f redis

# 所有服务日志
docker-compose logs -f
```

### 进入数据库
```bash
# MySQL
docker exec -it assistant-mysql mysql -u assistant -p personal_assistant

# Redis
docker exec -it assistant-redis redis-cli
```

### 停止服务
```bash
# 停止但保留数据
docker-compose down

# 停止并删除数据（⚠️ 谨慎使用）
docker-compose down -v
```

### 重启服务
```bash
# 重启 MySQL
docker-compose restart mysql

# 重启所有服务
docker-compose restart
```

---

## 数据持久化

| 服务 | 卷名 | 挂载路径 | 说明 |
|------|------|----------|------|
| MySQL | mysql_data | /var/lib/mysql | 数据库文件 |
| ChromaDB | chroma_data | /chroma/chroma | 向量数据 |
| Redis | redis_data | /data | 缓存数据 |

---

## 网络配置

所有服务在同一个 Docker 网络 `assistant-network` 中，可以通过服务名互相访问。

**服务间访问**:
```python
# 从应用容器访问 MySQL
mysql://assistant:assistant_password@mysql:3306/personal_assistant

# 从应用容器访问 ChromaDB
http://chromadb:8000

# 从应用容器访问 Redis
redis://redis:6379/0
```

---

## 环境变量

### MySQL
| 变量 | 默认值 | 说明 |
|------|--------|------|
| MYSQL_ROOT_PASSWORD | root_password | root 密码 |
| MYSQL_DATABASE | personal_assistant | 默认数据库 |
| MYSQL_USER | assistant | 应用用户 |
| MYSQL_PASSWORD | assistant_password | 应用密码 |

### ChromaDB
| 变量 | 默认值 | 说明 |
|------|--------|------|
| IS_PERSISTENT | TRUE | 持久化存储 |
| CHROMA_SERVER_HOST | 0.0.0.0 | 监听地址 |
| CHROMA_SERVER_HTTP_PORT | 8000 | 监听端口 |

---

## 故障排查

### MySQL 启动失败
```bash
# 查看日志
docker-compose logs mysql

# 检查端口占用
netstat -tlnp | grep 3306

# 删除数据卷后重新启动（会丢失数据）
docker-compose down -v
docker-compose up -d mysql
```

### 连接被拒绝
```bash
# 等待健康检查通过
docker-compose ps

# 手动检查 MySQL 状态
docker exec assistant-mysql mysqladmin ping
```

### 数据库初始化失败
```bash
# 检查 init.sql 语法
docker logs assistant-mysql 2>&1 | grep ERROR

# 手动执行初始化
docker exec -i assistant-mysql mysql -u root -p < docker/mysql/init.sql
```
