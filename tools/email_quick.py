#!/usr/bin/env python3
"""
邮件智能检查 - 优化版
修复超时问题，限制处理数量
"""

import json
import os
import sys
import re
from datetime import datetime, timedelta

sys.path.insert(0, '/root/.openclaw/workspace/tools')
from email_tool import fetch_unread, load_config

# 配置文件
CONFIG_DIR = "/root/.openclaw/workspace/config"
NOTIFIED_FILE = f"{CONFIG_DIR}/notified_emails.json"
EMAIL_STATS_FILE = f"{CONFIG_DIR}/email_stats.json"

def load_json(filepath, default=None):
    """加载 JSON 文件"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return default if default is not None else {}

def save_json(filepath, data):
    """保存 JSON 文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

class EmailClassifier:
    """邮件智能分类器"""
    
    # 重要邮件关键词
    IMPORTANT_KEYWORDS = [
        'security', 'alert', 'warning', 'verify', 'confirm', 'authentication',
        '安全', '验证', '提醒', '警告', '确认', '登录', '密码',
        'invoice', 'receipt', 'payment', '账单', '发票', '付款',
        'meeting', 'calendar', 'schedule', '会议', '日程', '约会',
    ]
    
    @classmethod
    def classify(cls, email_data):
        """分类单封邮件"""
        subject = email_data.get('subject', '').lower()
        from_addr = email_data.get('from', '').lower()
        
        important_score = 0
        
        # 主题关键词检测
        for kw in cls.IMPORTANT_KEYWORDS:
            if kw in subject:
                important_score += 3
        
        # GitHub 通知标记为重要
        if 'github' in from_addr and '[alert]' in subject.lower():
            important_score += 5
        
        if important_score > 0:
            return 'important', important_score
        else:
            return 'normal', 0


def check_important_emails():
    """检查重要邮件（优化版）"""
    config = load_config()
    if not config:
        return {'error': '未配置邮箱'}
    
    # 限制只获取20封最新邮件
    result = fetch_unread(config, limit=20)
    if 'error' in result:
        return result
    
    emails = result.get('emails', [])
    
    if not emails:
        print("✅ 没有新邮件")
        return {'success': True, 'count': 0, 'important': 0}
    
    notified = load_json(NOTIFIED_FILE, [])
    new_important = []
    
    for email in emails:
        category, score = EmailClassifier.classify(email)
        
        # 新收到的重要邮件
        if category == 'important' and email['id'] not in notified:
            new_important.append(email)
            notified.append(email['id'])
    
    # 保存已通知记录
    save_json(NOTIFIED_FILE, notified[-100:])  # 只保留最近100条
    
    # 输出结果
    now = datetime.now().strftime('%H:%M')
    
    if new_important:
        print(f"\n🔴 发现 {len(new_important)} 封重要邮件 [{now}]")
        print("=" * 50)
        for email in new_important:
            print(f"\n📧 {email['subject']}")
            print(f"   发件人: {email['from']}")
            print(f"   时间: {email['date']}")
        print()
    else:
        print(f"✅ 已检查 {len(emails)} 封邮件，无重要邮件 [{now}]")
    
    return {
        'success': True,
        'count': len(emails),
        'important': len(new_important),
        'emails': new_important
    }


if __name__ == '__main__':
    result = check_important_emails()
    sys.exit(0 if 'error' not in result else 1)