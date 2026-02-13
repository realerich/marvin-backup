# 数据库配置 - RDS版本
# 复制此文件为 config.py 并填入实际值

# 阿里云RDS配置
DB_CONFIG = {
    "host": "pgm-xxx.pg.rds.aliyuncs.com",  # 你的RDS内网/公网地址
    "port": "5432",
    "dbname": "marvin_db",
    "user": "marvin",
    "password": "你的密码",
    # "sslmode": "require",  # 如果使用SSL连接，取消注释
}

# 本地备份配置（迁移后保留，用于紧急情况）
DB_CONFIG_LOCAL = {
    "host": "localhost",
    "port": "5432",
    "dbname": "marvin_db",
    "user": "marvin",
    "password": "marvin_2026",
}
