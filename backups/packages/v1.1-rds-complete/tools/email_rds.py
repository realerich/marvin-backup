#!/usr/bin/env python3
"""
邮件归档RDS工具
存储邮件、分类管理、全文搜索
"""

import json
from datetime import datetime
from rds_manager import RDSManager

class EmailArchiveRDS:
    """邮件归档管理"""
    
    def __init__(self):
        self.rds = RDSManager()
    
    def archive_email(self, email_data, category='normal'):
        """归档单封邮件"""
        sql = """
        INSERT INTO emails 
        (message_id, subject, sender, sender_name, received_at, category, 
         is_read, body_summary, full_content, labels)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        category=VALUES(category), is_read=VALUES(is_read), updated_at=NOW()
        """
        
        # 提取发件人名称
        sender = email_data.get('from', '')
        sender_name = ''
        if '<' in sender:
            sender_name = sender.split('<')[0].strip().strip('"')
            sender = sender.split('<')[1].strip('>')
        
        # 解析日期
        received_at = email_data.get('date')
        try:
            from email.utils import parsedate_to_datetime
            received_at = parsedate_to_datetime(received_at)
        except:
            received_at = datetime.now()
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    email_data.get('id'),
                    email_data.get('subject', '')[:500],
                    sender[:250],
                    sender_name[:250],
                    received_at,
                    category,
                    email_data.get('is_read', False),
                    email_data.get('body', '')[:500],
                    email_data.get('body', ''),
                    json.dumps(email_data.get('labels', []))
                ))
                conn.commit()
        
        return True
    
    def batch_archive(self, emails, category_map=None):
        """批量归档"""
        category_map = category_map or {}
        archived = 0
        
        for email in emails:
            category = category_map.get(email.get('id'), 'normal')
            try:
                self.archive_email(email, category)
                archived += 1
            except Exception as e:
                print(f"⚠️ 归档失败 {email.get('id')}: {e}")
        
        return f"✅ 已归档 {archived} 封邮件"
    
    def search_emails(self, keyword=None, category=None, sender=None, days=30, limit=50):
        """搜索邮件"""
        conditions = ["received_at > DATE_SUB(NOW(), INTERVAL %s DAY)"]
        params = [days]
        
        if keyword:
            conditions.append("(subject LIKE %s OR body_summary LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        if category:
            conditions.append("category = %s")
            params.append(category)
        
        if sender:
            conditions.append("sender LIKE %s")
            params.append(f"%{sender}%")
        
        sql = f"""
        SELECT * FROM emails
        WHERE {' AND '.join(conditions)}
        ORDER BY received_at DESC
        LIMIT %s
        """
        params.append(limit)
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()
    
    def get_unread_summary(self, days=7):
        """获取未读摘要"""
        sql = """
        SELECT 
            category,
            COUNT(*) as count
        FROM emails
        WHERE is_read = FALSE 
        AND received_at > DATE_SUB(NOW(), INTERVAL %s DAY)
        GROUP BY category
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (days,))
                return cursor.fetchall()
    
    def mark_as_read(self, message_ids):
        """标记为已读"""
        if not isinstance(message_ids, list):
            message_ids = [message_ids]
        
        placeholders = ','.join(['%s'] * len(message_ids))
        sql = f"UPDATE emails SET is_read = TRUE WHERE message_id IN ({placeholders})"
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, message_ids)
                conn.commit()
                return cursor.rowcount
    
    def get_stats(self):
        """获取邮件统计"""
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                # 总数
                cursor.execute("SELECT COUNT(*) as total FROM emails")
                total = cursor.fetchone()['total']
                
                # 未读数
                cursor.execute("SELECT COUNT(*) as unread FROM emails WHERE is_read = FALSE")
                unread = cursor.fetchone()['unread']
                
                # 按分类统计
                cursor.execute("SELECT category, COUNT(*) as count FROM emails GROUP BY category")
                by_category = cursor.fetchall()
                
                # 今日新增
                cursor.execute("SELECT COUNT(*) as today FROM emails WHERE DATE(received_at) = CURDATE()")
                today = cursor.fetchone()['today']
                
                return {
                    'total': total,
                    'unread': unread,
                    'today': today,
                    'by_category': by_category
                }
    
    def cleanup_old_promo(self, days=30):
        """清理旧营销邮件"""
        sql = """
        DELETE FROM emails 
        WHERE category = 'promo' 
        AND received_at < DATE_SUB(NOW(), INTERVAL %s DAY)
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (days,))
                deleted = cursor.rowcount
                conn.commit()
        
        return f"✅ 已清理 {deleted} 封旧营销邮件"


def main():
    import sys
    
    tool = EmailArchiveRDS()
    
    if len(sys.argv) < 2:
        print("📧 邮件归档RDS工具")
        print("\n用法:")
        print("  python3 email_rds.py stats                    # 邮件统计")
        print("  python3 email_rds.py search <关键词>          # 搜索邮件")
        print("  python3 email_rds.py unread                   # 未读摘要")
        print("  python3 email_rds.py cleanup [天数]           # 清理旧营销邮件")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'stats':
        stats = tool.get_stats()
        print("📊 邮件统计")
        print("=" * 40)
        print(f"总数量: {stats['total']}")
        print(f"未读: {stats['unread']}")
        print(f"今日新增: {stats['today']}")
        print("\n按分类:")
        for c in stats['by_category']:
            print(f"  {c['category']}: {c['count']}")
    
    elif cmd == 'search':
        keyword = sys.argv[2] if len(sys.argv) > 2 else None
        results = tool.search_emails(keyword=keyword)
        print(f"找到 {len(results)} 封邮件:")
        for e in results[:10]:
            print(f"  [{e['category']}] {e['subject'][:50]} - {e['sender'][:30]}")
    
    elif cmd == 'unread':
        summary = tool.get_unread_summary()
        print("📬 未读邮件摘要:")
        for s in summary:
            print(f"  {s['category']}: {s['count']}")
    
    elif cmd == 'cleanup':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 30
        result = tool.cleanup_old_promo(days)
        print(result)
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
