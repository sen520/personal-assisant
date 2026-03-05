# ChromaDB 向量数据库
# 用于个人助理的长期记忆存储

FROM chromadb/chroma:0.6.0

# 设置工作目录
WORKDIR /chroma

# 数据卷挂载点
VOLUME ["/chroma/chroma"]

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["--host", "0.0.0.0", "--port", "8000", "--path", "/chroma/chroma"]
