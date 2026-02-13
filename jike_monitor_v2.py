#!/usr/bin/env python3
"""
即刻监测方案 - 通过网页版API
"""

import json
import requests
from datetime import datetime

# 即刻API配置
JIKE_API_BASE = "https://app.jike.ruguoapp.com/1.0"

# 监测的主题/用户ID
JIKE_TARGETS = [
    {
        "type": "topic",
        "name": "晚点LatePost",
        "id": "584b8ac671a288001154a115",
        "priority": "P0"
    },
    {
        "type": "user", 
        "name": "王小川",
        "id": "5e5b3b3c6a9d0a0017f5b8e1",  # 需要获取真实ID
        "priority": "P0"
    }
]

def fetch_topic_feed(topic_id: str, limit: int = 20):
    """获取即刻主题动态"""
    url = f"{JIKE_API_BASE}/messages/list"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Referer": "https://web.okjike.com/"
    }
    
    params = {
        "topicId": topic_id,
        "limit": limit
    }
    
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        print(f"[错误] 获取失败: {e}")
    
    return None

def parse_message(msg: dict) -> dict:
    """解析单条消息"""
    return {
        "id": msg.get("id"),
        "content": msg.get("content", ""),
        "created_at": msg.get("createdAt"),
        "author": msg.get("user", {}).get("screenName", "未知"),
        "url": f"https://web.okjike.com/message/{msg.get('id')}",
        "pictures": [p.get("picUrl") for p in msg.get("pictures", [])],
        "topic": msg.get("topic", {}).get("content", "")
    }

def analyze_content(content: str) -> dict:
    """AI分析内容"""
    text = content.lower()
    
    # 分类
    category = "其他"
    if any(kw in text for kw in ["融资", "投资", "亿", "美元", "估值"]):
        category = "投资融资"
    elif any(kw in text for kw in ["发布", "上线", "推出", "新品", "更新"]):
        category = "产品发布"
    elif any(kw in text for kw in ["gpt", "llm", "大模型", "ai", "人工智能", "claude"]):
        category = "AI技术"
    elif any(kw in text for kw in ["离职", "加入", "招聘", "团队", "人事"]):
        category = "人事变动"
    elif any(kw in text for kw in ["政策", "监管", "法律", "规定"]):
        category = "政策监管"
    
    # 重要性
    importance = "中"
    high_keywords = ["openai", "google", "microsoft", "字节", "阿里", "腾讯", "融资", "收购", "发布"]
    if any(kw in text for kw in high_keywords):
        importance = "高"
    
    # 情绪
    sentiment = "中性"
    if any(kw in text for kw in ["突破", "成功", "增长", "上涨", "利好"]):
        sentiment = "积极"
    elif any(kw in text for kw in ["失败", "下降", "裁员", "亏损", "问题"]):
        sentiment = "消极"
    
    return {
        "category": category,
        "importance": importance,
        "sentiment": sentiment,
        "summary": content[:150] + "..." if len(content) > 150 else content
    }

def save_to_bitable(activity: dict):
    """保存到Bitable（简化版，打印输出）"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    text = f"{timestamp} | {activity['source']} | 即刻 | {activity['summary']} | {activity['url']} | {activity['category']} | {activity['importance']} | {activity['sentiment']}"
    print(f"  → {text}")

def run_jike_monitor():
    """执行即刻监测"""
    print(f"\n[{datetime.now()}] 开始监测即刻...")
    
    # 先监测晚点LatePost主题
    topic = JIKE_TARGETS[0]
    print(f"\n[监测] {topic['name']} ({topic['id']})...")
    
    data = fetch_topic_feed(topic['id'])
    
    if not data or 'data' not in data:
        print(f"  [警告] 获取数据失败或暂无数据")
        print(f"  [提示] 即刻API可能需要登录态，建议：")
        print(f"    1. 使用浏览器获取Cookie后配置")
        print(f"    2. 或等待Twitter API申请完成")
        return
    
    messages = data.get('data', [])
    print(f"  [成功] 获取到{len(messages)}条动态")
    
    for msg in messages[:5]:  # 只处理前5条
        parsed = parse_message(msg)
        analysis = analyze_content(parsed['content'])
        
        activity = {
            'source': f"{topic['name']} - {parsed['author']}",
            'summary': analysis['summary'],
            'url': parsed['url'],
            'category': analysis['category'],
            'importance': analysis['importance'],
            'sentiment': analysis['sentiment']
        }
        
        save_to_bitable(activity)
    
    print(f"[{datetime.now()}] 监测完成\n")

if __name__ == "__main__":
    run_jike_monitor()
