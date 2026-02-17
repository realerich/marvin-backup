#!/usr/bin/env python3
"""
邮件检查并通知
定期检查 Gmail 新邮件，如有重要邮件则通知飞书
"""

import json
import os
import sys

# 添加工具路径
sys.path.insert(0, '/root/.openclaw/workspace/tools')
from email_tool import fetch_unread, load_config

# 已通知的邮件ID记录文件
NOTIFIED_FILE = "/root/.openclaw/workspace/config/notified_emails.json"

def load_notified():
    """加载已通知的邮件ID"""
    if os.path.exists(NOTIFIED_FILE):
        with open(NOTIFIED_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_notified(notified_ids):
    """保存已通知的邮件ID"""
    os.makedirs(os.path.dirname(NOTIFIED_FILE), exist_ok=True)
    with open(NOTIFIED_FILE, 'w') as f:
        json.dump(list(notified_ids), f)

def check_and_notify():
    """检查邮件并通知"""
    config = load_config()
    if not config:
        print("❌ 未配置邮箱")
        return
    
    print(f"📧 检查 {config['email']} 的新邮件...")
    
    # 获取未读邮件
    result = fetch_unread(config, limit=20)
    
    if 'error' in result:
        print(f"❌ 获取失败: {result['error']}")
        return
    
    emails = result.get('emails', [])
    if not emails:
        print("📭 没有新邮件")
        return
    
    # 加载已通知记录
    notified = load_notified()
    
    # 过滤出新邮件
    new_emails = [e for e in emails if e['id'] not in notified]
    
    if not new_emails:
        print(f"📭 没有新邮件（已通知 {len(notified)} 封）")
        return
    
    print(f"📬 发现 {len(new_emails)} 封新邮件")
    
    # 生成通知内容
    notification = f"📧 新邮件提醒 ({len(new_emails)} 封)\n" + "=" * 40 + "\n"
    
    for i, email in enumerate(new_emails[:5], 1):  # 最多显示5封
        subject = email['subject'][:50] + "..." if len(email['subject']) > 50 else email['subject']
        from_addr = email['from'][:30]
        notification += f"\n{i}. {subject}\n   发件人: {from_addr}\n"
        
        # 标记为已通知
        notified.add(email['id'])
    
    if len(new_emails) > 5:
        notification += f"\n... 还有 {len(new_emails) - 5} 封未显示"
    
    notification += f"\n\n💡 回复 '查看邮件' 获取详情"
    
    # 保存通知记录
    save_notified(notified)
    
    # 输出通知（会被飞书接收）
    print(notification)
    
    return notification

if __name__ == '__main__':
    check_and_notify()
