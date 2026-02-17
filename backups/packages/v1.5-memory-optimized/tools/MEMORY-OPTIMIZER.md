# 🧠 记忆层优化系统

## 概述

增强型记忆系统，支持关联记忆、自动摘要、混合检索和主动回忆。

---

## 功能特性

### 1. 记忆关联图谱
- 记忆之间自动/手动创建关联
- 支持多种关联类型：related, part_of, caused, same_topic
- 关联强度评分（0-1）

### 2. 自动摘要
- 每日自动生成摘要
- 提取关键决策和待办事项
- 识别涉及人员和主题

### 3. 混合检索
- 全文搜索 + 关键词匹配 + 关联记忆
- RRF融合排序算法
- 提高搜索准确率

### 4. 主动回忆
- 基于时间模式推荐相关记忆
- 基于查询关键词推荐
- 无需主动搜索即可获取上下文

---

## 使用方法

### 初始化
```bash
python3 tools/memory_optimizer.py init
```

### 自动创建记忆关联
```bash
python3 tools/memory_optimizer.py link
```

### 生成每日摘要
```bash
# 今日摘要
python3 tools/memory_optimizer.py summary

# 指定日期
python3 tools/memory_optimizer.py summary 2026-02-16
```

### 混合检索
```bash
python3 tools/memory_optimizer.py search "关键词"
```

### 主动回忆
```bash
python3 tools/memory_optimizer.py suggest
python3 tools/memory_optimizer.py suggest "查询内容"
```

### 自动维护
```bash
python3 tools/memory_optimizer.py maintain
```

---

## 数据表结构

### memory_links
存储记忆之间的关联
- source_memory_id: 源记忆ID
- target_memory_id: 目标记忆ID
- link_type: 关联类型
- strength: 关联强度

### memory_summaries
存储每日摘要
- summary_date: 日期
- content_summary: 内容摘要
- key_decisions: 关键决策（JSON）
- action_items: 待办事项（JSON）
- people_mentioned: 涉及人员
- topics: 主题

### memory_access_patterns
存储访问模式统计
- hour_of_day: 小时
- day_of_week: 星期
- category: 类别
- access_count: 访问次数

---

## 集成说明

与现有记忆系统集成：
- 复用 RDSManager 连接
- 扩展现有 memories 表
- 兼容 memory_rds.py 工具

---

## 示例

### 查看关联记忆
```python
from memory_optimizer import MemoryOptimizer

opt = MemoryOptimizer()
related = opt.find_related_memories(memory_id=16)  # RDS配置记忆的关联
for r in related:
    print(f"关联: {r[1]} (强度: {r[-1]})")
```

### 添加记忆时创建关联
```python
from memory_rds import MemoryRDS
from memory_optimizer import MemoryOptimizer

mem = MemoryRDS()
opt = MemoryOptimizer()

# 添加新记忆
mid = mem.add_memory("新功能开发完成", "dev", importance=0.8)

# 关联到现有记忆
opt.create_memory_link(mid, 2, "part_of", 0.9)  # 关联到系统升级
```

---

## 维护建议

- 每天运行 `summary` 生成当日摘要
- 每周运行 `maintain` 清理过期记忆
- 定期运行 `link` 自动发现新的关联

---

创建时间: 2026-02-16
版本: 1.0
