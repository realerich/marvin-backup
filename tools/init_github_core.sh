#!/bin/bash
# GitHub 代码层核心初始化脚本
# 将 GitHub 配置为代码层核心，防止本地服务器崩溃

set -e

echo "🚀 初始化 GitHub 代码层核心..."
echo "================================"

# 配置
REPO_URL="https://github.com/realerich/marvin-backup.git"
WORKSPACE="/root/.openclaw/workspace"

# 进入工作目录
cd "$WORKSPACE"

# 检查 git 配置
if [ ! -d ".git" ]; then
    echo "⚠️  初始化 Git 仓库..."
    git init
    git remote add origin "$REPO_URL"
fi

# 确保远程配置正确
if ! git remote -v | grep -q "realerich/marvin-backup"; then
    echo "⚠️  更新远程仓库地址..."
    git remote remove origin 2>/dev/null || true
    git remote add origin "$REPO_URL"
fi

# 设置 git 用户信息
git config user.email "marvin@liuky.net"
git config user.name "Marvin AI"

# 确保 .gitignore 存在
if [ ! -f ".gitignore" ]; then
    echo "📝 创建 .gitignore..."
    cat > .gitignore << 'EOF'
# 敏感配置（包含密钥）
config/*_secret*
config/*_private*
*.key
*.pem

# 日志文件
*.log
logs/

# 临时文件
*.tmp
*.temp
.DS_Store

# 大型备份文件（GitHub 限制 100MB）
*.tar.gz
!marvin_backup_*.tar.gz

# 运行时数据
__pycache__/
*.pyc
*.pyo
node_modules/
EOF
fi

echo "✅ Git 配置完成"

# 创建关键目录
echo "📁 创建目录结构..."
mkdir -p .github/workflows
mkdir -p .github/ISSUE_TEMPLATE
mkdir -p config
mkdir -p tools
mkdir -p memory

echo "✅ 目录结构创建完成"

# 初始提交
echo "📤 初始同步到 GitHub..."
git add -A || true

# 检查是否有更改要提交
if git diff --cached --quiet 2>/dev/null; then
    echo "ℹ️  没有新的更改需要提交"
else
    git commit -m "初始化 GitHub 代码层核心 - $(date +%Y-%m-%d)" || true
    git push origin main || echo "⚠️ 推送失败，可能需要手动处理"
fi

echo ""
echo "================================"
echo "✅ GitHub 代码层核心初始化完成！"
echo ""
echo "GitHub 仓库: https://github.com/realerich/marvin-backup"
echo "GitHub Pages: https://realerich.github.io/marvin-backup/"
echo ""
echo "常用命令:"
echo "  python3 tools/github_core.py backup    - 备份关键文件"
echo "  python3 tools/github_core.py sync      - 同步到 GitHub"
echo "  python3 tools/github_core.py issues    - 查看 Issues"