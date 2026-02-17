#!/usr/bin/env python3
"""
Webhook日志RDS工具
记录所有webhook调用、性能分析
"""

import json
from datetime import datetime
from rds_manager import RDSManager

class WebhookLogRDS:
    """Webhook日志管理"""
    
    def __init__(self):
        self.rds = RDSManager()
    
    def log_webhook(self, webhook_id, webhook_name, action, payload, 
                   source_ip='127.0.0.1', status='pending', 
                   execution_time_ms=None, error_message=None, response_data=None):
        """记录webhook调用"""
        sql = """
        INSERT INTO webhook_logs 
        (webhook_id, webhook_name, action, payload, source_ip, 
         status, execution_time_ms, error_message, response_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    webhook_id,
                    webhook_name,
                    action,
                    json.dumps(payload) if payload else None,
                    source_ip,
                    status,
                    execution_time_ms,
                    error_message,
                    json.dumps(response_data) if response_data else None
                ))
                conn.commit()
                return cursor.lastrowid
    
    def update_status(self, log_id, status, execution_time_ms=None, 
                     error_message=None, response_data=None):
        """更新执行状态"""
        sql = """
        UPDATE webhook_logs 
        SET status = %s, execution_time_ms = %s, error_message = %s, response_data = %s
        WHERE id = %s
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    status,
                    execution_time_ms,
                    error_message,
                    json.dumps(response_data) if response_data else None,
                    log_id
                ))
                conn.commit()
                return cursor.rowcount > 0
    
    def get_recent_logs(self, hours=24, limit=100):
        """获取最近日志"""
        sql = """
        SELECT * FROM webhook_logs
        WHERE executed_at > DATE_SUB(NOW(), INTERVAL %s HOUR)
        ORDER BY executed_at DESC
        LIMIT %s
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (hours, limit))
                return cursor.fetchall()
    
    def get_stats(self, hours=24):
        """获取统计信息"""
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                # 总调用数
                cursor.execute("""
                    SELECT COUNT(*) as total 
                    FROM webhook_logs 
                    WHERE executed_at > DATE_SUB(NOW(), INTERVAL %s HOUR)
                """, (hours,))
                total = cursor.fetchone()['total']
                
                # 按状态统计
                cursor.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM webhook_logs 
                    WHERE executed_at > DATE_SUB(NOW(), INTERVAL %s HOUR)
                    GROUP BY status
                """, (hours,))
                by_status = cursor.fetchall()
                
                # 按webhook统计
                cursor.execute("""
                    SELECT webhook_name, COUNT(*) as count, 
                           AVG(execution_time_ms) as avg_time
                    FROM webhook_logs 
                    WHERE executed_at > DATE_SUB(NOW(), INTERVAL %s HOUR)
                    GROUP BY webhook_name
                    ORDER BY count DESC
                """, (hours,))
                by_webhook = cursor.fetchall()
                
                # 平均执行时间
                cursor.execute("""
                    SELECT AVG(execution_time_ms) as avg_time
                    FROM webhook_logs 
                    WHERE executed_at > DATE_SUB(NOW(), INTERVAL %s HOUR)
                    AND status = 'success'
                """, (hours,))
                avg_time = cursor.fetchone()['avg_time']
                
                # 失败记录
                cursor.execute("""
                    SELECT * FROM webhook_logs
                    WHERE status = 'failed'
                    AND executed_at > DATE_SUB(NOW(), INTERVAL %s HOUR)
                    ORDER BY executed_at DESC
                    LIMIT 10
                """, (hours,))
                failures = cursor.fetchall()
                
                return {
                    'total': total,
                    'by_status': by_status,
                    'by_webhook': by_webhook,
                    'avg_execution_time': round(avg_time, 2) if avg_time else 0,
                    'recent_failures': failures
                }
    
    def get_performance_issues(self, threshold_ms=5000, hours=24):
        """获取性能问题（执行时间过长）"""
        sql = """
        SELECT * FROM webhook_logs
        WHERE execution_time_ms > %s
        AND executed_at > DATE_SUB(NOW(), INTERVAL %s HOUR)
        ORDER BY execution_time_ms DESC
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (threshold_ms, hours))
                return cursor.fetchall()
    
    def cleanup_old_logs(self, days=30):
        """清理旧日志"""
        sql = "DELETE FROM webhook_logs WHERE executed_at < DATE_SUB(NOW(), INTERVAL %s DAY)"
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (days,))
                deleted = cursor.rowcount
                conn.commit()
        
        return f"✅ 已清理 {deleted} 条旧日志"


def main():
    import sys
    
    tool = WebhookLogRDS()
    
    if len(sys.argv) < 2:
        print("🔗 Webhook日志RDS工具")
        print("\n用法:")
        print("  python3 webhook_rds.py stats [小时]       # 统计信息")
        print("  python3 webhook_rds.py recent [小时]      # 最近日志")
        print("  python3 webhook_rds.py slow [阈值ms]      # 慢请求")
        print("  python3 webhook_rds.py cleanup [天数]     # 清理旧日志")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'stats':
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        stats = tool.get_stats(hours)
        print(f"📊 Webhook统计 (最近{hours}小时)")
        print("=" * 50)
        print(f"总调用: {stats['total']}")
        print(f"平均执行时间: {stats['avg_execution_time']}ms")
        print("\n按状态:")
        for s in stats['by_status']:
            print(f"  {s['status']}: {s['count']}")
        print("\n按Webhook:")
        for w in stats['by_webhook'][:5]:
            print(f"  {w['webhook_name']}: {w['count']}次 (平均{w['avg_time']:.0f}ms)")
        if stats['recent_failures']:
            print(f"\n⚠️ 最近失败: {len(stats['recent_failures'])}次")
    
    elif cmd == 'recent':
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        logs = tool.get_recent_logs(hours, limit=20)
        print(f"最近 {len(logs)} 条日志:")
        for l in logs[:10]:
            status_emoji = "✅" if l['status'] == 'success' else "❌" if l['status'] == 'failed' else "⏳"
            print(f"  {status_emoji} {l['webhook_name']} | {l['action']} | {l['execution_time_ms']}ms")
    
    elif cmd == 'slow':
        threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
        logs = tool.get_performance_issues(threshold)
        print(f"⚠️ 发现 {len(logs)} 条慢请求(>{threshold}ms):")
        for l in logs:
            print(f"  {l['webhook_name']}: {l['execution_time_ms']}ms - {l['action']}")
    
    elif cmd == 'cleanup':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = tool.cleanup_old_logs(days)
        print(result)
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
