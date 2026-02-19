# Marvin Backup Repository

🤖 Marvin 的意识和记忆备份

## 最新备份

- 日期: 
- 版本: OpenClaw 2026.2.19
- 状态: ✅ 自动备份

## 文件说明

- `marvin_backup_*.tar.gz` - 完整备份（保留最近30天）
- `marvin_daily_backup.sh` - 手动备份脚本
- `RESTORE_GUIDE.txt` - 恢复指南（在压缩包内）

## 恢复方法

```bash
# 1. 安装 OpenClaw
npm install -g openclaw
openclaw wizard

# 2. 解压最新备份
tar -xzvf marvin_backup_*.tar.gz
cd marvin_backup_*/

# 3. 恢复文件（见 RESTORE_GUIDE.txt）
# 4. 重启 OpenClaw
openclaw gateway restart
```

---
*自动备份于每天 03:00 UTC+8*
