#!/usr/bin/env python3
"""
邮件清理工具
自动识别并删除营销/促销邮件
"""

import imaplib
import json
import os
from datetime import datetime

CONFIG_FILE = "/root/.openclaw/workspace/config/email_config.json"

# 营销邮件关键词
PROMO_KEYWORDS = [
    'savings', 'sale', 'deal', 'offer', 'promo', 'discount',
    'award', 'reward', 'points', 'bonus', 'free', 'limited',
    'newsletter', 'subscribe', 'unsubscribe', 'marketing',
    'news', 'update', 'digest', 'weekly', 'monthly',
    'zwift', 'garmin', 'hyatt', 'amazon', 'promotion',
    '优惠', '促销', '打折', '特价', '限时', '免费',
    '积分', '奖励', '会员', '订阅', '退订', '广告',
]

# 营销邮件发件人域名
PROMO_DOMAINS = [
    'zwift.com', 'garmin.com', 'hyatt.com', 'discoverasr.com',
    'sendgrid.net', 'mailchimp.com', 'campaign-monitor.com',
]

def load_config():
    """加载配置"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def is_promo_email(subject, from_addr, body=''):
    """判断是否为营销邮件"""
    text = f"{subject} {from_addr} {body}".lower()
    
    # 检查关键词
    for keyword in PROMO_KEYWORDS:
        if keyword in text:
            return True, f"关键词: {keyword}"
    
    # 检查发件人域名
    for domain in PROMO_DOMAINS:
        if domain in from_addr.lower():
            return True, f"营销域名: {domain}"
    
    return False, None

def clean_promo_emails(dry_run=True, limit=50):
    """清理营销邮件"""
    config = load_config()
    
    try:
        # 连接IMAP
        imap = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
        imap.login(config['email'], config['password'])
        
        # 选择收件箱
        imap.select('INBOX')
        
        # 搜索邮件
        _, messages = imap.search(None, 'ALL')
        email_ids = messages[0].split()
        
        # 限制处理数量
        email_ids = email_ids[-limit:] if len(email_ids) > limit else email_ids
        
        promos_found = []
        deleted_count = 0
        
        print(f"📧 检查 {len(email_ids)} 封邮件...")
        print("=" * 60)
        
        for email_id in email_ids:
            try:
                _, msg_data = imap.fetch(email_id, '(RFC822)')
                import email
                msg = email.message_from_bytes(msg_data[0][1])
                
                subject = msg.get('Subject', '')
                from_addr = msg.get('From', '')
                
                # 解码主题
                try:
                    decoded_subject = email.header.decode_header(subject)[0]
                    if isinstance(decoded_subject[0], bytes):
                        subject = decoded_subject[0].decode(decoded_subject[1] or 'utf-8')
                    else:
                        subject = decoded_subject[0]
                except:
                    pass
                
                is_promo, reason = is_promo_email(subject, from_addr)
                
                if is_promo:
                    promos_found.append({
                        'id': email_id.decode(),
                        'subject': subject[:60],
                        'from': from_addr[:40],
                        'reason': reason
                    })
                    
                    if not dry_run:
                        # 删除邮件
                        imap.store(email_id, '+FLAGS', '\\Deleted')
                        deleted_count += 1
                        print(f"🗑️ 已删除: {subject[:50]} ({reason})")
                    else:
                        print(f"🔴 将删除: {subject[:50]} ({reason})")
            
            except Exception as e:
                print(f"⚠️ 处理邮件失败: {e}")
                continue
        
        if not dry_run:
            # 永久删除
            imap.expunge()
        
        imap.close()
        imap.logout()
        
        print("\n" + "=" * 60)
        print(f"📊 发现 {len(promos_found)} 封营销邮件")
        
        if dry_run:
            print("💡 这是预览模式，没有实际删除")
            print("💡 运行 'python3 email_cleaner.py clean' 执行删除")
        else:
            print(f"🗑️ 已删除 {deleted_count} 封邮件")
        
        return {
            'success': True,
            'found': len(promos_found),
            'deleted': deleted_count if not dry_run else 0,
            'dry_run': dry_run,
            'emails': promos_found
        }
    
    except Exception as e:
        return {'success': False, 'error': str(e)}


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("🧹 邮件清理工具")
        print("\n用法:")
        print("  python3 email_cleaner.py preview [数量]  # 预览要删除的邮件")
        print("  python3 email_cleaner.py clean [数量]    # 执行删除")
        print("\n示例:")
        print("  python3 email_cleaner.py preview         # 预览前50封")
        print("  python3 email_cleaner.py preview 20      # 预览前20封")
        print("  python3 email_cleaner.py clean           # 删除前50封营销邮件")
        sys.exit(1)
    
    cmd = sys.argv[1]
    limit = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    
    if cmd == 'preview':
        result = clean_promo_emails(dry_run=True, limit=limit)
        if not result.get('success'):
            print(f"❌ 错误: {result.get('error')}")
    
    elif cmd == 'clean':
        print("⚠️ 即将删除营销邮件！")
        response = input("确认删除? (yes/no): ").strip().lower()
        if response == 'yes':
            result = clean_promo_emails(dry_run=False, limit=limit)
            if not result.get('success'):
                print(f"❌ 错误: {result.get('error')}")
        else:
            print("已取消")
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
