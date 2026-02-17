#!/usr/bin/env python3
"""
增强记忆搜索 - 纯本地实现
无需外部API，使用关键词+上下文匹配
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
MEMORY_FILE = Path("/root/.openclaw/workspace/MEMORY.md")
INDEX_FILE = Path("/root/.openclaw/workspace/config/memory_index.json")

class SimpleMemory:
    """简化版记忆系统"""
    
    def __init__(self):
        self.index = {'documents': {}, 'keywords': defaultdict(list)}
        self._build_index()
    
    def _build_index(self):
        """构建关键词索引"""
        print("🔄 构建记忆索引...")
        
        docs_to_index = []
        
        # 加载 MEMORY.md
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                docs_to_index.append(('MEMORY.md', f.read()))
        
        # 加载 memory/*.md
        for md_file in sorted(MEMORY_DIR.glob("*.md")):
            with open(md_file, 'r', encoding='utf-8') as f:
                docs_to_index.append((md_file.name, f.read()))
        
        # 索引每个文档
        for filename, content in docs_to_index:
            # 分割成段落
            paragraphs = [p.strip() for p in re.split(r'\n\n+', content) if len(p.strip()) > 20]
            
            for i, para in enumerate(paragraphs):
                doc_id = f"{filename}#{i}"
                
                # 提取关键词
                words = self._extract_keywords(para)
                
                self.index['documents'][doc_id] = {
                    'id': doc_id,
                    'filename': filename,
                    'content': para[:500],  # 限制长度
                    'keywords': words,
                    'word_count': len(para.split()),
                    'timestamp': self._extract_date(filename, para)
                }
                
                # 反向索引
                for word in words:
                    self.index['keywords'][word].append(doc_id)
        
        print(f"✅ 索引完成: {len(self.index['documents'])} 段落, {len(self.index['keywords'])} 关键词")
    
    def _extract_keywords(self, text):
        """提取关键词"""
        # 清理文本
        text = re.sub(r'[^\w\u4e00-\u9fa5\s]', ' ', text)  # 保留中文和英文
        words = text.lower().split()
        
        # 过滤停用词
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 
                     '的', '了', '和', '是', '在', '有', '我', '你', '他', '它',
                     'this', 'that', 'these', 'those', 'to', 'of', 'in', 'for',
                     'with', 'on', 'at', 'by', 'from', 'as', 'it', 'its'}
        
        # 过滤短词和停用词，但保留中文
        keywords = []
        for w in words:
            if len(w) >= 2 or any('\u4e00' <= c <= '\u9fff' for c in w):
                if w not in stopwords:
                    keywords.append(w)
        
        return list(set(keywords))  # 去重
    
    def _extract_date(self, filename, content):
        """提取日期"""
        # 从文件名提取
        date_match = re.search(r'(\d{4}-\d{2}-\d{2}|\d{8})', filename)
        if date_match:
            return date_match.group(1)
        
        # 从内容提取
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', content)
        if date_match:
            return date_match.group(1)
        
        return None
    
    def search(self, query, top_k=5, context_lines=2):
        """搜索记忆"""
        query_words = self._extract_keywords(query)
        
        if not query_words:
            return []
        
        # 计算匹配分数
        scores = defaultdict(float)
        matched_keywords = defaultdict(set)
        
        for word in query_words:
            for doc_id in self.index['keywords'].get(word, []):
                scores[doc_id] += 1
                matched_keywords[doc_id].add(word)
        
        # 归一化分数
        for doc_id in scores:
            doc = self.index['documents'][doc_id]
            # 考虑关键词覆盖率和文档长度
            coverage = len(matched_keywords[doc_id]) / len(query_words)
            length_bonus = min(doc['word_count'] / 100, 1.0)  # 长度奖励
            scores[doc_id] = (scores[doc_id] * coverage) * (1 + length_bonus * 0.2)
        
        # 排序并返回前K个
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, score in sorted_results[:top_k]:
            doc = self.index['documents'][doc_id]
            results.append({
                'id': doc_id,
                'filename': doc['filename'],
                'content': doc['content'],
                'score': score,
                'matched': list(matched_keywords[doc_id]),
                'date': doc['timestamp']
            })
        
        return results
    
    def add_fact(self, fact_text, category="auto"):
        """添加事实记忆"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        date_str = datetime.now().strftime('%Y-%m-%d')
        
        filename = f"{date_str}_fact_{timestamp}.md"
        filepath = MEMORY_DIR / filename
        
        content = f"""# 自动提取记忆

**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**类别**: {category}

## 内容

{fact_text}

---
"""
        
        MEMORY_DIR.mkdir(exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        # 更新索引
        words = self._extract_keywords(fact_text)
        doc_id = f"{filename}#0"
        self.index['documents'][doc_id] = {
            'id': doc_id,
            'filename': filename,
            'content': fact_text,
            'keywords': words,
            'timestamp': date_str
        }
        for word in words:
            self.index['keywords'][word].append(doc_id)
        
        return filename
    
    def get_recent(self, days=7, limit=10):
        """获取最近记忆"""
        recent = []
        cutoff = datetime.now().timestamp() - (days * 86400)
        
        for doc_id, doc in self.index['documents'].items():
            if doc['timestamp']:
                try:
                    # 解析日期
                    if '-' in doc['timestamp']:
                        doc_date = datetime.strptime(doc['timestamp'][:10], '%Y-%m-%d')
                        if doc_date.timestamp() >= cutoff:
                            recent.append(doc)
                except:
                    pass
        
        # 按日期排序
        recent.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return recent[:limit]


def main():
    import sys
    
    memory = SimpleMemory()
    
    if len(sys.argv) < 2:
        print("🧠 增强记忆系统")
        print("\n用法:")
        print("  python3 memory_simple.py search <查询>    # 搜索记忆")
        print("  python3 memory_simple.py add <内容>       # 添加记忆")
        print("  python3 memory_simple.py recent [天数]    # 最近记忆")
        print("  python3 memory_simple.py stats            # 统计")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'search':
        query = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else input("搜索: ")
        results = memory.search(query)
        
        print(f"\n🔍 搜索: '{query}'")
        print(f"找到 {len(results)} 条结果:\n")
        
        for i, r in enumerate(results, 1):
            match_level = "🔴" if r['score'] > 2 else "🟡" if r['score'] > 1 else "🟢"
            print(f"{i}. [{match_level}] {r['filename']}")
            if r['date']:
                print(f"   日期: {r['date']}")
            print(f"   匹配: {', '.join(r['matched'][:5])}")
            print(f"   内容: {r['content'][:120]}...")
            print()
    
    elif cmd == 'add':
        content = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else input("记忆内容: ")
        category = input("类别 (auto/fact/preference/goal): ") or "auto"
        filename = memory.add_fact(content, category)
        print(f"✅ 已保存: {filename}")
    
    elif cmd == 'recent':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        recent = memory.get_recent(days)
        
        print(f"\n📅 最近 {days} 天记忆 ({len(recent)} 条):\n")
        for doc in recent:
            print(f"• [{doc.get('timestamp', 'N/A')}] {doc['content'][:80]}...")
    
    elif cmd == 'stats':
        print("📊 记忆统计")
        print(f"   段落数: {len(memory.index['documents'])}")
        print(f"   关键词: {len(memory.index['keywords'])}")
        
        # 文件统计
        files = set(d['filename'] for d in memory.index['documents'].values())
        print(f"   源文件: {len(files)}")
        
        # 最近更新
        recent = memory.get_recent(1, 3)
        if recent:
            print(f"\n📝 最近添加:")
            for r in recent:
                print(f"   • {r['content'][:60]}...")
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
