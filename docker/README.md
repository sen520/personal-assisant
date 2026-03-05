# Docker 服务配置

## 服务列表

### 1. ChromaDB - 向量数据库
用于存储长期记忆的向量数据库。

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

### 2. Redis - 缓存服务（可选）
用于短期记忆和会话缓存。

**启动命令**:
```bash
docker-compose up -d redis
```

**访问地址**: localhost:6379

## 使用说明

### 启动所有服务
```bash
cd /root/.openclaw/workspace/code/personal-assistant
docker-compose up -d
```

### 查看服务状态
```bash
docker-compose ps
```

### 查看日志
```bash
docker-compose logs -f chromadb
```

### 停止服务
```bash
docker-compose down
```

### 停止并删除数据
```bash
docker-compose down -v
```

## 数据持久化

- **ChromaDB**: 数据存储在 Docker Volume `chroma_data`
- **Redis**: 数据存储在 Docker Volume `redis_data`

## 网络配置

所有服务在同一个 Docker 网络 `assistant-network` 中，可以通过服务名互相访问。

例如，从应用容器访问 ChromaDB:
```python
http://chromadb:8000
```