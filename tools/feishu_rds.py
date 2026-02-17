#!/usr/bin/env python3
"""
飞书消息 RDS 同步工具 - 健壮版
解决RDS连接不稳定问题
"""

import json
import sys
from pathlib import Path
from datetime import datetime
import logging

sys.path.insert(0, str(Path(__file__).parent))
from rds_pool import RobustRDSManager, get_pool

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('feishu_rds')


class FeishuMessageRDS:
    """飞书消息 RDS 存储 - 健壮版"""
    
    def __init__(self):
        self.manager = RobustRDSManager()
        # 初始化时测试连接
        self._ensure_table_exists()
    
    def _ensure_table_exists(self):
        """确保表存在"""
        try:
            sql = """
            CREATE TABLE IF NOT EXISTS feishu_messages (
                id SERIAL PRIMARY KEY,
                message_id VARCHAR(100) UNIQUE,
                sender_id VARCHAR(100),
                sender_name VARCHAR(100),
                chat_type VARCHAR(20),
                chat_id VARCHAR(100),
                content TEXT,
                content_type VARCHAR(20) DEFAULT 'text',
                is_processed BOOLEAN DEFAULT FALSE,
                processed_action VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_feishu_sender ON feishu_messages(sender_id);
            CREATE INDEX IF NOT EXISTS idx_feishu_chat ON feishu_messages(chat_id);
            CREATE INDEX IF NOT EXISTS idx_feishu_created ON feishu_messages(created_at);
            CREATE INDEX IF NOT EXISTS idx_feishu_processed ON feishu_messages(is_processed);
            """
            
            with self.manager.pool.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql)
                    conn.commit()
                    logger.info("✅ feishu_messages 表已就绪")
        except Exception as e:
            logger.error(f"❌ 创建表失败: {e}")
            raise
    
    def save_message(self, message_id, sender_id, sender_name, chat_type, 
                     chat_id, content, content_type='text', processed=False, 
                     processed_action=None) -> bool:
        """保存飞书消息到 RDS - 带重试"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                with self.manager.pool.get_connection() as conn:
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
                        logger.info(f"✅ 消息已保存: {message_id[:20]}...")
                        return True
                        
            except Exception as e:
                logger.warning(f"保存尝试 {attempt+1}/{max_retries} 失败: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)  # 短暂延迟后重试
                else:
                    logger.error(f"❌ 保存消息最终失败: {e}")
                    return False
        
        return False
    
    def mark_processed(self, message_id, action='processed') -> bool:
        """标记消息已处理 - 带重试"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                with self.manager.pool.get_connection() as conn:
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
                logger.warning(f"标记处理 {attempt+1}/{max_retries} 失败: {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(1)
                else:
                    logger.error(f"❌ 标记处理最终失败: {e}")
                    return False
        
        return False
    
    def search_messages(self, keyword=None, sender_id=None, chat_id=None, 
                        limit=50, offset=0) -> list:
        """搜索消息历史 - 带容错"""
        try:
            with self.manager.pool.get_connection() as conn:
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
                    columns = [desc[0] for desc in cursor.description]
                    rows = cursor.fetchall()
                    
                    # 转换为字典列表
                    return [dict(zip(columns, row)) for row in rows]
                    
        except Exception as e:
            logger.error(f"❌ 搜索失败: {e}")
            return []
    
    def get_stats(self) -> dict:
        """获取消息统计 - 带容错"""
        try:
            with self.manager.pool.get_connection() as conn:
                with conn.cursor() as cursor:
                    stats = {}
                    
                    # 总消息数
                    cursor.execute("SELECT COUNT(*) FROM feishu_messages")
                    stats['total'] = cursor.fetchone()[0]
                    
                    # 今日消息数
                    cursor.execute("""
                        SELECT COUNT(*) FROM feishu_messages 
                        WHERE DATE(created_at) = CURRENT_DATE
                    """)
                    stats['today'] = cursor.fetchone()[0]
                    
                    # 未处理消息数
                    cursor.execute("""
                        SELECT COUNT(*) FROM feishu_messages 
                        WHERE is_processed = FALSE
                    """)
                    stats['unprocessed'] = cursor.fetchone()[0]
                    
                    # 发件人统计
                    cursor.execute("""
                        SELECT sender_name, COUNT(*) as count 
                        FROM feishu_messages 
                        GROUP BY sender_name 
                        ORDER BY count DESC 
                        LIMIT 10
                    """)
                    stats['top_senders'] = cursor.fetchall()
                    
                    return stats
                    
        except Exception as e:
            logger.error(f"❌ 获取统计失败: {e}")
            return {'error': str(e)}
    
    def get_conversation_context(self, chat_id, limit=10) -> list:
        """获取对话上下文"""
        return self.search_messages(chat_id=chat_id, limit=limit)
    
    def save_current_conversation(self, conversation_data: dict) -> bool:
        """保存当前对话到 RDS
        
        conversation_data 格式:
        {
            'message_id': '...',
            'sender_id': 'ou_...',
            'sender_name': '大王',
            'chat_type': 'direct',
            'chat_id': '...',
            'content': '消息内容',
            'content_type': 'text'
        }
        """
        try:
            return self.save_message(
                message_id=conversation_data.get('message_id'),
                sender_id=conversation_data.get('sender_id'),
                sender_name=conversation_data.get('sender_name'),
                chat_type=conversation_data.get('chat_type'),
                chat_id=conversation_data.get('chat_id'),
                content=conversation_data.get('content'),
                content_type=conversation_data.get('content_type', 'text'),
                processed=False
            )
        except Exception as e:
            logger.error(f"❌ 保存对话失败: {e}")
            return False


def main():
    """命令行工具"""
    import sys
    
    tool = FeishuMessageRDS()
    
    if len(sys.argv) < 2:
        print("📱 飞书消息 RDS 同步工具 (健壮版)")
        print("\n用法:")
        print("  python3 feishu_rds.py stats           # 查看统计")
        print("  python3 feishu_rds.py search [关键词]  # 搜索消息")
        print("  python3 feishu_rds.py test            # 连接测试")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'stats':
        stats = tool.get_stats()
        if 'error' in stats:
            print(f"❌ 获取统计失败: {stats['error']}")
            sys.exit(1)
            
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
            print(f"\n[{msg['created_at']}] {msg['sender_name']}")
            print(f"  {msg['content'][:100]}...")
    
    elif cmd == 'test':
        print("🧪 测试 RDS 连接...")
        health = tool.manager.health.check_health()
        print(json.dumps(health, indent=2, default=str))
    
    else:
        print(f"❌ 未知命令: {cmd}")


if __name__ == '__main__':
    main()