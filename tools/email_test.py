#!/usr/bin/env python3
"""
邮件检查测试 - 带调试输出
"""

import json
import sys
import os

sys.path.insert(0, '/root/.openclaw/workspace/tools')

print("📧 开始测试邮件检查...")
print("=" * 50)

# 1. 加载配置
print("\n1️⃣ 加载配置...")
from email_tool import load_config
config = load_config()
if not config:
    print("❌ 未配置邮箱")
    sys.exit(1)
print(f"✅ 配置加载: {config['email']}")

# 2. 获取未读邮件
print("\n2️⃣ 获取未读邮件（限制10封）...")
from email_tool import fetch_unread
result = fetch_unread(config, limit=10)
if 'error' in result:
    print(f"❌ 错误: {result['error']}")
    sys.exit(1)

emails = result.get('emails', [])
print(f"✅ 获取到 {len(emails)} 封邮件")

if not emails:
    print("📭 没有新邮件")
    sys.exit(0)

# 3. 分类测试
print("\n3️⃣ 分类邮件...")
from email_smart import EmailClassifier

for i, email in enumerate(emails[:5], 1):
    print(f"  处理第 {i} 封: {email['subject'][:40]}...")
    category, score = EmailClassifier.classify(email)
    print(f"    -> {category} (分数: {score})")

print("\n✅ 测试完成！")
print(f"\n📊 统计:")
print(f"  总邮件: {len(emails)}")
print(f"  测试分类: 5 封")