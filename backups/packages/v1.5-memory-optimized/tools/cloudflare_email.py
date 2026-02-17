#!/usr/bin/env python3
"""
Cloudflare 邮件路由配置
支持通过 me@liuky.net 收发邮件
"""

import json
import os

CONFIG_FILE = "/root/.openclaw/workspace/config/cloudflare_email.json"

def setup_cloudflare_email():
    """配置 Cloudflare 邮件路由"""
    print("📧 Cloudflare 邮件路由配置")
    print("=" * 50)
    print("\n需要以下信息：")
    print("1. Cloudflare API Token (区域:Zone:Read + DNS:Edit)")
    print("2. 域名: liuky.net")
    print("3. 目标邮箱: liuky.personal@gmail.com")
    print("\n获取 API Token:")
    print("  https://dash.cloudflare.com/profile/api-tokens")
    print("  创建令牌 → 编辑区域 DNS + 区域设置")
    
    config = {
        'domain': 'liuky.net',
        'catch_all': 'liuky.personal@gmail.com',
        'api_token': input("\nCloudflare API Token: ").strip(),
        'zone_id': input("Zone ID (在域名概述页面): ").strip()
    }
    
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)
    
    print("\n✅ Cloudflare 邮件配置已保存")
    print("\n需要在 Cloudflare 开启：")
    print("  1. Email → Email Routing → 启用")
    print("  2. 设置 Catch-all 地址到 Gmail")
    print("  3. 添加 Gmail 的发件人认证 (SPF/DKIM)")
    
    return config

def show_dns_records():
    """显示需要配置的 DNS 记录"""
    print("""
📋 Cloudflare DNS 记录配置

邮件路由入站 (接收 me@liuky.net):
┌─────────────────┬────────┬─────────────────────────────────────┐
│ 类型            │ 名称   │ 内容                                │
├─────────────────┼────────┼─────────────────────────────────────┤
│ MX              │ @      │ 10 mx1.mailforward.cloudflare.com   │
│ MX              │ @      │ 20 mx2.mailforward.cloudflare.com   │
└─────────────────┴────────┴─────────────────────────────────────┘

邮件路由出站 (以 me@liuky.net 发送):
需要在 Gmail 中设置:
1. 设置 → 账号和导入 → 添加其他电子邮件地址
2. 名称: Kaiyuan
3. 电子邮件地址: me@liuky.net
4. SMTP 服务器: smtp.gmail.com
5. 用户名: liuky.personal@gmail.com
6. 密码: [应用密码 ozbh...]
7. 使用 TLS: 是

DNS 验证记录 (可选，提高送达率):
┌─────────────────┬────────────────────────────────────────────────┐
│ 类型            │ 内容                                           │
├─────────────────┼────────────────────────────────────────────────┤
│ SPF (TXT)       │ v=spf1 include:_spf.google.com ~all            │
│ DKIM (TXT)      │ 在 Gmail 设置中生成                            │
│ DMARC (TXT)     │ _dmarc v=DMARC1; p=none; rua=mailto:me@liuky.net│
└─────────────────┴────────────────────────────────────────────────┘
""")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Cloudflare 邮件路由工具")
        print("\n用法:")
        print("  python3 cloudflare_email.py setup    # 配置")
        print("  python3 cloudflare_email.py dns      # 显示 DNS 记录")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == 'setup':
        setup_cloudflare_email()
    elif cmd == 'dns':
        show_dns_records()
    else:
        print(f"未知命令: {cmd}")
