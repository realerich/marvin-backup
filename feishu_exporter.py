#!/usr/bin/env python3
"""
飞书文档输出模块
将监测数据自动输出到飞书文档
"""

import requests
from datetime import datetime
from marvin_db import MarvinDB

# 飞书配置
FEISHU_APP_ID = "cli_a90f11e23af91bde"  # 从环境变量或配置文件读取
FEISHU_APP_SECRET = ""  # 需要配置

class FeishuDocExporter:
    def __init__(self):
        self.db = MarvinDB()
        self.access_token = None
    
    def export_daily_summary(self) -> str:
        """导出每日摘要到飞书文档"""
        from datetime import datetime, timedelta
        
        # 获取今日数据
        recent = self.db.get_recent_activities(hours=24)
        
        if not recent:
            content = f"## {datetime.now().strftime('%Y-%m-%d')} AI动态监测\n\n今日暂无重要动态。"
        else:
            content = f"## {datetime.now().strftime('%Y-%m-%d')} AI动态监测\n\n"
            content += f"**今日共监测到 {len(recent)} 条动态**\n\n"
            
            # 高重要性优先
            high_importance = [a for a in recent if a['importance'] == '高']
            if high_importance:
                content += "### 🔴 重点动态\n\n"
                for a in high_importance[:5]:
                    content += f"**{a['name']}** ({a['company']})\n"
                    content += f"- {a['content_summary']}\n"
                    content += f"- [查看原文]({a['url']})\n\n"
            
            # 其他动态
            others = [a for a in recent if a['importance'] != '高']
            if others:
                content += "### 📋 其他动态\n\n"
                for a in others[:10]:
                    content += f"- **{a['name']}**: {a['content_summary'][:80]}...\n"
        
        return content
    
    def export_weekly_report(self, week_number: str = None) -> str:
        """导出周报到飞书文档"""
        if not week_number:
            week_number = datetime.now().strftime("%W")
        
        # 从数据库获取周报
        result = self.db.execute_sql(
            "SELECT * FROM weekly_reports WHERE week_number = %s",
            (f"2026-W{week_number}",)
        )
        
        if result:
            return result[0]['full_report']
        else:
            return f"周报 2026-W{week_number} 尚未生成。"
    
    def create_daily_doc(self, folder_token: str = None) -> str:
        """创建每日监测文档"""
        content = self.export_daily_summary()
        
        # TODO: 调用飞书API创建文档
        # 暂时保存到本地文件
        date_str = datetime.now().strftime("%Y%m%d")
        filename = f"/root/.openclaw/workspace/reports/daily_{date_str}.md"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"[飞书文档] 每日摘要已生成: {filename}")
        return filename
    
    def close(self):
        self.db.close()

if __name__ == "__main__":
    exporter = FeishuDocExporter()
    
    # 生成今日摘要
    exporter.create_daily_doc()
    
    exporter.close()
