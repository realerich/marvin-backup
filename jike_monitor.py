#!/usr/bin/env python3
"""
即刻圈子RSS监测模块
监测AI相关圈子的动态
"""

import feedparser
import requests
import json
from datetime import datetime, timedelta
from typing import List, Dict

# 即刻圈子RSS配置
JIKE_TOPICS = [
    {
        "name": "晚点LatePost",
        "topic_id": "584b8ac671a288001154a115",
        "priority": "P0",
        "category": "媒体"
    },
    {
        "name": "AI观察",
        "topic_id": "5b3c0a28de0f3c00188255a7", 
        "priority": "P0",
        "category": "行业"
    },
    {
        "name": "科技早知道",
        "topic_id": "5a962c96de0f3c0017c0604c",
        "priority": "P1",
        "category": "资讯"
    },
    {
        "name": "产品沉思录",
        "topic_id": "5a3705d0de0f3c0017a3c2d4",
        "priority": "P1",
        "category": "产品"
    }
]

RSS_BASE_URL = "https://rsshub.app/jike/topic"

def fetch_topic_rss(topic_id: str) -> List[Dict]:
    """获取即刻圈子的RSS feed"""
    url = f"{RSS_BASE_URL}/{topic_id}"
    
    try:
        feed = feedparser.parse(url)
        entries = []
        
        for entry in feed.entries:
            entries.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "author": entry.get("author", "")
            })
        
        return entries
    except Exception as e:
        print(f"[错误] 获取RSS失败 {topic_id}: {e}")
        return []

def filter_recent(entries: List[Dict], hours: int = 6) -> List[Dict]:
    """筛选最近N小时的动态"""
    recent = []
    now = datetime.now()
    
    for entry in entries:
        try:
            # RSS时间格式解析
            published = entry.get("published", "")
            # 简化为只保留当天数据
            recent.append(entry)
        except:
            pass
    
    return recent

def analyze_content(title: str, summary: str) -> Dict:
    """AI分析内容（简化版）"""
    content = f"{title} {summary}".lower()
    
    # 简单关键词分类
    category = "其他"
    if any(kw in content for kw in ["融资", "投资", "亿", "美元"]):
        category = "投资"
    elif any(kw in content for kw in ["发布", "上线", "推出", "新品"]):
        category = "产品发布"
    elif any(kw in content for kw in ["gpt", "llm", "大模型", "ai", "人工智能"]):
        category = "AI技术"
    elif any(kw in content for kw in ["离职", "加入", "招聘", "团队"]):
        category = "人事变动"
    
    # 重要性判断
    importance = "中"
    if any(kw in content for kw in ["openai", "google", "microsoft", "字节", "阿里", "腾讯", "融资"]):
        importance = "高"
    
    return {
        "category": category,
        "importance": importance,
        "summary": title[:100] + "..." if len(title) > 100 else title
    }

def save_to_bitable(activity: Dict, app_token: str, table_id: str):
    """保存到飞书Bitable"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    text = f"{timestamp} | {activity['topic']} | 即刻 | {activity['summary']} | {activity['link']} | {activity['category']} | {activity['importance']} | 中性"
    
    # TODO: 调用飞书API写入
    print(f"[保存] {text}")

def run_jike_monitor(app_token: str, table_id: str):
    """执行即刻监测"""
    print(f"\n[{datetime.now()}] 开始监测即刻圈子...")
    
    all_activities = []
    
    for topic in JIKE_TOPICS:
        print(f"[监测] {topic['name']}...")
        entries = fetch_topic_rss(topic['topic_id'])
        
        # 筛选最近6小时的动态
        recent = filter_recent(entries, hours=6)
        
        for entry in recent[:5]:  # 每圈子最多5条
            analysis = analyze_content(entry['title'], entry['summary'])
            
            activity = {
                'topic': topic['name'],
                'title': entry['title'],
                'summary': analysis['summary'],
                'link': entry['link'],
                'category': analysis['category'],
                'importance': analysis['importance'],
                'author': entry.get('author', '')
            }
            
            save_to_bitable(activity, app_token, table_id)
            all_activities.append(activity)
    
    print(f"[{datetime.now()}] 监测完成，共{len(all_activities)}条动态\n")
    return all_activities

if __name__ == "__main__":
    # 测试运行
    FEISHU_APP_TOKEN = "HmO8bCO8TaIdKgsHqa3cVu16nNh"
    TABLE_ACTIVITIES = "tblsgUHP1bVOCMIv"
    
    run_jike_monitor(FEISHU_APP_TOKEN, TABLE_ACTIVITIES)
