#!/usr/bin/env python3
"""
AI从业者监测系统 - 完整版
基于PostgreSQL + 飞书文档输出
"""

import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict
from marvin_db import MarvinDB

class AIActivityMonitor:
    def __init__(self):
        self.db = MarvinDB()
        self.feishu_webhook = None  # 可选：飞书群机器人
    
    def analyze_with_ai(self, content: str) -> Dict:
        """AI分析内容（集成到OpenClaw时使用）"""
        text = content.lower()
        
        # 分类
        category = "其他"
        if any(kw in text for kw in ["融资", "投资", "亿", "美元", "估值", "轮"]):
            category = "投资融资"
        elif any(kw in text for kw in ["发布", "上线", "推出", "新品", "更新", "v2", "v3"]):
            category = "产品发布"
        elif any(kw in text for kw in ["gpt", "llm", "大模型", "ai", "claude", "openai"]):
            category = "AI技术"
        elif any(kw in text for kw in ["离职", "加入", "招聘", "团队", "人事", "任命"]):
            category = "人事变动"
        elif any(kw in text for kw in ["政策", "监管", "法律", "规定", "禁令"]):
            category = "政策监管"
        
        # 重要性
        importance = "中"
        high_keywords = ["openai", "google", "microsoft", "meta", "字节", "阿里", "腾讯", 
                        "融资", "收购", "ipo", "发布", "突破"]
        if any(kw in text for kw in high_keywords):
            importance = "高"
        
        # 情绪
        sentiment = "中性"
        if any(kw in text for kw in ["突破", "成功", "增长", "上涨", "利好", "创新"]):
            sentiment = "积极"
        elif any(kw in text for kw in ["失败", "下降", "裁员", "亏损", "问题", "危机"]):
            sentiment = "消极"
        
        # 摘要
        summary = content[:200] + "..." if len(content) > 200 else content
        
        return {
            "category": category,
            "importance": importance,
            "sentiment": sentiment,
            "summary": summary
        }
    
    def run_daily_monitor(self):
        """每日监测执行"""
        print(f"\n{'='*60}")
        print(f"[{datetime.now()}] AI从业者每日监测")
        print(f"{'='*60}")
        
        # 获取P0/P1优先级人员（国内+国际）
        persons = self.db.get_active_persons()
        print(f"\n[监测人员] 共 {len(persons)} 人")
        print(f"  P0: {len([p for p in persons if p['priority'] == 'P0'])} 人")
        print(f"  P1: {len([p for p in persons if p['priority'] == 'P1'])} 人")
        print(f"  P2: {len([p for p in persons if p['priority'] == 'P2'])} 人")
        
        # TODO: 接入Twitter API抓取
        # TODO: 接入即刻抓取（需要Cookie）
        
        print("\n[状态] 等待API配置完成...")
        print("  - Twitter API: 需申请开发者账号")
        print("  - 即刻: 需配置Cookie")
        
        # 统计今日数据
        recent = self.db.get_recent_activities(hours=24)
        print(f"\n[今日数据] 已记录 {len(recent)} 条动态")
        
        return len(recent)
    
    def generate_weekly_report(self) -> str:
        """生成周报"""
        # 计算本周时间范围
        today = datetime.now()
        start_of_week = today - timedelta(days=today.weekday())
        end_of_week = start_of_week + timedelta(days=6)
        week_number = today.strftime("%W")
        
        print(f"\n{'='*60}")
        print(f"[周报生成] 2026-W{week_number}")
        print(f"{'='*60}")
        print(f"时间范围: {start_of_week.date()} ~ {end_of_week.date()}")
        
        # 获取统计数据
        stats = self.db.get_weekly_stats(start_of_week, end_of_week)
        
        # 生成报告
        report_lines = [
            f"# AI从业者动态周报 (2026-W{week_number})",
            f"",
            f"**统计周期**: {start_of_week.date()} ~ {end_of_week.date()}",
            f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"",
            f"## 数据概览",
            f"",
            f"- 总动态数: **{stats['total']}** 条",
            f"- 高重要性: **{stats['by_importance'].get('高', 0)}** 条",
            f"- 中重要性: **{stats['by_importance'].get('中', 0)}** 条",
            f"",
            f"### 按平台分布",
        ]
        
        for platform, count in stats['by_platform'].items():
            report_lines.append(f"- {platform}: {count} 条")
        
        report_lines.extend([
            f"",
            f"## 重点事件 (Top 10)",
            f"",
        ])
        
        for i, event in enumerate(stats['key_events'], 1):
            report_lines.append(f"{i}. **{event['name']}** ({event['company']})")
            report_lines.append(f"   - {event['content_summary']}")
            report_lines.append(f"")
        
        report = "\n".join(report_lines)
        
        # 保存到数据库
        self.db.add_weekly_report(
            week_number=f"2026-W{week_number}",
            start_date=start_of_week,
            end_date=end_of_week,
            stats=stats,
            report=report
        )
        
        # 保存到文件
        report_file = f"/root/.openclaw/workspace/reports/weekly_report_2026W{week_number}.md"
        import os
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"\n[报告已保存]")
        print(f"  - 数据库: weekly_reports 表")
        print(f"  - 文件: {report_file}")
        
        return report
    
    def auto_adjust_list(self):
        """自动调整监测名单"""
        print(f"\n{'='*60}")
        print(f"[名单优化] 自动分析调整建议")
        print(f"{'='*60}")
        
        # 获取所有人员
        persons = self.db.get_active_persons()
        
        for person in persons:
            person_id = person['id']
            name = person['name']
            
            # 查询最近30天动态数
            since = datetime.now() - timedelta(days=30)
            result = self.db.execute_sql("""
                SELECT COUNT(*) as count FROM activities 
                WHERE person_id = %s AND published_at > %s
            """, (person_id, since))
            
            activity_count = result[0]['count'] if result else 0
            
            # 活跃度判断
            if activity_count == 0:
                print(f"[建议暂停] {name} - 30天无动态")
            elif activity_count > 20:
                print(f"[活跃度高] {name} - 30天 {activity_count} 条动态")
    
    def query_data(self, question: str) -> str:
        """自然语言查询（AI辅助）"""
        # TODO: 集成AI解析自然语言为SQL
        print(f"\n[查询] {question}")
        print("[提示] 自然语言查询功能待AI集成")
        return "功能开发中..."
    
    def close(self):
        self.db.close()

if __name__ == "__main__":
    monitor = AIActivityMonitor()
    
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "daily":
            monitor.run_daily_monitor()
        elif sys.argv[1] == "weekly":
            monitor.generate_weekly_report()
        elif sys.argv[1] == "adjust":
            monitor.auto_adjust_list()
        else:
            print("用法: python ai_monitor_complete.py [daily|weekly|adjust]")
    else:
        # 默认运行每日监测
        monitor.run_daily_monitor()
    
    monitor.close()
