#!/usr/bin/env python3
"""
Marvin 数据基础设施
PostgreSQL 连接和操作封装
"""

import psycopg2
import psycopg2.extras
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# 数据库配置 - 从环境变量读取，支持GitHub Secrets
import os

DB_CONFIG = {
    "host": os.environ.get("RDS_HOST", "pgm-j6c0rrysy447d8tc.pg.rds.aliyuncs.com"),
    "port": os.environ.get("RDS_PORT", "5432"),
    "dbname": os.environ.get("RDS_DB", "marvin_db"),
    "user": os.environ.get("RDS_USER", "marvin"),
    "password": os.environ.get("RDS_PASSWORD", ""),
}

# 本地备份配置（紧急情况使用）
DB_CONFIG_LOCAL = {
    "host": "localhost",
    "port": "5432",
    "dbname": "marvin_db",
    "user": "marvin",
    "password": "marvin_2026",
}

class MarvinDB:
    def __init__(self):
        self.conn = None
        self.connect()
    
    def connect(self):
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            print("[DB] 数据库连接成功")
        except Exception as e:
            print(f"[DB] 连接失败: {e}")
    
    def get_active_persons(self, priority: Optional[str] = None) -> List[Dict]:
        """获取活跃监测人员"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        if priority:
            cursor.execute(
                "SELECT * FROM persons WHERE status = 'active' AND priority = %s ORDER BY priority, name",
                (priority,)
            )
        else:
            cursor.execute("SELECT * FROM persons WHERE status = 'active' ORDER BY priority, name")
        
        return cursor.fetchall()
    
    def add_activity(self, person_id: int, platform: str, content_original: str,
                     content_summary: str, url: str, category: str, 
                     importance: str, sentiment: str, published_at: datetime) -> int:
        """添加动态记录"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO activities (person_id, platform, content_original, content_summary,
                                   url, category, importance, sentiment, published_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (person_id, platform, content_original, content_summary, url,
              category, importance, sentiment, published_at))
        
        activity_id = cursor.fetchone()[0]
        self.conn.commit()
        
        # 更新人员最后活跃时间
        cursor.execute(
            "UPDATE persons SET last_active = %s WHERE id = %s",
            (datetime.now(), person_id)
        )
        self.conn.commit()
        
        return activity_id
    
    def get_recent_activities(self, hours: int = 24) -> List[Dict]:
        """获取最近N小时的动态"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        since = datetime.now() - timedelta(hours=hours)
        
        cursor.execute("""
            SELECT a.*, p.name, p.company 
            FROM activities a
            JOIN persons p ON a.person_id = p.id
            WHERE a.created_at > %s
            ORDER BY a.importance DESC, a.created_at DESC
        """, (since,))
        
        return cursor.fetchall()
    
    def get_weekly_stats(self, start_date: datetime, end_date: datetime) -> Dict:
        """获取周报统计数据"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # 总动态数
        cursor.execute("""
            SELECT COUNT(*) as count FROM activities 
            WHERE published_at BETWEEN %s AND %s
        """, (start_date, end_date))
        total = cursor.fetchone()['count']
        
        # 按平台统计
        cursor.execute("""
            SELECT platform, COUNT(*) as count 
            FROM activities 
            WHERE published_at BETWEEN %s AND %s
            GROUP BY platform
        """, (start_date, end_date))
        by_platform = {row['platform']: row['count'] for row in cursor.fetchall()}
        
        # 按重要性统计
        cursor.execute("""
            SELECT importance, COUNT(*) as count 
            FROM activities 
            WHERE published_at BETWEEN %s AND %s
            GROUP BY importance
        """, (start_date, end_date))
        by_importance = {row['importance']: row['count'] for row in cursor.fetchall()}
        
        # 高重要性动态详情
        cursor.execute("""
            SELECT a.*, p.name, p.company 
            FROM activities a
            JOIN persons p ON a.person_id = p.id
            WHERE a.published_at BETWEEN %s AND %s
            AND a.importance = '高'
            ORDER BY a.published_at DESC
            LIMIT 10
        """, (start_date, end_date))
        key_events = cursor.fetchall()
        
        return {
            "total": total,
            "by_platform": by_platform,
            "by_importance": by_importance,
            "key_events": key_events
        }
    
    def add_weekly_report(self, week_number: str, start_date: datetime, 
                         end_date: datetime, stats: Dict, report: str):
        """添加周报"""
        cursor = self.conn.cursor()
        
        key_events_text = "\n".join([
            f"- {e['name']} ({e['company']}): {e['content_summary']}"
            for e in stats['key_events']
        ])
        
        cursor.execute("""
            INSERT INTO weekly_reports (week_number, start_date, end_date, 
                                       activity_count, key_events, full_report)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (week_number, start_date, end_date, stats['total'], 
              key_events_text, report))
        
        self.conn.commit()
    
    def log_adjustment(self, person_id: int, action_type: str, reason: str,
                       trigger_by: str, details: str = ""):
        """记录名单调整"""
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO adjustment_logs (person_id, action_type, reason, trigger_by, details)
            VALUES (%s, %s, %s, %s, %s)
        """, (person_id, action_type, reason, trigger_by, details))
        self.conn.commit()
    
    def execute_sql(self, sql: str, params=None) -> List[Dict]:
        """执行自定义SQL查询"""
        cursor = self.conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(sql, params or ())
        return cursor.fetchall()
    
    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()

if __name__ == "__main__":
    # 测试数据库连接
    db = MarvinDB()
    
    print("\n[测试] 获取活跃人员:")
    persons = db.get_active_persons()
    print(f"  共 {len(persons)} 人")
    for p in persons[:5]:
        print(f"  - {p['name']} ({p['company']}) [{p['priority']}]")
    
    print("\n[测试] 查询表结构:")
    tables = db.execute_sql("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)
    for t in tables:
        print(f"  - {t['table_name']}")
    
    db.close()
    print("\n[DB] 测试完成")
