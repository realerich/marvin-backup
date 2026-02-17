#!/bin/bash
# 邮件检查并发送飞书通知
# 通过 cron 每30分钟运行

CHECK_RESULT=$(cd /root/.openclaw/workspace && python3 tools/email_checker.py 2>&1)

# 如果有新邮件通知（包含"📧 新邮件提醒"）
if echo "$CHECK_RESULT" | grep -q "📧 新邮件提醒"; then
    # 提取邮件数量
    COUNT=$(echo "$CHECK_RESULT" | grep -oP '\d+(?= 封)')
    
    # 发送飞书通知（通过 webhook 或消息接口）
    # 这里可以添加飞书消息发送逻辑
    
    # 输出到日志
    echo "[$(date)] 发现 $COUNT 封新邮件"
    echo "$CHECK_RESULT"
else
    echo "[$(date)] 没有新邮件"
fi
