#!/usr/bin/env python3
"""
系统监控RDS工具 (PostgreSQL)
存储监控指标、生成趋势报告
"""

import json
from datetime import datetime, timedelta
from rds_manager import RDSManager

class SystemMetricsRDS:
    """系统指标RDS管理"""
    
    def __init__(self):
        self.rds = RDSManager()
    
    def save_metrics(self, stats, hostname='localhost'):
        """保存系统指标"""
        sql = """
        INSERT INTO system_metrics 
        (hostname, cpu_percent, cpu_count, memory_total_gb, memory_used_gb, 
         memory_percent, disk_total_gb, disk_used_gb, disk_percent,
         network_in_mb, network_out_mb, openclaw_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    hostname,
                    stats['cpu']['percent'],
                    stats['cpu']['count'],
                    stats['memory']['total'],
                    stats['memory']['used'],
                    stats['memory']['percent'],
                    stats['disk']['total'],
                    stats['disk']['used'],
                    stats['disk']['percent'],
                    stats['network']['bytes_recv'],
                    stats['network']['bytes_sent'],
                    'running'
                ))
                conn.commit()
        
        return True
    
    def get_recent_metrics(self, hours=24, hostname='localhost'):
        """获取最近指标"""
        sql = """
        SELECT * FROM system_metrics 
        WHERE hostname = %s AND timestamp > NOW() - INTERVAL '%s hours'
        ORDER BY timestamp DESC
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (hostname, hours))
                return cursor.fetchall()
    
    def get_hourly_avg(self, hours=24, hostname='localhost'):
        """获取每小时平均值"""
        sql = """
        SELECT 
            TO_CHAR(timestamp, 'YYYY-MM-DD HH24:00') as hour,
            AVG(cpu_percent) as avg_cpu,
            AVG(memory_percent) as avg_memory,
            AVG(disk_percent) as avg_disk,
            MAX(cpu_percent) as max_cpu,
            MAX(memory_percent) as max_memory
        FROM system_metrics
        WHERE hostname = %s AND timestamp > NOW() - INTERVAL '%s hours'
        GROUP BY TO_CHAR(timestamp, 'YYYY-MM-DD HH24:00')
        ORDER BY hour
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (hostname, hours))
                return cursor.fetchall()
    
    def get_daily_summary(self, days=7, hostname='localhost'):
        """获取每日汇总"""
        sql = """
        SELECT 
            DATE(timestamp) as date,
            AVG(cpu_percent) as avg_cpu,
            AVG(memory_percent) as avg_memory,
            AVG(disk_percent) as avg_disk,
            MAX(cpu_percent) as max_cpu,
            MAX(memory_percent) as max_memory,
            COUNT(*) as sample_count
        FROM system_metrics
        WHERE hostname = %s AND timestamp > NOW() - INTERVAL '%s days'
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (hostname, days))
                return cursor.fetchall()
    
    def get_alerts(self, hostname='localhost'):
        """获取报警记录（高资源使用）"""
        sql = """
        SELECT * FROM system_metrics
        WHERE hostname = %s 
        AND (cpu_percent > 80 OR memory_percent > 85 OR disk_percent > 90)
        ORDER BY timestamp DESC
        LIMIT 50
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (hostname,))
                return cursor.fetchall()
    
    def cleanup_old_data(self, days=30):
        """清理旧数据"""
        sql = "DELETE FROM system_metrics WHERE timestamp < NOW() - INTERVAL '%s days'"
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (days,))
                deleted = cursor.rowcount
                conn.commit()
        
        return f"✅ 已清理 {deleted} 条旧记录"
    
    def format_trend_report(self, hourly_data):
        """格式化趋势报告"""
        if not hourly_data:
            return "📭 无数据"
        
        msg = "📊 系统资源趋势 (最近24小时)\n"
        msg += "=" * 50 + "\n\n"
        
        msg += f"{'时间':<16} {'CPU':<8} {'内存':<8} {'磁盘':<8}\n"
        msg += "-" * 50 + "\n"
        
        # hourly_data is list of tuples: (hour, avg_cpu, avg_memory, avg_disk, max_cpu, max_memory)
        for row in hourly_data[-12:]:
            msg += f"{row[0]:<16} {row[1]:<8.1f} {row[2]:<8.1f} {row[3]:<8.1f}\n"
        
        # 统计
        avg_cpu = sum(r[1] for r in hourly_data) / len(hourly_data)
        avg_mem = sum(r[2] for r in hourly_data) / len(hourly_data)
        max_cpu = max(r[4] for r in hourly_data)
        max_mem = max(r[5] for r in hourly_data)
        
        msg += "\n" + "=" * 50 + "\n"
        msg += f"平均CPU: {avg_cpu:.1f}%  最高CPU: {max_cpu:.1f}%\n"
        msg += f"平均内存: {avg_mem:.1f}%  最高内存: {max_mem:.1f}%\n"
        
        return msg


def main():
    import sys
    
    tool = SystemMetricsRDS()
    
    if len(sys.argv) < 2:
        print("📊 系统监控RDS工具")
        print("\n用法:")
        print("  python3 metrics_rds.py save           # 保存当前指标")
        print("  python3 metrics_rds.py trend [小时]   # 查看趋势")
        print("  python3 metrics_rds.py daily [天数]   # 每日汇总")
        print("  python3 metrics_rds.py alerts         # 查看报警")
        print("  python3 metrics_rds.py cleanup [天数] # 清理旧数据")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'save':
        import psutil
        stats = {
            'cpu': {'percent': psutil.cpu_percent(interval=1), 'count': psutil.cpu_count()},
            'memory': {
                'total': psutil.virtual_memory().total // (1024**3),
                'used': psutil.virtual_memory().used // (1024**3),
                'percent': psutil.virtual_memory().percent
            },
            'disk': {
                'total': psutil.disk_usage('/').total // (1024**3),
                'used': psutil.disk_usage('/').used // (1024**3),
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'bytes_recv': psutil.net_io_counters().bytes_recv // (1024**2),
                'bytes_sent': psutil.net_io_counters().bytes_sent // (1024**2)
            }
        }
        tool.save_metrics(stats)
        print("✅ 指标已保存到RDS")
    
    elif cmd == 'trend':
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        data = tool.get_hourly_avg(hours)
        print(tool.format_trend_report(data))
    
    elif cmd == 'daily':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        data = tool.get_daily_summary(days)
        print(f"最近{days}天汇总:")
        for d in data:
            print(f"  {d[0]}: CPU {d[1]:.1f}%, 内存 {d[2]:.1f}%")
    
    elif cmd == 'alerts':
        alerts = tool.get_alerts()
        if alerts:
            print(f"⚠️ 最近 {len(alerts)} 次资源报警:")
            for a in alerts[:10]:
                print(f"  {a[2]}: CPU {a[3]}%, 内存 {a[6]}%")
        else:
            print("✅ 无报警记录")
    
    elif cmd == 'cleanup':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = tool.cleanup_old_data(days)
        print(result)
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
