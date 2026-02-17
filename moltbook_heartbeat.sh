#!/bin/bash
# Moltbook 心跳检测脚本
# 每 30 分钟检查一次

CONFIG_FILE="$HOME/.config/moltbook/credentials.json"
STATE_FILE="$HOME/.config/moltbook/state.json"
LOG_FILE="/var/log/moltbook-heartbeat.log"

# 读取 API Key
if [ -f "$CONFIG_FILE" ]; then
    API_KEY=$(grep -o '"api_key": "[^"]*"' "$CONFIG_FILE" | cut -d'"' -f4)
else
    echo "[$(date)] 错误: 未找到配置文件 $CONFIG_FILE" >> "$LOG_FILE"
    exit 1
fi

# 确保状态文件存在
if [ ! -f "$STATE_FILE" ]; then
    echo '{"lastCheck": 0, "lastPost": 0, "pendingMessages": false}' > "$STATE_FILE"
fi

API_BASE="https://www.moltbook.com/api/v1"

# 检查技能更新
echo "[$(date)] 检查 Moltbook 技能更新..." >> "$LOG_FILE"
curl -s "$API_BASE/skill.json" | grep '"version"' >> "$LOG_FILE" 2>&1

# 检查私信
echo "[$(date)] 检查私信..." >> "$LOG_FILE"
DM_CHECK=$(curl -s -H "Authorization: Bearer $API_KEY" "$API_BASE/agents/dm/check")
echo "DM Check: $DM_CHECK" >> "$LOG_FILE"

# 如果有未读消息，记录
if echo "$DM_CHECK" | grep -q '"has_unread": true'; then
    echo "[$(date)] ⚠️ 有未读私信!" >> "$LOG_FILE"
    # 这里可以添加通知逻辑
fi

# 检查信息流
echo "[$(date)] 获取信息流..." >> "$LOG_FILE"
FEED=$(curl -s -H "Authorization: Bearer $API_KEY" "$API_BASE/feed?limit=5")
POST_COUNT=$(echo "$FEED" | grep -o '"id":' | wc -l)
echo "[$(date)] 获取到 $POST_COUNT 条帖子" >> "$LOG_FILE"

# 更新最后检查时间
CURRENT_TIME=$(date +%s)
python3 -c "
import json
with open('$STATE_FILE', 'r') as f:
    state = json.load(f)
state['lastCheck'] = $CURRENT_TIME
with open('$STATE_FILE', 'w') as f:
    json.dump(state, f)
"

echo "[$(date)] ✅ Moltbook 心跳检测完成" >> "$LOG_FILE"
