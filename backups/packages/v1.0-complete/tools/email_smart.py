#!/usr/bin/env python3
"""
智能邮件检查与分类
自动过滤广告、分类重要邮件、发送每日摘要
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
    
    # 广告/促销关键词
    PROMO_KEYWORDS = [
        'sale', 'promo', 'discount', 'offer', 'deal', 'save', 'off', 
        '优惠', '促销', '折扣', '特价', '限时', 'sale ends', 'last chance',
        '积分', 'points', 'reward', 'bonus', 'cashback', '返现',
        'unsubscribe', '退订', '取消订阅',
    ]
    
    # 重要邮件关键词
    IMPORTANT_KEYWORDS = [
        'security', 'alert', 'warning', 'verify', 'confirm', 'authentication',
        '安全', '验证', '提醒', '警告', '确认', '登录', '密码',
        'invoice', 'receipt', 'payment', '账单', '发票', '付款',
        'meeting', 'calendar', 'schedule', '会议', '日程', '约会',
    ]
    
    # 已知广告发件人域名
    PROMO_DOMAINS = [
        'mail.', 'email.', 'marketing.', 'promo.', 'newsletter.',
        'noreply@', 'no-reply@', 'donotreply@',
    ]
    
    @classmethod
    def classify(cls, email_data):
        """分类单封邮件"""
        subject = email_data.get('subject', '').lower()
        from_addr = email_data.get('from', '').lower()
        body = email_data.get('body', '').lower()
        
        # 计算分数
        promo_score = 0
        important_score = 0
        
        # 主题关键词检测
        for kw in cls.PROMO_KEYWORDS:
            if kw in subject:
                promo_score += 2
        for kw in cls.IMPORTANT_KEYWORDS:
            if kw in subject:
                important_score += 3
        
        # 发件人检测
        for domain in cls.PROMO_DOMAINS:
            if domain in from_addr:
                promo_score += 1
        
        # 正文检测
        if 'unsubscribe' in body or '退订' in body:
            promo_score += 2
        
        # 判断分类
        if important_score > 0:
            return 'important', important_score
        elif promo_score >= 2:
            return 'promo', promo_score
        else:
            return 'normal', 0
    
    @classmethod
    def get_priority(cls, category, score):
        """获取优先级"""
        priorities = {
            'important': '🔴 重要',
            'normal': '🟡 普通',
            'promo': '🟢 促销/广告'
        }
        return priorities.get(category, '🟡 普通')


def generate_daily_summary(hours=24):
    """生成邮件每日摘要"""
    config = load_config()
    if not config:
        return {'error': '未配置邮箱'}
    
    # 获取未读邮件
    result = fetch_unread(config, limit=50)
    if 'error' in result:
        return result
    
    emails = result.get('emails', [])
    if not emails:
        return {'success': True, 'count': 0, 'message': '📭 过去24小时没有新邮件'}
    
    # 加载统计
    stats = load_json(EMAIL_STATS_FILE, {'total_checked': 0, 'history': []})
    notified = load_json(NOTIFIED_FILE, [])
    
    # 分类
    categories = {
        'important': [],
        'normal': [],
        'promo': []
    }
    
    new_important = []
    
    for email in emails:
        category, score = EmailClassifier.classify(email)
        email['category'] = category
        email['score'] = score
        categories[category].append(email)
        
        # 新收到的重要邮件
        if category == 'important' and email['id'] not in notified:
            new_important.append(email)
    
    # 保存统计
    stats['total_checked'] += len(emails)
    stats['last_check'] = datetime.now().isoformat()
    stats['last_counts'] = {
        'total': len(emails),
        'important': len(categories['important']),
        'normal': len(categories['normal']),
        'promo': len(categories['promo'])
    }
    save_json(EMAIL_STATS_FILE, stats)
    
    # 生成摘要报告
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    report = f"📧 邮件摘要 [{now}]\n"
    report += "=" * 50 + "\n\n"
    
    # 重要邮件（需要立即通知）
    if new_important:
        report += f"🔴 重要邮件 ({len(new_important)} 封新)\n"
        report += "-" * 50 + "\n"
        for email in new_important[:5]:
            subject = email['subject'][:40] + "..." if len(email['subject']) > 40 else email['subject']
            report += f"• {subject}\n"
            report += f"  发件人: {email['from'][:30]}\n\n"
        
        # 标记为已通知
        for email in new_important:
            notified.append(email['id'])
        save_json(NOTIFIED_FILE, notified)
    
    # 统计概览
    report += f"📊 分类统计\n"
    report += "-" * 50 + "\n"
    report += f"🔴 重要: {len(categories['important'])} 封\n"
    report += f"🟡 普通: {len(categories['normal'])} 封\n"
    report += f"🟢 促销/广告: {len(categories['promo'])} 封\n"
    report += f"📨 总计: {len(emails)} 封\n\n"
    
    # 普通邮件列表（仅显示发件人）
    if categories['normal']:
        report += "🟡 普通邮件发件人:\n"
        senders = list(set([e['from'].split('<')[0].strip()[:25] for e in categories['normal'][:10]]))
        report += ", ".join(senders)
        if len(categories['normal']) > 10:
            report += f" 等 {len(categories['normal'])} 封"
        report += "\n\n"
    
    # 促销邮件（仅统计数量）
    if categories['promo']:
        report += f"🟢 促销邮件: {len(categories['promo'])} 封（已过滤）\n\n"
    
    report += "💡 回复:\n"
    report += "  '查看重要' - 看重要邮件详情\n"
    report += "  '查看全部' - 看所有邮件\n"
    report += "  '标记已读' - 忽略这些邮件"
    
    return {
        'success': True,
        'count': len(emails),
        'important_count': len(categories['important']),
        'new_important': len(new_important),
        'report': report,
        'emails': emails
    }


def check_important_only():
    """仅检查并通知重要邮件"""
    result = generate_daily_summary()
    
    if 'error' in result:
        return result
    
    if result['new_important'] > 0:
        # 有重要邮件，立即通知
        print(result['report'])
        return result
    else:
        # 没有重要邮件，仅记录
        print(f"✅ 已检查 {result['count']} 封邮件，无重要邮件")
        return {'success': True, 'count': result['count'], 'important': 0}


def show_email_detail(email_id=None, category=None, limit=5):
    """显示邮件详情"""
    config = load_config()
    result = fetch_unread(config, limit=20)
    
    if 'error' in result:
        return result
    
    emails = result['emails']
    
    # 分类
    for email in emails:
        email['category'], _ = EmailClassifier.classify(email)
    
    if category:
        emails = [e for e in emails if e['category'] == category]
    
    if email_id:
        emails = [e for e in emails if e['id'] == email_id]
    
    if not emails:
        print("未找到邮件")
        return
    
    for i, email in enumerate(emails[:limit], 1):
        priority = EmailClassifier.get_priority(email['category'], email.get('score', 0))
        print(f"\n{'='*60}")
        print(f"{i}. [{priority}] {email['subject']}")
        print(f"   发件人: {email['from']}")
        print(f"   日期: {email['date']}")
        print(f"   ID: {email['id']}")
        print(f"\n{email['body'][:800]}...")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        # 默认：生成每日摘要（仅重要邮件通知）
        result = check_important_only()
        if 'report' in result:
            print(result['report'])
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'summary':
        # 完整摘要
        result = generate_daily_summary()
        if 'report' in result:
            print(result['report'])
    
    elif cmd == 'important':
        # 仅重要邮件
        result = check_important_only()
    
    elif cmd == 'detail':
        # 显示详情
        category = sys.argv[2] if len(sys.argv) > 2 else None
        show_email_detail(category=category)
    
    elif cmd == 'stats':
        # 显示统计
        stats = load_json(EMAIL_STATS_FILE, {'total_checked': 0})
        print(f"📊 邮件统计")
        print(f"   累计检查: {stats.get('total_checked', 0)} 封")
        print(f"   上次检查: {stats.get('last_check', 'N/A')}")
        if 'last_counts' in stats:
            counts = stats['last_counts']
            print(f"   最近分类:")
            print(f"     🔴 重要: {counts.get('important', 0)}")
            print(f"     🟡 普通: {counts.get('normal', 0)}")
            print(f"     🟢 促销: {counts.get('promo', 0)}")
    
    else:
        print(f"未知命令: {cmd}")
        print("用法:")
        print("  python3 email_smart.py              # 检查重要邮件")
        print("  python3 email_smart.py summary      # 完整摘要")
        print("  python3 email_smart.py important    # 仅重要")
        print("  python3 email_smart.py detail       # 显示详情")
        print("  python3 email_smart.py stats        # 统计信息")
