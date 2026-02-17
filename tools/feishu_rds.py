#!/usr/bin/env python3
"""
飞书消息 RDS 同步工具
将飞书消息存储到 RDS，实现对话历史可追溯
"""

import json
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))
from rds_manager import RDSManager


class FeishuMessageRDS:
    """飞书消息 RDS 存储"""
    
    def __init__(self):
        self.rds = RDSManager()
    
    def save_message(self, message_id, sender_id, sender_name, chat_type, 
                     chat_id, content, content_type='text', processed=False, 
                     processed_action=None):
        """保存飞书消息到 RDS"""
        try:
            with self.rds.get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                    INSERT INTO feishu_messages 
                    (message_id, sender_id, sender_name, chat_type, chat_id, 
                     content, content_type, is_processed, processed_action, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (message_id) DO NOTHING
                    """
                    cursor.execute(sql, (
                        message_id, sender_id, sender_name, chat_type, chat_id,
                        content, content_type, processed, processed_action, 
                        datetime.now()
                    ))
                    conn.commit()
                    return True
        except Exception as e:
            print(f"❌ 保存消息失败: {e}")
            return False
    
    def mark_processed(self, message_id, action='processed'):
        """标记消息已处理"""
        try:
            with self.rds.get_connection() as conn:
                with conn.cursor() as cursor:
                    sql = """
                    UPDATE feishu_messages 
                    SET is_processed = TRUE, processed_action = %s, processed_at = %s
                    WHERE message_id = %s
                    """
                    cursor.execute(sql, (action, datetime.now(), message_id))
                    conn.commit()
                    return True
        except Exception as e:
            print(f"❌ 标记处理失败: {e}")
            return False
    
    def search_messages(self, keyword=None, sender_id=None, chat_id=None, 
                        limit=50, offset=0):
        """搜索消息历史"""
        try:
            with self.rds.get_connection() as conn:
                with conn.cursor() as cursor:
                    conditions = []
                    params = []
                    
                    if keyword:
                        conditions.append("content ILIKE %s")
                        params.append(f"%{keyword}%")
                    if sender_id:
                        conditions.append("sender_id = %s")
                        params.append(sender_id)
                    if chat_id:
                        conditions.append("chat_id = %s")
                        params.append(chat_id)
                    
                    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
                    
                    sql = f"""
                    SELECT * FROM feishu_messages
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT %s OFFSET %s
                    """
                    params.extend([limit, offset])
                    
                    cursor.execute(sql, params)
                    return cursor.fetchall()
        except Exception as e:
            print(f"❌ 搜索失败: {e}")
            return []
    
    def get_stats(self):
        """获取消息统计"""
        try:
            with self.rds.get_connection() as conn:
                with conn.cursor() as cursor:
                    # 总消息数
                    cursor.execute("SELECT COUNT(*) FROM feishu_messages")
                    total = cursor.fetchone()[0]
                    
                    # 今日消息数
                    cursor.execute("""
                        SELECT COUNT(*) FROM feishu_messages 
                        WHERE DATE(created_at) = CURRENT_DATE
                    """)
                    today = cursor.fetchone()[0]
                    
                    # 未处理消息数
                    cursor.execute("""
                        SELECT COUNT(*) FROM feishu_messages 
                        WHERE is_processed = FALSE
                    """)
                    unprocessed = cursor.fetchone()[0]
                    
                    # 发件人统计
                    cursor.execute("""
                        SELECT sender_name, COUNT(*) as count 
                        FROM feishu_messages 
                        GROUP BY sender_name 
                        ORDER BY count DESC 
                        LIMIT 10
                    """)
                    top_senders = cursor.fetchall()
                    
                    return {
                        'total': total,
                        'today': today,
                        'unprocessed': unprocessed,
                        'top_senders': top_senders
                    }
        except Exception as e:
            print(f"❌ 获取统计失败: {e}")
            return {}
    
    def get_conversation_context(self, chat_id, limit=10):
        """获取对话上下文"""
        return self.search_messages(chat_id=chat_id, limit=limit)


def main():
    """命令行工具"""
    import sys
    
    tool = FeishuMessageRDS()
    
    if len(sys.argv) < 2:
        print("📱 飞书消息 RDS 同步工具")
        print("\n用法:")
        print("  python3 feishu_rds.py stats           # 查看统计")
        print("  python3 feishu_rds.py search [关键词]  # 搜索消息")
        print("  python3 feishu_rds.py context [chat_id] # 获取对话上下文")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'stats':
        stats = tool.get_stats()
        print("📊 飞书消息统计")
        print("=" * 40)
        print(f"总消息数: {stats.get('total', 0)}")
        print(f"今日消息: {stats.get('today', 0)}")
        print(f"未处理: {stats.get('unprocessed', 0)}")
        
        if stats.get('top_senders'):
            print("\n活跃发件人:")
            for sender in stats['top_senders']:
                print(f"  {sender[0]}: {sender[1]} 条")
    
    elif cmd == 'search':
        keyword = sys.argv[2] if len(sys.argv) > 2 else None
        results = tool.search_messages(keyword=keyword, limit=20)
        print(f"🔍 搜索结果 ({len(results)} 条)")
        print("=" * 40)
        for msg in results:
            print(f"\n[{msg[9]}] {msg[3]}")
            print(f"  {msg[6][:100]}...")
    
    elif cmd == 'context':
        chat_id = sys.argv[2] if len(sys.argv) > 2 else None
        if not chat_id:
            print("❌ 请提供 chat_id")
            sys.exit(1)
        results = tool.get_conversation_context(chat_id)
        print(f"💬 对话上下文 ({len(results)} 条)")
        print("=" * 40)
        for msg in reversed(results):
            print(f"\n[{msg[9]}] {msg[3]}: {msg[6][:80]}...")


if __name__ == '__main__':
    main()