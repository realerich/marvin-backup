#!/usr/bin/env python3
"""
RDS 到 GitHub 数据同步工具
将 RDS 数据导出到 GitHub，实现数据可视化
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))
from rds_manager import RDSManager


class RDSGitHubSync:
    """RDS 到 GitHub 同步"""
    
    def __init__(self):
        self.rds = RDSManager()
        self.output_dir = Path("/root/.openclaw/workspace/data")
        self.output_dir.mkdir(exist_ok=True)
    
    def export_system_metrics(self, days=7):
        """导出系统监控指标"""
        try:
            with self.rds.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM system_metrics 
                        WHERE timestamp > NOW() - INTERVAL '%s days'
                        ORDER BY timestamp DESC
                    """, (days,))
                    rows = cursor.fetchall()
                    
                    # 转换为字典列表
                    columns = [desc[0] for desc in cursor.description]
                    data = []
                    for row in rows:
                        data.append(dict(zip(columns, row)))
                    
                    # 保存为 JSON
                    output_file = self.output_dir / f"system_metrics_{days}d.json"
                    with open(output_file, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    
                    # 生成 CSV
                    import csv
                    csv_file = self.output_dir / f"system_metrics_{days}d.csv"
                    with open(csv_file, 'w', newline='') as f:
                        if data:
                            writer = csv.DictWriter(f, fieldnames=columns)
                            writer.writeheader()
                            writer.writerows(data)
                    
                    print(f"✅ 导出 {len(data)} 条监控指标")
                    return True
        except Exception as e:
            print(f"❌ 导出监控指标失败: {e}")
            return False
    
    def export_tasks(self, status=None):
        """导出任务数据"""
        try:
            with self.rds.get_connection() as conn:
                with conn.cursor() as cursor:
                    if status:
                        cursor.execute("""
                            SELECT * FROM tasks 
                            WHERE status = %s
                            ORDER BY created_at DESC
                        """, (status,))
                    else:
                        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC")
                    
                    rows = cursor.fetchall()
                    columns = [desc[0] for desc in cursor.description]
                    
                    data = []
                    for row in rows:
                        data.append(dict(zip(columns, row)))
                    
                    output_file = self.output_dir / "tasks.json"
                    with open(output_file, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    
                    print(f"✅ 导出 {len(data)} 条任务")
                    return True
        except Exception as e:
            print(f"❌ 导出任务失败: {e}")
            return False
    
    def export_email_stats(self, days=30):
        """导出邮件统计"""
        try:
            with self.rds.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT 
                            DATE(received_at) as date,
                            category,
                            COUNT(*) as count
                        FROM emails
                        WHERE received_at > NOW() - INTERVAL '%s days'
                        GROUP BY DATE(received_at), category
                        ORDER BY date DESC
                    """, (days,))
                    
                    rows = cursor.fetchall()
                    
                    data = {}
                    for row in rows:
                        date, category, count = row
                        if date not in data:
                            data[date] = {}
                        data[date][category] = count
                    
                    output_file = self.output_dir / f"email_stats_{days}d.json"
                    with open(output_file, 'w') as f:
                        json.dump(data, f, indent=2, default=str)
                    
                    print(f"✅ 导出 {len(data)} 天邮件统计")
                    return True
        except Exception as e:
            print(f"❌ 导出邮件统计失败: {e}")
            return False
    
    def generate_dashboard_data(self):
        """生成仪表盘数据"""
        try:
            dashboard = {
                'generated_at': datetime.now().isoformat(),
                'summary': {}
            }
            
            with self.rds.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 系统监控摘要
                    cursor.execute("""
                        SELECT 
                            AVG(cpu_percent) as avg_cpu,
                            MAX(cpu_percent) as max_cpu,
                            AVG(memory_percent) as avg_memory,
                            MAX(memory_percent) as max_memory
                        FROM system_metrics
                        WHERE timestamp > NOW() - INTERVAL '24 hours'
                    """)
                    row = cursor.fetchone()
                    dashboard['summary']['system_24h'] = {
                        'avg_cpu': round(row[0], 2) if row[0] else 0,
                        'max_cpu': round(row[1], 2) if row[1] else 0,
                        'avg_memory': round(row[2], 2) if row[2] else 0,
                        'max_memory': round(row[3], 2) if row[3] else 0
                    }
                    
                    # 任务统计
                    cursor.execute("""
                        SELECT status, COUNT(*) 
                        FROM tasks 
                        GROUP BY status
                    """)
                    dashboard['summary']['tasks'] = {row[0]: row[1] for row in cursor.fetchall()}
                    
                    # 飞书消息
                    cursor.execute("""
                        SELECT COUNT(*) FROM feishu_messages
                        WHERE created_at > NOW() - INTERVAL '24 hours'
                    """)
                    dashboard['summary']['feishu_messages_24h'] = cursor.fetchone()[0]
            
            output_file = self.output_dir / "dashboard.json"
            with open(output_file, 'w') as f:
                json.dump(dashboard, f, indent=2, default=str)
            
            print(f"✅ 生成仪表盘数据")
            return True
        except Exception as e:
            print(f"❌ 生成仪表盘失败: {e}")
            return False
    
    def sync_all(self):
        """同步所有数据"""
        print("🔄 RDS 到 GitHub 数据同步")
        print("=" * 50)
        
        results = []
        results.append(self.export_system_metrics(days=7))
        results.append(self.export_tasks())
        results.append(self.export_email_stats(days=30))
        results.append(self.generate_dashboard_data())
        
        print("\n" + "=" * 50)
        print(f"✅ 完成 {sum(results)}/{len(results)} 项导出")
        
        return all(results)


def main():
    """命令行工具"""
    import sys
    
    sync = RDSGitHubSync()
    
    if len(sys.argv) < 2:
        print("🔄 RDS 到 GitHub 数据同步")
        print("\n用法:")
        print("  python3 rds_github_sync.py all          # 同步所有")
        print("  python3 rds_github_sync.py metrics      # 同步监控指标")
        print("  python3 rds_github_sync.py tasks        # 同步任务")
        print("  python3 rds_github_sync.py emails       # 同步邮件统计")
        print("  python3 rds_github_sync.py dashboard    # 生成仪表盘")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'all':
        sync.sync_all()
    elif cmd == 'metrics':
        sync.export_system_metrics()
    elif cmd == 'tasks':
        sync.export_tasks()
    elif cmd == 'emails':
        sync.export_email_stats()
    elif cmd == 'dashboard':
        sync.generate_dashboard_data()
    else:
        print(f"❌ 未知命令: {cmd}")


if __name__ == '__main__':
    main()