#!/usr/bin/env python3
"""
本地智能记忆系统
无需外部API，使用本地嵌入模型实现语义搜索
"""

import os
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path

# 尝试导入向量库
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer
    VECTOR_LIBS_AVAILABLE = True
except ImportError:
    VECTOR_LIBS_AVAILABLE = False
    print("⚠️ 向量库未安装，使用关键词搜索模式")

# 配置
MEMORY_DIR = Path("/root/.openclaw/workspace/memory")
VECTOR_DB_PATH = MEMORY_DIR / "vector_db"
MEMORY_FILE = Path("/root/.openclaw/workspace/MEMORY.md")

class LocalMemory:
    """本地记忆管理器"""
    
    def __init__(self):
        self.model = None
        self.embeddings = {}
        self.documents = []
        
        if VECTOR_LIBS_AVAILABLE:
            try:
                # 使用轻量级中文模型
                print("🔄 加载嵌入模型...")
                self.model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                print("✅ 模型加载完成")
            except Exception as e:
                print(f"⚠️ 模型加载失败: {e}")
                self.model = None
        
        # 确保目录存在
        MEMORY_DIR.mkdir(exist_ok=True)
        VECTOR_DB_PATH.mkdir(exist_ok=True)
        
        # 加载现有记忆
        self.load_memory()
    
    def load_memory(self):
        """从文件加载记忆"""
        # 加载 MEMORY.md
        if MEMORY_FILE.exists():
            with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
                self._index_document("MEMORY.md", content)
        
        # 加载 memory/*.md
        for md_file in MEMORY_DIR.glob("*.md"):
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self._index_document(md_file.name, content)
        
        print(f"📚 已加载 {len(self.documents)} 个记忆文档")
    
    def _index_document(self, filename, content):
        """索引文档"""
        # 分割成段落
        paragraphs = [p.strip() for p in re.split(r'\n\n+', content) if p.strip()]
        
        for i, para in enumerate(paragraphs):
            doc_id = f"{filename}#{i}"
            self.documents.append({
                'id': doc_id,
                'filename': filename,
                'content': para,
                'length': len(para)
            })
            
            # 生成嵌入
            if self.model:
                self.embeddings[doc_id] = self.model.encode(para)
    
    def search(self, query, top_k=5):
        """搜索记忆"""
        if not self.documents:
            return []
        
        results = []
        
        if self.model and query in self.embeddings:
            # 语义搜索
            query_vec = self.model.encode(query)
            
            for doc in self.documents:
                doc_id = doc['id']
                if doc_id in self.embeddings:
                    # 计算余弦相似度
                    similarity = self._cosine_similarity(query_vec, self.embeddings[doc_id])
                    results.append({
                        **doc,
                        'score': float(similarity),
                        'match_type': 'semantic'
                    })
            
            # 按相似度排序
            results.sort(key=lambda x: x['score'], reverse=True)
            results = results[:top_k]
        
        else:
            # 关键词搜索
            query_words = set(query.lower().split())
            
            for doc in self.documents:
                content_lower = doc['content'].lower()
                
                # 计算匹配分数
                matches = sum(1 for word in query_words if word in content_lower)
                score = matches / len(query_words) if query_words else 0
                
                if score > 0:
                    results.append({
                        **doc,
                        'score': score,
                        'match_type': 'keyword'
                    })
            
            results.sort(key=lambda x: x['score'], reverse=True)
            results = results[:top_k]
        
        return results
    
    def _cosine_similarity(self, a, b):
        """计算余弦相似度"""
        return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    def add_memory(self, content, category="general", tags=None):
        """添加新记忆"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 生成文件名
        content_hash = hashlib.md5(content.encode()).hexdigest()[:8]
        filename = f"{timestamp}_{content_hash}.md"
        
        # 构建记忆内容
        memory_entry = f"""# 记忆条目 [{timestamp}]

**类别**: {category}
**标签**: {', '.join(tags or [])}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 内容

{content}

