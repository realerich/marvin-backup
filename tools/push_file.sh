#!/bin/bash
# 文件自动推送脚本
# 生成文件后自动上传到GitHub并发送链接

set -e

FILE_PATH="$1"
COMMIT_MSG="${2:-添加文件}"

if [ -z "$FILE_PATH" ]; then
    echo "❌ 请提供文件路径"
    echo "用法: ./push_file.sh <文件路径> [提交信息]"
    exit 1
fi

if [ ! -f "$FILE_PATH" ]; then
    echo "❌ 文件不存在: $FILE_PATH"
    exit 1
fi

FILENAME=$(basename "$FILE_PATH")
WORKSPACE="/root/.openclaw/workspace"
OUTPUT_DIR="$WORKSPACE/output"

echo "📤 推送文件: $FILENAME"
echo "========================================"

# 检查文件是否已在output目录
FILE_ABS_DIR=$(cd "$(dirname "$FILE_PATH")" && pwd)
if [ "$FILE_ABS_DIR" != "$OUTPUT_DIR" ]; then
    echo "1️⃣ 复制到output目录..."
    cp "$FILE_PATH" "$OUTPUT_DIR/"
    echo "   ✅ 已复制"
else
    echo "1️⃣ 文件已在output目录，跳过复制"
fi

# 2. 提交到GitHub
echo "2️⃣ 提交到GitHub..."
cd "$WORKSPACE"
git add "output/$FILENAME"
git commit -m "$COMMIT_MSG: $FILENAME" 2>/dev/null || echo "   ℹ️ 无更改需要提交"
git push github main 2>&1 | tail -3

# 3. 生成链接
GITHUB_URL="https://github.com/realerich/marvin-backup/blob/main/output/$FILENAME"
RAW_URL="https://raw.githubusercontent.com/realerich/marvin-backup/main/output/$FILENAME"

echo ""
echo "========================================"
echo "✅ 文件推送完成！"
echo ""
echo "📎 GitHub链接:"
echo "   $GITHUB_URL"
echo ""
echo "📎 直链下载:"
echo "   $RAW_URL"
echo ""
echo "💡 可直接点击链接查看或下载"
echo "========================================"