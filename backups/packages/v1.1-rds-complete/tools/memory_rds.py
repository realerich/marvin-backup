#!/usr/bin/env python3
"""
记忆系统RDS工具
替代本地文件存储，支持SQL查询
"""

import json
from datetime import datetime
from rds_manager import RDSManager

class MemoryRDS:
    """记忆RDS管理"""
    
    def __init__(self):
        self.rds = RDSManager()
    
    def add_memory(self, content, category='general', session_key=None, importance=0.5, source=None):
        """添加记忆"""
        # 提取关键词（简单实现）
        keywords = self._extract_keywords(content)
        
        sql = """
        INSERT INTO memories 
        (session_key, memory_type, category, content, keywords, importance_score, source)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    session_key,
                    'long_term' if importance > 0.7 else 'short_term',
                    category,
                    content,
                    json.dumps(keywords),
                    importance,
                    source
                ))
                conn.commit()
                return cursor.lastrowid
    
    def _extract_keywords(self, content, max_keywords=5):
        """简单关键词提取"""
        import re
        # 提取中文和英文单词
        words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', content.lower())
        # 简单的频率统计
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
        # 返回最常见的词
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [w[0] for w in sorted_words[:max_keywords]]
    
    def search_memories(self, keyword=None, category=None, memory_type=None, 
                       min_importance=None, limit=20):
        """搜索记忆"""
        conditions = ["1=1"]
        params = []
        
        if keyword:
            conditions.append("(content LIKE %s OR keywords LIKE %s)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])
        
        if category:
            conditions.append("category = %s")
            params.append(category)
        
        if memory_type:
            conditions.append("memory_type = %s")
            params.append(memory_type)
        
        if min_importance:
            conditions.append("importance_score >= %s")
            params.append(min_importance)
        
        sql = f"""
        SELECT * FROM memories
        WHERE {' AND '.join(conditions)}
        ORDER BY importance_score DESC, created_at DESC
        LIMIT %s
        """
        params.append(limit)
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                results = cursor.fetchall()
                
                # 更新访问次数和时间
                for r in results:
                    self._update_access(r['id'])
                
                return results
    
    def _update_access(self, memory_id):
        """更新访问统计"""
        sql = """
        UPDATE memories 
        SET last_accessed = NOW(), access_count = access_count + 1
        WHERE id = %s
        """
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (memory_id,))
                conn.commit()
    
    def get_recent_memories(self, hours=24, limit=50):
        """获取最近记忆"""
        sql = """
        SELECT * FROM memories
        WHERE created_at > DATE_SUB(NOW(), INTERVAL %s HOUR)
        ORDER BY created_at DESC
        LIMIT %s
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (hours, limit))
                return cursor.fetchall()
    
    def get_popular_memories(self, limit=20):
        """获取最常访问的记忆"""
        sql = """
        SELECT * FROM memories
        ORDER BY access_count DESC, last_accessed DESC
        LIMIT %s
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (limit,))
                return cursor.fetchall()
    
    def update_importance(self, memory_id, importance):
        """更新重要性分数"""
        sql = "UPDATE memories SET importance_score = %s WHERE id = %s"
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (importance, memory_id))
                conn.commit()
                return cursor.rowcount > 0
    
    def delete_memory(self, memory_id):
        """删除记忆"""
        sql = "DELETE FROM memories WHERE id = %s"
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (memory_id,))
                conn.commit()
                return cursor.rowcount > 0
    
    def get_stats(self):
        """获取记忆统计"""
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                # 总数
                cursor.execute("SELECT COUNT(*) as total FROM memories")
                total = cursor.fetchone()['total']
                
                # 按类型统计
                cursor.execute("SELECT memory_type, COUNT(*) as count FROM memories GROUP BY memory_type")
                by_type = cursor.fetchall()
                
                # 按分类统计
                cursor.execute("SELECT category, COUNT(*) as count FROM memories GROUP BY category")
                by_category = cursor.fetchall()
                
                # 今日新增
                cursor.execute("SELECT COUNT(*) as today FROM memories WHERE DATE(created_at) = CURDATE()")
                today = cursor.fetchone()['today']
                
                # 平均重要性
                cursor.execute("SELECT AVG(importance_score) as avg_importance FROM memories")
                avg_importance = cursor.fetchone()['avg_importance']
                
                return {
                    'total': total,
                    'today': today,
                    'by_type': by_type,
                    'by_category': by_category,
                    'avg_importance': round(avg_importance, 2) if avg_importance else 0
                }
    
    def cleanup_old_short_term(self, days=7):
        """清理旧的短期记忆"""
        sql = """
        DELETE FROM memories 
        WHERE memory_type = 'short_term' 
        AND importance_score < 0.5
        AND created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
        AND access_count < 3
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (days,))
                deleted = cursor.rowcount
                conn.commit()
        
        return f"✅ 已清理 {deleted} 条旧短期记忆"
    
    def format_memory(self, memory):
        """格式化单条记忆"""
        msg = f"📝 #{memory['id']} [{memory['category']}]\n"
        msg += f"   {memory['content'][:100]}...\n"
        msg += f"   ⭐ {memory['importance_score']}  👁️ {memory['access_count']}  📅 {memory['created_at']}\n"
        return msg


def main():
    import sys
    
    tool = MemoryRDS()
    
    if len(sys.argv) < 2:
        print("🧠 记忆系统RDS工具")
        print("\n用法:")
        print("  python3 memory_rds.py add '<内容>' [分类] [重要性]   # 添加记忆")
        print("  python3 memory_rds.py search <关键词>                 # 搜索记忆")
        print("  python3 memory_rds.py recent [小时]                   # 最近记忆")
        print("  python3 memory_rds.py popular                         # 热门记忆")
        print("  python3 memory_rds.py stats                           # 统计信息")
        print("  python3 memory_rds.py cleanup [天数]                  # 清理旧记忆")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'add':
        content = sys.argv[2]
        category = sys.argv[3] if len(sys.argv) > 3 else 'general'
        importance = float(sys.argv[4]) if len(sys.argv) > 4 else 0.5
        memory_id = tool.add_memory(content, category, importance=importance)
        print(f"✅ 记忆已添加 (ID: {memory_id})")
    
    elif cmd == 'search':
        keyword = sys.argv[2]
        results = tool.search_memories(keyword=keyword)
        print(f"找到 {len(results)} 条记忆:")
        for m in results[:5]:
            print(tool.format_memory(m))
    
    elif cmd == 'recent':
        hours = int(sys.argv[2]) if len(sys.argv) > 2 else 24
        results = tool.get_recent_memories(hours)
        print(f"最近{hours}小时的 {len(results)} 条记忆:")
        for m in results[:5]:
            print(tool.format_memory(m))
    
    elif cmd == 'popular':
        results = tool.get_popular_memories()
        print("热门记忆:")
        for m in results[:5]:
            print(tool.format_memory(m))
    
    elif cmd == 'stats':
        stats = tool.get_stats()
        print("📊 记忆统计")
        print("=" * 40)
        print(f"总数量: {stats['total']}")
        print(f"今日新增: {stats['today']}")
        print(f"平均重要性: {stats['avg_importance']}")
        print("\n按类型:")
        for t in stats['by_type']:
            print(f"  {t['memory_type']}: {t['count']}")
        print("\n按分类:")
        for c in stats['by_category']:
            print(f"  {c['category']}: {c['count']}")
    
    elif cmd == 'cleanup':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        result = tool.cleanup_old_short_term(days)
        print(result)
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