---
*自动记录*
"""
        
        # 保存到文件
        filepath = MEMORY_DIR / filename
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(memory_entry)
        
        # 更新索引
        self._index_document(filename, memory_entry)
        
        print(f"✅ 记忆已保存: {filename}")
        return filename
    
    def extract_facts(self, conversation):
        """从对话中提取事实"""
        facts = []
        
        # 提取关键信息模式
        patterns = [
            (r'我叫(\S+)', 'name', '用户名为: {}'),
            (r'我喜欢(\S+)', 'preference', '喜欢: {}'),
            (r'我在(\S+)', 'location', '位置: {}'),
            (r'(\S+)是我的', 'possession', '拥有: {}'),
            (r'我(\S+)岁', 'age', '年龄: {}'),
        ]
        
        for pattern, fact_type, template in patterns:
            matches = re.findall(pattern, conversation)
            for match in matches:
                facts.append({
                    'type': fact_type,
                    'content': template.format(match),
                    'source': 'conversation'
                })
        
        return facts
    
    def summarize_daily(self, date_str=None):
        """生成每日记忆摘要"""
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        
        # 查找当天的记忆
        daily_memories = []
        for doc in self.documents:
            if date_str in doc['filename'] or date_str in doc['content']:
                daily_memories.append(doc)
        
        if not daily_memories:
            return f"📭 {date_str} 没有新记忆"
        
        summary = f"📚 记忆摘要 [{date_str}]\n"
        summary += "=" * 50 + "\n\n"
        
        # 按类别分组
        by_category = {}
        for mem in daily_memories:
            # 从内容中提取类别
            cat_match = re.search(r'\*\*类别\*\*:\s*(\w+)', mem['content'])
            category = cat_match.group(1) if cat_match else 'general'
            
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(mem)
        
        for category, items in by_category.items():
            summary += f"📁 {category.upper()} ({len(items)} 条)\n"
            for item in items[:3]:  # 每类最多显示3条
                content_preview = item['content'][:100].replace('\n', ' ')
                summary += f"  • {content_preview}...\n"
            if len(items) > 3:
                summary += f"  ... 还有 {len(items) - 3} 条\n"
            summary += "\n"
        
        return summary


def main():
    import sys
    
    memory = LocalMemory()
    
    if len(sys.argv) < 2:
        print("🧠 本地智能记忆系统")
        print("\n用法:")
        print("  python3 memory_local.py search <查询>    # 搜索记忆")
        print("  python3 memory_local.py add <内容>       # 添加记忆")
        print("  python3 memory_local.py summary [日期]   # 每日摘要")
        print("  python3 memory_local.py stats            # 统计信息")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'search':
        query = sys.argv[2] if len(sys.argv) > 2 else input("搜索: ")
        results = memory.search(query)
        
        print(f"\n🔍 搜索: '{query}'")
        print(f"找到 {len(results)} 条结果:\n")
        
        for i, r in enumerate(results, 1):
            match_icon = "🔴" if r['score'] > 0.8 else "🟡" if r['score'] > 0.5 else "🟢"
            print(f"{i}. [{match_icon}] {r['filename']} ({r['match_type']}, 得分: {r['score']:.3f})")
            print(f"   {r['content'][:150]}...")
            print()
    
    elif cmd == 'add':
        content = sys.argv[2] if len(sys.argv) > 2 else input("记忆内容: ")
        category = sys.argv[3] if len(sys.argv) > 3 else "general"
        tags = sys.argv[4].split(',') if len(sys.argv) > 4 else []
        
        memory.add_memory(content, category, tags)
    
    elif cmd == 'summary':
        date = sys.argv[2] if len(sys.argv) > 2 else None
        print(memory.summarize_daily(date))
    
    elif cmd == 'stats':
        print("📊 记忆统计")
        print(f"   文档数: {len(memory.documents)}")
        print(f"   向量数: {len(memory.embeddings)}")
        print(f"   向量库可用: {VECTOR_LIBS_AVAILABLE}")
        print(f"   模型加载: {memory.model is not None}")
        
        # 文件统计
        md_files = list(MEMORY_DIR.glob("*.md"))
        print(f"   记忆文件: {len(md_files)}")
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
