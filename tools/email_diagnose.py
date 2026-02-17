#!/usr/bin/env python3
"""
邮件检查诊断工具
测试 Gmail IMAP 连接
"""

import imaplib
import json
import socket

# 加载配置
CONFIG_FILE = "/root/.openclaw/workspace/config/email_config.json"

with open(CONFIG_FILE, 'r') as f:
    config = json.load(f)

print("📧 邮件连接诊断")
print("=" * 50)
print(f"IMAP 服务器: {config['imap_server']}:{config['imap_port']}")
print(f"邮箱: {config['email']}")
print(f"密码长度: {len(config['password'])} 字符")

# 1. DNS 测试
print("\n1️⃣ DNS 解析测试...")
try:
    ip = socket.gethostbyname(config['imap_server'])
    print(f"✅ DNS 解析成功: {ip}")
except Exception as e:
    print(f"❌ DNS 解析失败: {e}")

# 2. 端口连接测试
print("\n2️⃣ 端口连接测试...")
try:
    sock = socket.create_connection((config['imap_server'], config['imap_port']), timeout=10)
    print(f"✅ 端口 {config['imap_port']} 可连接")
    sock.close()
except Exception as e:
    print(f"❌ 端口连接失败: {e}")

# 3. IMAP SSL 连接测试
print("\n3️⃣ IMAP SSL 连接测试...")
try:
    imap = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'], timeout=30)
    print(f"✅ IMAP SSL 连接成功")
    
    # 4. 登录测试
    print("\n4️⃣ 登录测试...")
    imap.login(config['email'], config['password'])
    print(f"✅ 登录成功")
    
    # 5. 邮箱状态
    print("\n5️⃣ 检查邮箱状态...")
    status, messages = imap.select('INBOX')
    if status == 'OK':
        print(f"✅ 收件箱状态: {messages[0].decode()} 封邮件")
    
    # 6. 搜索未读
    print("\n6️⃣ 搜索未读邮件...")
    status, msg_ids = imap.search(None, 'UNSEEN')
    if status == 'OK':
        unread = len(msg_ids[0].split())
        print(f"✅ 未读邮件: {unread} 封")
    
    imap.logout()
    print("\n✅ 所有测试通过！")
    
except Exception as e:
    print(f"❌ 错误: {e}")