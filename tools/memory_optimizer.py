#!/usr/bin/env python3
"""
记忆层优化系统 - 关联记忆 + 自动摘要 + 混合检索
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import numpy as np

# 尝试导入现有工具
try:
    from rds_manager import RDSManager
    RDS_AVAILABLE = True
except:
    RDS_AVAILABLE = False

class MemoryOptimizer:
    """记忆优化器"""
    
    def __init__(self):
        if RDS_AVAILABLE:
            self.rds = RDSManager()
        self.workspace = Path("/root/.openclaw/workspace")
    
    def init_enhanced_tables(self):
        """初始化增强版记忆表"""
        if not RDS_AVAILABLE:
            print("❌ RDS不可用")
            return False
        
        sql_statements = [
            # 记忆关联表
            """
            CREATE TABLE IF NOT EXISTS memory_links (
                id SERIAL PRIMARY KEY,
                source_memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
                target_memory_id INTEGER REFERENCES memories(id) ON DELETE CASCADE,
                link_type VARCHAR(50) DEFAULT 'related',
                strength NUMERIC(3, 2) DEFAULT 0.5,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_memory_id, target_memory_id, link_type)
            );
            CREATE INDEX IF NOT EXISTS idx_memory_links_source ON memory_links(source_memory_id);
            CREATE INDEX IF NOT EXISTS idx_memory_links_target ON memory_links(target_memory_id);
            """,
            
            # 记忆摘要表
            """
            CREATE TABLE IF NOT EXISTS memory_summaries (
                id SERIAL PRIMARY KEY,
                summary_date DATE UNIQUE,
                content_summary TEXT,
                key_decisions JSONB,
                action_items JSONB,
                people_mentioned JSONB,
                topics JSONB,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """,
            
            # 记忆访问统计表（用于主动回忆）
            """
            CREATE TABLE IF NOT EXISTS memory_access_patterns (
                id SERIAL PRIMARY KEY,
                hour_of_day INTEGER,
                day_of_week INTEGER,
                category VARCHAR(50),
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP,
                UNIQUE(hour_of_day, day_of_week, category)
            );
            """,
            
            # 为memories表添加新字段
            """
            ALTER TABLE memories 
            ADD COLUMN IF NOT EXISTS tier INTEGER DEFAULT 2,
            ADD COLUMN IF NOT EXISTS decay_rate NUMERIC(3, 2) DEFAULT 0.1,
            ADD COLUMN IF NOT EXISTS summary TEXT,
            ADD COLUMN IF NOT EXISTS related_topics JSONB DEFAULT '[]'::jsonb;
            """,
            
            # 创建全文搜索索引（使用simple配置，适配PostgreSQL默认）
            """
            CREATE INDEX IF NOT EXISTS idx_memories_content_fts ON memories 
            USING gin(to_tsvector('simple', content));
            """
        ]
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                for sql in sql_statements:
                    try:
                        cursor.execute(sql)
                        conn.commit()
                    except Exception as e:
                        print(f"⚠️ 表可能已存在或错误: {e}")
                        conn.rollback()
        
        print("✅ 增强记忆表初始化完成")
        return True
    
    def create_memory_link(self, source_id: int, target_id: int, 
                          link_type: str = 'related', strength: float = 0.5):
        """创建记忆关联"""
        if not RDS_AVAILABLE:
            return False
        
        sql = """
        INSERT INTO memory_links (source_memory_id, target_memory_id, link_type, strength)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (source_memory_id, target_memory_id, link_type) DO UPDATE
        SET strength = EXCLUDED.strength
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (source_id, target_id, link_type, strength))
                conn.commit()
        return True
    
    def find_related_memories(self, memory_id: int, min_strength: float = 0.3):
        """查找关联记忆"""
        if not RDS_AVAILABLE:
            return []
        
        sql = """
        SELECT m.*, ml.link_type, ml.strength
        FROM memory_links ml
        JOIN memories m ON ml.target_memory_id = m.id
        WHERE ml.source_memory_id = %s AND ml.strength >= %s
        UNION
        SELECT m.*, ml.link_type, ml.strength
        FROM memory_links ml
        JOIN memories m ON ml.source_memory_id = m.id
        WHERE ml.target_memory_id = %s AND ml.strength >= %s
        ORDER BY strength DESC
        LIMIT 10
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (memory_id, min_strength, memory_id, min_strength))
                return cursor.fetchall()
    
    def auto_link_memories(self):
        """自动创建记忆关联"""
        if not RDS_AVAILABLE:
            return 0
        
        # 1. 获取近期记忆
        sql = """
        SELECT id, content, category, keywords, created_at
        FROM memories
        WHERE created_at > NOW() - INTERVAL '7 days'
        ORDER BY created_at DESC
        LIMIT 100
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql)
                memories = cursor.fetchall()
        
        links_created = 0
        
        # 2. 基于相似度创建关联
        for i, m1 in enumerate(memories):
            for m2 in memories[i+1:]:
                similarity = self._calculate_similarity(m1, m2)
                if similarity > 0.6:
                    link_type = self._determine_link_type(m1, m2)
                    if self.create_memory_link(m1[0], m2[0], link_type, similarity):
                        links_created += 1
        
        return links_created
    
    def _calculate_similarity(self, m1, m2):
        """计算两段记忆的相似度"""
        # 基于关键词重叠 + 时间接近度 + 类别相同
        score = 0.0
        
        # 类别相同 +0.3
        if m1[2] == m2[2]:  # category
            score += 0.3
        
        # 关键词重叠
        try:
            k1 = set(json.loads(m1[3]) if m1[3] else [])
            k2 = set(json.loads(m2[3]) if m2[3] else [])
            if k1 and k2:
                overlap = len(k1 & k2) / max(len(k1), len(k2))
                score += overlap * 0.4
        except:
            pass
        
        # 内容相似度（简单版本）
        c1, c2 = m1[1].lower(), m2[1].lower()
        common_words = set(c1.split()) & set(c2.split())
        if len(common_words) > 3:
            score += 0.2
        
        # 时间接近度（同一天+0.1）
        try:
            t1 = m1[4]
            t2 = m2[4]
            if abs((t1 - t2).days) <= 1:
                score += 0.1
        except:
            pass
        
        return min(score, 1.0)
    
    def _determine_link_type(self, m1, m2):
        """确定关联类型"""
        # 简单启发式规则
        if 'RDS' in m1[1] and 'RDS' in m2[1]:
            return 'same_topic'
        if m1[2] == m2[2]:
            return 'same_category'
        return 'related'
    
    def generate_daily_summary(self, date_str: str = None):
        """生成每日摘要"""
        if not RDS_AVAILABLE:
            return None
        
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 1. 获取当日记忆
        sql = """
        SELECT * FROM memories
        WHERE DATE(created_at) = %s
        ORDER BY importance_score DESC
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (date_str,))
                memories = cursor.fetchall()
        
        if not memories:
            return None
        
        # 2. 提取关键信息
        key_decisions = []
        action_items = []
        people = set()
        topics = set()
        
        for m in memories:
            content = m[4]  # content
            
            # 检测决策（包含"决定"、"选择"等词）
            if any(w in content for w in ['决定', '选择', '确定', '完成', '创建', '配置']):
                key_decisions.append(content[:100])
            
            # 检测行动项（包含"TODO"、"待办"等）
            if any(w in content for w in ['TODO', '待办', '需要', '计划']):
                action_items.append(content[:100])
            
            # 提取人名/角色（简单规则）
            words = re.findall(r'[\u4e00-\u9fa5]{2,4}', content)
            for w in words:
                if w in ['大王', 'Marvin', '用户', '管理员']:
                    people.add(w)
            
            # 提取主题
            if m[3]:  # category
                topics.add(m[3])
        
        # 3. 生成摘要文本
        content_summary = f"今日共记录 {len(memories)} 条记忆。"
        if key_decisions:
            content_summary += f" 关键决策: {len(key_decisions)} 项。"
        if action_items:
            content_summary += f" 待办事项: {len(action_items)} 项。"
        
        # 4. 保存摘要
        sql = """
        INSERT INTO memory_summaries 
        (summary_date, content_summary, key_decisions, action_items, people_mentioned, topics)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (summary_date) DO UPDATE SET
        content_summary = EXCLUDED.content_summary,
        key_decisions = EXCLUDED.key_decisions,
        action_items = EXCLUDED.action_items
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (
                    date_str,
                    content_summary,
                    json.dumps(key_decisions[:10]),
                    json.dumps(action_items[:10]),
                    json.dumps(list(people)),
                    json.dumps(list(topics))
                ))
                conn.commit()
        
        return {
            'date': date_str,
            'total_memories': len(memories),
            'key_decisions': key_decisions,
            'action_items': action_items,
            'people': list(people),
            'topics': list(topics)
        }
    
    def hybrid_search(self, query: str, top_k: int = 10):
        """混合检索：向量 + 关键词 + SQL"""
        if not RDS_AVAILABLE:
            return []
        
        results = []
        
        # 1. 全文搜索（PostgreSQL内置）
        sql_fts = """
        SELECT *, ts_rank(to_tsvector('simple', content), plainto_tsquery('simple', %s)) as rank
        FROM memories
        WHERE to_tsvector('simple', content) @@ plainto_tsquery('simple', %s)
        ORDER BY rank DESC
        LIMIT %s
        """
        
        # 2. 关键词模糊匹配
        sql_like = """
        SELECT * FROM memories
        WHERE content ILIKE %s OR keywords::text ILIKE %s
        ORDER BY importance_score DESC, created_at DESC
        LIMIT %s
        """
        
        # 3. 关联记忆搜索（通过关键词匹配）
        sql_related = """
        SELECT m.*, ml.strength as link_score
        FROM memories m
        JOIN memory_links ml ON m.id = ml.target_memory_id
        WHERE ml.source_memory_id IN (
            SELECT id FROM memories 
            WHERE content ILIKE %s 
            ORDER BY created_at DESC LIMIT 5
        )
        ORDER BY ml.strength DESC
        LIMIT %s
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                # 执行三种搜索
                try:
                    cursor.execute(sql_fts, (query, query, top_k))
                    fts_results = cursor.fetchall()
                except:
                    fts_results = []
                
                cursor.execute(sql_like, (f'%{query}%', f'%{query}%', top_k))
                like_results = cursor.fetchall()
                
                try:
                    cursor.execute(sql_related, (f'%{query}%', top_k))
                    related_results = cursor.fetchall()
                except:
                    related_results = []
        
        # 4. RRF融合排序
        combined = self._reciprocal_rank_fusion(
            fts_results, like_results, related_results
        )
        
        return combined[:top_k]
    
    def _reciprocal_rank_fusion(self, *result_lists):
        """RRF融合算法"""
        k = 60  # RRF常数
        scores = {}
        
        for results in result_lists:
            for rank, item in enumerate(results):
                item_id = item[0]  # id
                if item_id not in scores:
                    scores[item_id] = {'item': item, 'score': 0}
                scores[item_id]['score'] += 1.0 / (k + rank + 1)
        
        # 排序
        sorted_results = sorted(scores.values(), 
                               key=lambda x: x['score'], 
                               reverse=True)
        return [r['item'] for r in sorted_results]
    
    def proactive_recall(self, query: str = None):
        """主动回忆：基于当前查询和时间模式建议相关记忆"""
        if not RDS_AVAILABLE:
            return []
        
        suggestions = []
        now = datetime.now()
        
        # 1. 基于时间模式的建议
        sql_pattern = """
        SELECT category, SUM(access_count) as total
        FROM memory_access_patterns
        WHERE hour_of_day = %s AND day_of_week = %s
        GROUP BY category
        ORDER BY total DESC
        LIMIT 3
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_pattern, (now.hour, now.weekday()))
                patterns = cursor.fetchall()
                
                for p in patterns:
                    # 获取该类别的最新记忆
                    cursor.execute("""
                        SELECT * FROM memories
                        WHERE category = %s
                        ORDER BY last_accessed DESC NULLS LAST
                        LIMIT 2
                    """, (p[0],))
                    suggestions.extend(cursor.fetchall())
        
        # 2. 基于查询关键词的建议
        if query:
            # 提取关键词
            keywords = self._extract_keywords(query)
            if keywords:
                sql = """
                SELECT * FROM memories
                WHERE content ILIKE ANY(%s)
                ORDER BY importance_score DESC, created_at DESC
                LIMIT 3
                """
                
                with self.rds.get_connection() as conn:
                    with conn.cursor() as cursor:
                        patterns = [f'%{k}%' for k in keywords[:3]]
                        cursor.execute(sql, (patterns,))
                        suggestions.extend(cursor.fetchall())
        
        # 去重
        seen = set()
        unique_suggestions = []
        for s in suggestions:
            if s[0] not in seen:
                seen.add(s[0])
                unique_suggestions.append(s)
        
        return unique_suggestions[:5]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        words = re.findall(r'[\u4e00-\u9fa5]{2,}|[a-zA-Z]{3,}', text.lower())
        # 简单频率统计
        freq = {}
        for w in words:
            freq[w] = freq.get(w, 0) + 1
        return [w for w, c in sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]]
    
    def update_access_pattern(self, category: str):
        """更新访问模式统计"""
        if not RDS_AVAILABLE:
            return
        
        now = datetime.now()
        sql = """
        INSERT INTO memory_access_patterns (hour_of_day, day_of_week, category, access_count, last_accessed)
        VALUES (%s, %s, %s, 1, NOW())
        ON CONFLICT (hour_of_day, day_of_week, category) DO UPDATE
        SET access_count = memory_access_patterns.access_count + 1,
            last_accessed = NOW()
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (now.hour, now.weekday(), category))
                conn.commit()
    
    def auto_maintain(self):
        """自动维护：清理过期记忆、升级重要记忆"""
        if not RDS_AVAILABLE:
            return "RDS不可用"
        
        results = []
        
        # 1. 升级高频访问记忆
        sql_upgrade = """
        UPDATE memories
        SET memory_type = 'long_term', tier = 1
        WHERE access_count > 5 
        AND importance_score > 0.7
        AND memory_type = 'short_term'
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_upgrade)
                upgraded = cursor.rowcount
                conn.commit()
                results.append(f"升级 {upgraded} 条记忆为长期记忆")
        
        # 2. 清理过期短期记忆
        sql_cleanup = """
        DELETE FROM memories
        WHERE memory_type = 'short_term'
        AND tier = 3
        AND importance_score < 0.3
        AND access_count < 3
        AND created_at < NOW() - INTERVAL '30 days'
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_cleanup)
                deleted = cursor.rowcount
                conn.commit()
                results.append(f"清理 {deleted} 条过期记忆")
        
        # 3. 自动创建关联
        links = self.auto_link_memories()
        results.append(f"创建 {links} 条记忆关联")
        
        return "\n".join(results)


def main():
    import sys
    
    optimizer = MemoryOptimizer()
    
    if len(sys.argv) < 2:
        print("🧠 记忆层优化系统")
        print("\n用法:")
        print("  python3 memory_optimizer.py init              # 初始化增强表")
        print("  python3 memory_optimizer.py link              # 自动创建记忆关联")
        print("  python3 memory_optimizer.py summary [日期]    # 生成每日摘要")
        print("  python3 memory_optimizer.py search <关键词>   # 混合检索")
        print("  python3 memory_optimizer.py suggest [查询]    # 主动回忆")
        print("  python3 memory_optimizer.py maintain          # 自动维护")
        print("\n示例:")
        print("  python3 memory_optimizer.py init")
        print("  python3 memory_optimizer.py search RDS配置")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'init':
        optimizer.init_enhanced_tables()
    
    elif cmd == 'link':
        count = optimizer.auto_link_memories()
        print(f"✅ 创建了 {count} 条记忆关联")
    
    elif cmd == 'summary':
        date = sys.argv[2] if len(sys.argv) > 2 else None
        result = optimizer.generate_daily_summary(date)
        if result:
            print(f"📅 {result['date']} 摘要")
            print(f"记忆数量: {result['total_memories']}")
            print(f"关键决策: {len(result['key_decisions'])}")
            print(f"待办事项: {len(result['action_items'])}")
        else:
            print("📭 该日期无记忆")
    
    elif cmd == 'search':
        query = sys.argv[2]
        results = optimizer.hybrid_search(query)
        print(f"找到 {len(results)} 条相关记忆:")
        for r in results[:5]:
            print(f"  [{r[3]}] {r[4][:80]}...")
    
    elif cmd == 'suggest':
        query = sys.argv[2] if len(sys.argv) > 2 else None
        suggestions = optimizer.proactive_recall(query)
        if suggestions:
            print("💡 你可能还想了解:")
            for s in suggestions:
                print(f"  • [{s[3]}] {s[4][:60]}...")
        else:
            print("📭 暂无相关建议")
    
    elif cmd == 'maintain':
        result = optimizer.auto_maintain()
        print(result)
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
