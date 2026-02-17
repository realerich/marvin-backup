#!/bin/bash
# Marvin 一键恢复脚本
# 用法: ./marvin-restore.sh [备份包路径]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="$SCRIPT_DIR/backups/packages"

echo "🔧 Marvin 一键恢复"
echo "=================="
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 需要Python3"
    exit 1
fi

# 如果有指定备份包
if [ -n "$1" ]; then
    BACKUP_FILE="$1"
else
    # 自动选择最新的备份
    BACKUP_FILE=$(ls -t "$BACKUP_DIR"/*.tar.gz 2>/dev/null | head -1)
    if [ -z "$BACKUP_FILE" ]; then
        echo "❌ 没有找到备份包"
        echo "备份包应该在: $BACKUP_DIR"
        exit 1
    fi
fi

echo "📦 使用备份: $(basename "$BACKUP_FILE")"
echo ""

# 运行恢复
python3 "$SCRIPT_DIR/tools/restore_tools.py" restore "$BACKUP_FILE"

echo ""
echo "===================="
echo "✅ 恢复流程完成!"
echo ""
echo "如需安装依赖，运行:"
echo "  python3 tools/restore_tools.py deps"
