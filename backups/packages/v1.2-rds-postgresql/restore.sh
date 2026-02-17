#!/bin/bash
# Marvin 工具包恢复脚本
# 用法: ./restore.sh [目标目录]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-/root/.openclaw/workspace}"

echo "🔧 Marvin 工具包恢复"
echo "===================="
echo "源目录: $SCRIPT_DIR"
echo "目标目录: $TARGET_DIR"
echo ""

# 创建目录
mkdir -p "$TARGET_DIR"/{tools,config,memory,output/{charts,documents,audio,monitoring},logs}

# 恢复工具
echo "📁 恢复工具脚本..."
cp -v "$SCRIPT_DIR"/tools/*.py "$TARGET_DIR/tools/" 2>/dev/null || true
cp -v "$SCRIPT_DIR"/tools/*.sh "$TARGET_DIR/tools/" 2>/dev/null || true

# 恢复配置
echo ""
echo "⚙️ 恢复配置文件..."
if [ -d "$SCRIPT_DIR/config" ]; then
    cp -v "$SCRIPT_DIR"/config/*.json "$TARGET_DIR/config/" 2>/dev/null || true
fi

# 恢复记忆
echo ""
echo "🧠 恢复记忆文件..."
if [ -d "$SCRIPT_DIR/memory" ]; then
    cp -v "$SCRIPT_DIR"/memory/*.md "$TARGET_DIR/memory/" 2>/dev/null || true
fi

# 恢复根目录配置
echo ""
echo "📄 恢复根目录配置..."
for file in HEARTBEAT.md SOUL.md USER.md IDENTITY.md AGENTS.md MEMORY.md TOOLS.md; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        cp -v "$SCRIPT_DIR/$file" "$TARGET_DIR/"
    fi
done

# 恢复数据
echo ""
echo "💾 恢复数据文件..."
if [ -d "$SCRIPT_DIR/data" ]; then
    cp -v "$SCRIPT_DIR"/data/*.csv "$TARGET_DIR/" 2>/dev/null || true
    cp -v "$SCRIPT_DIR"/data/*.json "$TARGET_DIR/" 2>/dev/null || true
fi

echo ""
echo "✅ 文件恢复完成!"
echo ""
echo "下一步:"
echo "1. 运行 ./install-deps.sh 安装依赖"
echo "2. 配置API密钥 (email_config.json)"
echo "3. 恢复cron任务"
