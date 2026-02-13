#!/bin/bash
# RDS数据迁移脚本
# 本地PostgreSQL → 阿里云RDS

echo "=== PostgreSQL 数据迁移到RDS ==="

# 配置
LOCAL_DB="marvin_db"
LOCAL_USER="marvin"
RDS_HOST="你的RDS地址"
RDS_USER="marvin"
RDS_DB="marvin_db"

# 1. 导出本地数据
echo "[1/4] 导出本地数据..."
pg_dump -h localhost -U $LOCAL_USER -d $LOCAL_DB --no-owner --no-privileges > /tmp/marvin_backup.sql

if [ $? -ne 0 ]; then
    echo "导出失败，请检查本地数据库连接"
    exit 1
fi

echo "  ✓ 导出成功: /tmp/marvin_backup.sql"

# 2. 创建RDS数据库（如果不存在）
echo "[2/4] 检查RDS数据库..."
psql -h $RDS_HOST -U $RDS_USER -d postgres -c "CREATE DATABASE $RDS_DB;" 2>/dev/null || echo "  数据库已存在或连接失败"

# 3. 导入到RDS
echo "[3/4] 导入数据到RDS..."
psql -h $RDS_HOST -U $RDS_USER -d $RDS_DB < /tmp/marvin_backup.sql

if [ $? -eq 0 ]; then
    echo "  ✓ 导入成功"
else
    echo "  ✗ 导入失败"
    exit 1
fi

# 4. 验证数据
echo "[4/4] 验证数据..."
LOCAL_COUNT=$(sudo -u postgres psql -d $LOCAL_DB -t -c "SELECT COUNT(*) FROM persons;" | xargs)
RDS_COUNT=$(psql -h $RDS_HOST -U $RDS_USER -d $RDS_DB -t -c "SELECT COUNT(*) FROM persons;" | xargs)

echo "  本地人员数: $LOCAL_COUNT"
echo "  RDS人员数: $RDS_COUNT"

if [ "$LOCAL_COUNT" = "$RDS_COUNT" ]; then
    echo "  ✓ 数据验证通过"
    echo ""
    echo "=== 迁移完成 ==="
    echo "请修改 marvin_db.py 中的连接配置为RDS地址"
else
    echo "  ✗ 数据不一致，请检查"
fi

# 清理
rm -f /tmp/marvin_backup.sql
