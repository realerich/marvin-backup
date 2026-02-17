# 飞书 ↔ RDS 消息同步 - 健壮版实现

## 问题背景

之前的飞书消息同步到 RDS 失败，主要问题：
1. **连接池耗尽** - 频繁的连接/断开导致阿里云RDS连接数限制
2. **网络不稳定** - 偶发的网络抖动导致连接超时
3. **无容错机制** - RDS 失败时消息丢失

## 解决方案

### 1. 连接池管理 (`tools/rds_pool.py`)

```python
# 特点:
- ThreadedConnectionPool: 连接复用，减少创建开销
- maxconn=10: 适当扩大连接池
- connect_timeout=10s: 连接超时控制
- 自动重试机制: 失败时重试3次
```

### 2. 本地队列兜底 (`tools/feishu_sync.py`)

```
飞书消息 → 尝试保存到 RDS
    ↓ 成功
    ✅ 完成
    ↓ 失败
    💾 保存到本地队列 (JSON文件)
    ↓ 定时同步
    🔄 队列 → RDS
```

### 3. 定时同步任务

| 任务 | 频率 | 功能 |
|------|------|------|
| `feishu-rds-sync` | 每10分钟 | 同步本地队列到RDS |

## 文件结构

```
tools/
├── rds_pool.py          # 连接池管理器 (NEW)
├── feishu_rds.py        # 飞书消息RDS操作 (UPDATED)
└── feishu_sync.py       # 同步协调器 (NEW)

data/
└── feishu_messages_queue.json  # 本地队列
```

## 使用方法

### 1. 测试连接
```bash
python3 tools/rds_pool.py test
```

### 2. 保存单条消息
```bash
python3 tools/feishu_sync.py test
```

### 3. 查看统计
```bash
python3 tools/feishu_rds.py stats
```

### 4. 手动同步队列
```bash
python3 tools/feishu_sync.py sync
```

### 5. 搜索历史消息
```bash
python3 tools/feishu_rds.py search "关键词"
```

## 与 OpenClaw 集成

### 方案1: 通过 Webhook (推荐)

配置 OpenClaw 发送消息事件到：
```
POST /webhook/feishu-message
```

处理脚本自动解析并保存到RDS。

### 方案2: 通过 Cron 定期同步

已配置定时任务每10分钟同步队列。

### 方案3: 实时保存 (当前实现)

修改 OpenClaw 消息处理器，在收到消息时立即调用：
```python
from feishu_sync import FeishuMessageSync

sync = FeishuMessageSync()
sync.process_inbound_message(message_data)
```

## 监控

### 健康检查
```bash
python3 tools/rds_pool.py health
```

### 队列状态
```bash
python3 tools/feishu_sync.py status
```

## 故障排查

### 连接失败
1. 检查RDS白名单是否包含ECS IP
2. 检查连接数是否超过限制 (`active_connections`)
3. 查看 `rds_pool.py` 日志

### 同步延迟
1. 检查定时任务是否正常执行
2. 手动运行 `feishu_sync.py sync`
3. 查看队列文件大小

### 数据丢失
1. 检查本地队列文件 `data/feishu_messages_queue.json`
2. 队列中的消息会在下次同步时重试
3. 最多保留1000条，超出会轮转

## 测试验证

```bash
# 1. 连接测试
python3 tools/rds_pool.py test

# 2. 保存测试
python3 tools/feishu_sync.py test

# 3. 查看统计
python3 tools/feishu_rds.py stats

# 4. 搜索验证
python3 tools/feishu_rds.py search "测试"
```

## 状态

- ✅ 连接池管理 - 完成
- ✅ 本地队列兜底 - 完成
- ✅ 定时同步任务 - 已配置
- ✅ 故障重试机制 - 完成
- ⏳ OpenClaw实时集成 - 待配置

---

**最后更新**: 2026-02-17 08:55