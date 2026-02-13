#!/usr/bin/env python3
"""
飞书Bitable任务管理中心
自动同步任务状态，生成日报
"""

import os
import sys
sys.path.insert(0, '/root/.openclaw/workspace')

from marvin_db import MarvinDB
from datetime import datetime, timedelta

# 飞书Bitable配置
FEISHU_APP_TOKEN = "HmO8bCO8TaIdKgsHqa3cVu16nNh"
TABLE_TASKS = "tblsgUHP1bVOCMIv"  # 动态记录表改作任务管理

class TaskManager:
    def __init__(self):
        self.db = MarvinDB()
    
    def parse_task_text(self, text):
        """解析任务文本格式"""
        # 格式：【任务-ID】名称 | 优先级 | 状态 | 截止日期 | 备注
        parts = text.split(' | ')
        if len(parts) >= 4:
            return {
                'id': parts[0].strip('【】').replace('任务-', ''),
                'name': parts[0].split('】')[1] if '】' in parts[0] else parts[0],
                'priority': parts[1],
                'status': parts[2],
                'deadline': parts[3],
                'note': parts[4] if len(parts) > 4 else ''
            }
        return None
    
    def get_all_tasks(self):
        """从Bitable获取所有任务"""
        # 这里需要调用飞书API获取记录
        # 简化版本：返回模拟数据
        return [
            {'id': '001', 'name': '完善GitHub Actions配置', 'priority': 'P1', 'status': '进行中', 'deadline': '2026-02-14'},
            {'id': '002', 'name': '申请Twitter API开发者账号', 'priority': 'P2', 'status': '待办', 'deadline': '按需'},
            {'id': '003', 'name': '每日自动晨报推送', 'priority': 'P1', 'status': '已完成', 'deadline': '2026-02-14'},
        ]
    
    def generate_daily_report(self):
        """生成每日任务报告"""
        tasks = self.get_all_tasks()
        
        todo = [t for t in tasks if t['status'] == '待办']
        in_progress = [t for t in tasks if t['status'] == '进行中']
        done = [t for t in tasks if t['status'] == '已完成']
        
        report = f"""📊 Marvin任务日报 [{datetime.now().strftime('%Y-%m-%d')}]
━━━━━━━━━━━━━━━━━━━

📈 任务统计
• 总任务: {len(tasks)}项
• 进行中: {len(in_progress)}项
• 待办: {len(todo)}项  
• 已完成: {len(done)}项

🔄 进行中 ({len(in_progress)})
"""
        for t in in_progress:
            report += f"  • 【{t['id']}】{t['name']} ({t['priority']})\n"
        
        report += f"\n📥 待办 ({len(todo)})\n"
        for t in todo:
            report += f"  • 【{t['id']}】{t['name']} ({t['priority']})\n"
        
        if done:
            report += f"\n✅ 今日完成 ({len(done)})\n"
            for t in done:
                report += f"  • 【{t['id']}】{t['name']}\n"
        
        report += """
━━━━━━━━━━━━━━━━━━━
💡 回复任务ID可查看详情
💡 回复"新任务：xxx"可创建任务
"""
        return report
    
    def close(self):
        self.db.close()

if __name__ == "__main__":
    manager = TaskManager()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "report":
            print(manager.generate_daily_report())
    else:
        print(manager.generate_daily_report())
    
    manager.close()
