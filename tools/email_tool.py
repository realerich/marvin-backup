#!/usr/bin/env python3
"""
邮件收发工具
支持 Gmail / Outlook / 企业邮箱
"""

import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import json
import os
from datetime import datetime

# 配置文件路径
CONFIG_FILE = "/root/.openclaw/workspace/config/email_config.json"

def load_config():
    """加载邮件配置"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def save_config(config):
    """保存邮件配置"""
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    # 设置权限，保护密码
    os.chmod(CONFIG_FILE, 0o600)

def setup_config():
    """交互式配置邮箱"""
    print("📧 邮件配置")
    print("=" * 40)
    
    print("\n选择邮箱类型:")
    print("1. Gmail")
    print("2. Outlook/Office365")
    print("3. QQ邮箱")
    print("4. 163邮箱")
    print("5. 飞书邮箱")
    print("6. 其他")
    
    choice = input("\n选择 (1-6): ").strip()
    
    presets = {
        '1': {'name': 'Gmail', 'imap': 'imap.gmail.com', 'smtp': 'smtp.gmail.com', 'imap_port': 993, 'smtp_port': 587},
        '2': {'name': 'Outlook', 'imap': 'outlook.office365.com', 'smtp': 'smtp.office365.com', 'imap_port': 993, 'smtp_port': 587},
        '3': {'name': 'QQ', 'imap': 'imap.qq.com', 'smtp': 'smtp.qq.com', 'imap_port': 993, 'smtp_port': 587},
        '4': {'name': '163', 'imap': 'imap.163.com', 'smtp': 'smtp.163.com', 'imap_port': 993, 'smtp_port': 994},
        '5': {'name': 'Feishu', 'imap': 'imap.feishu.cn', 'smtp': 'smtp.feishu.cn', 'imap_port': 993, 'smtp_port': 465},
    }
    
    if choice in presets:
        preset = presets[choice]
        config = {
            'name': preset['name'],
            'imap_server': preset['imap'],
            'imap_port': preset['imap_port'],
            'smtp_server': preset['smtp'],
            'smtp_port': preset['smtp_port'],
            'use_tls': True
        }
    else:
        print("\n自定义配置:")
        config = {
            'name': 'Custom',
            'imap_server': input("IMAP 服务器: ").strip(),
            'imap_port': int(input("IMAP 端口 (默认993): ").strip() or "993"),
            'smtp_server': input("SMTP 服务器: ").strip(),
            'smtp_port': int(input("SMTP 端口 (默认587): ").strip() or "587"),
            'use_tls': True
        }
    
    config['email'] = input(f"\n邮箱地址: ").strip()
    config['password'] = input("应用密码/授权码: ").strip()
    
    # 测试连接
    print("\n🔄 测试连接...")
    if test_connection(config):
        save_config(config)
        print("✅ 配置成功！")
        return config
    else:
        print("❌ 连接失败，请检查配置")
        return None

def test_connection(config):
    """测试邮件连接"""
    try:
        # 测试 IMAP
        imap = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'], timeout=30)
        imap.login(config['email'], config['password'])
        imap.logout()
        return True
    except Exception as e:
        print(f"连接错误: {e}")
        return False

def fetch_unread(config=None, limit=10):
    """获取未读邮件"""
    if not config:
        config = load_config()
    if not config:
        return {'error': '未配置邮箱'}
    
    try:
        imap = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'], timeout=30)
        imap.login(config['email'], config['password'])
        imap.select('INBOX')
        
        # 搜索未读邮件
        status, messages = imap.search(None, 'UNSEEN')
        if status != 'OK':
            return {'error': '搜索失败'}
        
        email_ids = messages[0].split()
        emails = []
        
        # 获取最新的 N 封
        for eid in email_ids[-limit:]:
            status, msg_data = imap.fetch(eid, '(RFC822)')
            if status == 'OK':
                msg = email.message_from_bytes(msg_data[0][1])
                
                # 解析主题
                subject, encoding = decode_header(msg['Subject'])[0]
                if isinstance(subject, bytes):
                    subject = subject.decode(encoding or 'utf-8')
                
                # 解析发件人
                from_addr = msg['From']
                
                # 解析日期
                date = msg['Date']
                
                # 解析正文
                body = ""
                if msg.is_multipart():
                    for part in msg.walk():
                        content_type = part.get_content_type()
                        if content_type == 'text/plain':
                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                            break
                else:
                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                
                emails.append({
                    'id': eid.decode(),
                    'subject': subject[:100],
                    'from': from_addr,
                    'date': date,
                    'body': body[:500]  # 只取前500字符
                })
        
        imap.logout()
        return {'success': True, 'count': len(emails), 'emails': emails}
    
    except Exception as e:
        return {'error': str(e)}

def send_email(to, subject, body, html=False, config=None):
    """发送邮件"""
    if not config:
        config = load_config()
    if not config:
        return {'error': '未配置邮箱'}
    
    try:
        msg = MIMEMultipart('alternative')
        msg['From'] = config['email']
        msg['To'] = to
        msg['Subject'] = subject
        
        # 添加正文
        content_type = 'html' if html else 'plain'
        msg.attach(MIMEText(body, content_type, 'utf-8'))
        
        # 发送
        server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
        server.starttls()
        server.login(config['email'], config['password'])
        server.send_message(msg)
        server.quit()
        
        return {'success': True, 'message': f'邮件已发送至 {to}'}
    
    except Exception as e:
        return {'error': str(e)}

def send_daily_summary(to_emails, content):
    """发送每日摘要"""
    subject = f"每日摘要 - {datetime.now().strftime('%Y-%m-%d')}"
    body = f"""
<h2>📧 每日摘要</h2>
<p><strong>日期:</strong> {datetime.now().strftime('%Y年%m月%d日')}</p>
<hr>
{content}
<hr>
<p><em>由 Marvin 自动生成</em></p>
"""
    
    results = []
    for email in to_emails:
        result = send_email(email, subject, body, html=True)
        results.append({'to': email, **result})
    
    return results

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("📧 邮件工具")
        print("\n用法:")
        print("  python3 email_tool.py setup           # 配置邮箱")
        print("  python3 email_tool.py fetch [数量]    # 获取未读邮件")
        print("  python3 email_tool.py send <收件人> <主题> <内容>  # 发送邮件")
        print("\n示例:")
        print("  python3 email_tool.py fetch 5")
        print("  python3 email_tool.py send user@example.com '测试' '这是一封测试邮件'")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'setup':
        setup_config()
    
    elif cmd == 'fetch':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        result = fetch_unread(limit=limit)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == 'send':
        if len(sys.argv) < 5:
            print("用法: send <收件人> <主题> <内容>")
            sys.exit(1)
        result = send_email(sys.argv[2], sys.argv[3], sys.argv[4])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
