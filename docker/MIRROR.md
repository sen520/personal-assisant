# Docker 镜像加速配置

## 国内镜像源

项目已配置以下国内镜像源：

| 原镜像 | 国内镜像 |
|--------|----------|
| docker.io/library/mysql | swr.cn-north-4.myhuaweicloud.com/ddn-k8s/gcr.io/ml-pipeline/mysql:8.0.26 |
| docker.io/library/redis | swr.cn-north-4.myhuaweicloud.com/ddn-k8s/quay.io/opstree/redis:v7.0.5 |
| docker.io/chromadb/chroma | swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/chromadb/chroma:latest |

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
    image: swr.cn-north-4.myhuaweicloud.com/ddn-k8s/gcr.io/ml-pipeline/mysql:8.0.26
```

```dockerfile
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/gcr.io/ml-pipeline/mysql:8.0.26
```

## 镜像源列表

- **swr.cn-north-4.myhuaweicloud.com** - 华为云镜像（推荐，稳定）
- **docker.aityp.com** - 用户提供的镜像站（需认证）
- **docker.mirrors.ustc.edu.cn** - 中科大镜像
- **hub-mirror.c.163.com** - 网易云镜像
- **docker.m.daocloud.io** - DaoCloud 镜像

## 测试镜像源

```bash
# 测试拉取速度
docker pull swr.cn-north-4.myhuaweicloud.com/ddn-k8s/gcr.io/ml-pipeline/mysql:8.0.26

# 查看镜像信息
docker images | grep mysql
```

## 注意事项

- 华为云镜像站无需认证，可直接使用
- 部分镜像站可能需要登录或已停止服务
- 如遇到拉取失败，尝试更换其他镜像源
