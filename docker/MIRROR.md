# Docker 镜像加速配置

## 国内镜像源

项目已配置以下国内镜像源：

| 原镜像 | 国内镜像 |
|--------|----------|
| docker.io/library/mysql | docker.aityp.com/library/mysql |
| docker.io/library/redis | docker.aityp.com/library/redis |
| docker.io/chromadb/chroma | docker.aityp.com/chromadb/chroma |

## 使用方法

### 1. Docker Daemon 全局配置（推荐）

创建或编辑 `/etc/docker/daemon.json`：

```json
{
  "registry-mirrors": [
    "https://docker.aityp.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com"
  ]
}
```

重启 Docker：
```bash
sudo systemctl restart docker
```

### 2. 单镜像指定（当前项目使用）

在 `docker-compose.yml` 或 `Dockerfile` 中直接指定：

```yaml
services:
  mysql:
    image: docker.aityp.com/library/mysql:8.0
```

```dockerfile
FROM docker.aityp.com/library/mysql:8.0
```

## 镜像源列表

- **docker.aityp.com** - 用户提供的镜像站
- **docker.mirrors.ustc.edu.cn** - 中科大镜像
- **hub-mirror.c.163.com** - 网易云镜像
- **docker.m.daocloud.io** - DaoCloud 镜像

## 测试镜像源

```bash
# 测试拉取速度
docker pull docker.aityp.com/library/mysql:8.0

# 查看镜像信息
docker images | grep mysql
```
