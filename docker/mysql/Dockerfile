# MySQL 8.0 for Personal Assistant

FROM mysql:8.0

# 设置环境变量
ENV MYSQL_ROOT_PASSWORD=root_password
ENV MYSQL_DATABASE=personal_assistant
ENV MYSQL_USER=assistant
ENV MYSQL_PASSWORD=assistant_password

# 字符集配置
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# 复制初始化脚本
COPY init.sql /docker-entrypoint-initdb.d/

# 复制自定义配置
COPY my.cnf /etc/mysql/conf.d/

# 暴露端口
EXPOSE 3306

# 数据卷
VOLUME ["/var/lib/mysql"]
