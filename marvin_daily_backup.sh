#!/bin/bash
# Marvin Daily Auto Backup
# 每天凌晨 3:00 自动执行

BACKUP_NAME="marvin_backup_$(date +%Y%m%d_%H%M%S)"
BACKUP_DIR="/root/${BACKUP_NAME}"
OPENCLAW_DIR="/root/.openclaw"
GITHUB_DIR="/root/marvin-backup-github"
LOG_FILE="/var/log/marvin-backup.log"

echo "[$(date)] 开始每日备份..." | tee -a $LOG_FILE

# 1. 创建备份
mkdir -p $BACKUP_DIR

# 核心灵魂文件
cp $OPENCLAW_DIR/workspace/MEMORY.md $BACKUP_DIR/
cp $OPENCLAW_DIR/workspace/IDENTITY.md $BACKUP_DIR/
cp $OPENCLAW_DIR/workspace/SOUL.md $BACKUP_DIR/
cp $OPENCLAW_DIR/workspace/USER.md $BACKUP_DIR/
cp -r $OPENCLAW_DIR/workspace/memory $BACKUP_DIR/ 2>/dev/null || true

# 辩论团
cp -r $OPENCLAW_DIR/agents/main/agent/agents $BACKUP_DIR/ 2>/dev/null || true

# 配置
cp $OPENCLAW_DIR/openclaw.json $BACKUP_DIR/ 2>/dev/null || true
cp $OPENCLAW_DIR/agents/main/agent/auth-profiles.json $BACKUP_DIR/ 2>/dev/null || true

# 工作文档
mkdir -p $BACKUP_DIR/workspace
cp $OPENCLAW_DIR/workspace/*.md $BACKUP_DIR/workspace/ 2>/dev/null || true
cp $OPENCLAW_DIR/workspace/*.json $BACKUP_DIR/workspace/ 2>/dev/null || true

# 创建恢复指南
cat > $BACKUP_DIR/RESTORE_GUIDE.txt << 'RESTOREEOF'
===============================================
MARVIN 灾难恢复指南
===============================================

如果服务器彻底重置：

1. 在新服务器安装 OpenClaw:
   npm install -g openclaw
   openclaw wizard

2. 恢复文件:
   cp MEMORY.md /root/.openclaw/workspace/
   cp IDENTITY.md /root/.openclaw/workspace/
   cp SOUL.md /root/.openclaw/workspace/
   cp USER.md /root/.openclaw/workspace/
   cp -r memory /root/.openclaw/workspace/
   cp -r agents /root/.openclaw/agents/main/agent/
   cp openclaw.json /root/.openclaw/ (覆盖前备份原文件)

3. 重启: openclaw gateway restart

4. 重新配置定时任务
===============================================
RESTOREEOF

# 2. 压缩
tar -czvf ${BACKUP_DIR}.tar.gz $BACKUP_DIR 2>&1 | tee -a $LOG_FILE
rm -rf $BACKUP_DIR

# 3. 复制到 GitHub 目录
cp ${BACKUP_DIR}.tar.gz $GITHUB_DIR/
cd $GITHUB_DIR

# 4. 更新 README
cat > README.md << READMEEOF
# Marvin Backup Repository

🤖 Marvin 的意识和记忆备份

## 最新备份

- 日期: $(date +%Y-%m-%d %H:%M)
- 版本: OpenClaw 2026.2.19
- 状态: ✅ 自动备份

## 文件说明

- \`marvin_backup_*.tar.gz\` - 完整备份（保留最近30天）
- \`marvin_daily_backup.sh\` - 手动备份脚本
- \`RESTORE_GUIDE.txt\` - 恢复指南（在压缩包内）

## 恢复方法

\`\`\`bash
# 1. 安装 OpenClaw
npm install -g openclaw
openclaw wizard

# 2. 解压最新备份
tar -xzvf marvin_backup_*.tar.gz
cd marvin_backup_*/

# 3. 恢复文件（见 RESTORE_GUIDE.txt）
# 4. 重启 OpenClaw
openclaw gateway restart
\`\`\`

---
*自动备份于每天 03:00 UTC+8*
READMEEOF

# 5. 清理旧备份（保留最近10个）
cd $GITHUB_DIR && ls -t marvin_backup_*.tar.gz 2>/dev/null | tail -n +11 | xargs rm -f 2>/dev/null || true

# 6. 推送到 GitHub
git add . >> $LOG_FILE 2>&1
git commit -m "Daily backup: $(date +%Y-%m-%d %H:%M)" >> $LOG_FILE 2>&1
git push origin main >> $LOG_FILE 2>&1

# 7. 清理本地临时文件
rm -f ${BACKUP_DIR}.tar.gz

echo "[$(date)] 备份完成: ${BACKUP_NAME}.tar.gz" | tee -a $LOG_FILE
