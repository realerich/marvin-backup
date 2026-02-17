#!/usr/bin/env python3
"""
邮件快速检查 - 最终优化版
"""

import imaplib
import email
from email.header import decode_header
import json
import os
from datetime import datetime

CONFIG_FILE = "/root/.openclaw/workspace/config/email_config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

# 重要关键词
IMPORTANT_KEYWORDS = [
    'security', 'alert', 'warning', 'verify', 'authentication',
    '安全', '验证', '提醒', '警告', '确认', '登录', '密码',
    'invoice', 'payment', '账单', '发票', '付款',
    'meeting', 'schedule', '会议', '日程',
]

def check_emails():
    config = load_config()
    if not config:
        print("❌ 未配置邮箱")
        return
    
    try:
        # 连接 IMAP
        imap = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'], timeout=30)
        imap.login(config['email'], config['password'])
        imap.select('INBOX')
        
        # 搜索未读
        status, messages = imap.search(None, 'UNSEEN')
        if status != 'OK':
            print("❌ 搜索失败")
            return
        
        email_ids = messages[0].split()
        total = len(email_ids)
        
        if total == 0:
            print("✅ 没有新邮件")
            imap.logout()
            return
        
        # 只检查最新的10封
        important = []
        for eid in email_ids[-10:]:
            status, msg_data = imap.fetch(eid, '(RFC822)')
            if status != 'OK':
                continue
            
            msg = email.message_from_bytes(msg_data[0][1])
            
            # 解析主题
            subject_hdr = msg['Subject']
            if subject_hdr:
                decoded = decode_header(subject_hdr)[0]
                subject = decoded[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(decoded[1] or 'utf-8', errors='ignore')
            else:
                subject = "(无主题)"
            
            from_addr = msg['From'] or "(未知发件人)"
            
            # 检查是否重要
            is_important = False
            subj_lower = subject.lower()
            for kw in IMPORTANT_KEYWORDS:
                if kw.lower() in subj_lower:
                    is_important = True
                    break
            
            # GitHub alerts
            if 'github' in from_addr.lower() and 'alert' in subj_lower:
                is_important = True
            
            if is_important:
                important.append({'subject': subject, 'from': from_addr})
        
        imap.logout()
        
        # 输出结果
        now = datetime.now().strftime('%H:%M')
        if important:
            print(f"\n🔴 发现 {len(important)} 封重要邮件 [{now}]")
            print("=" * 50)
            for m in important:
                print(f"\n📧 {m['subject'][:60]}")
                print(f"   发件人: {m['from'][:50]}")
        else:
            print(f"✅ 已检查 {min(total, 10)} 封邮件，无重要邮件 [{now}]")
        
    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == '__main__':
    check_emails()