# OpenClaw 实时消息同步配置指南

## 目标
配置 OpenClaw 在收到每条飞书消息时，自动保存到 RDS。

## 方案选择

### 方案1: AI助手内置保存 (推荐，最简单)

修改 AI 助手的消息处理逻辑，在每次回复前/后自动保存消息。

**实现方式**:
在 SOUL.md 或 AGENTS.md 中添加指令:

```markdown
## 消息处理流程

每次收到消息时:
1. 解析消息元数据
2. 调用保存钩子: `python3 tools/feishu_hook.py save '<json>'`
3. 正常处理消息内容
```

**当前消息格式示例**:
```json
{
  "schema": "openclaw.inbound_meta.v1",
  "channel": "feishu",
  "provider": "feishu",
  "surface": "feishu",
  "chat_type": "direct",
  "flags": {
    "has_reply_context": false,
    "has_forwarded_context": false,
    "has_thread_starter": false,
    "history_count": 0
  }
}
```

**优点**: 无需修改 OpenClaw 核心代码
**缺点**: 依赖 AI 助手主动调用

---

### 方案2: Webhook 中间件

配置 OpenClaw 将所有消息事件发送到一个 webhook，由 webhook 处理后保存到 RDS。

**配置步骤**:

1. **创建 Webhook 处理器** (tools/feishu_webhook_handler.py)

```python
#!/usr/bin/env python3
from flask import Flask, request
import json
from feishu_hook import save_inbound_message

app = Flask(__name__)

@app.route('/webhook/feishu-message', methods=['POST'])
def handle_message():
    data = request.json
    success = save_inbound_message(data)
    return {'success': success}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

2. **配置 OpenClaw Webhook**

在 OpenClaw 配置中添加:
```yaml
webhooks:
  - url: http://localhost:5000/webhook/feishu-message
    events: [message.received]
```

3. **启动 Webhook 服务**

```bash
python3 tools/feishu_webhook_handler.py
```

**优点**: 与 AI 助手解耦，更稳定
**缺点**: 需要额外运行服务

---

### 方案3: 文件系统轮询

OpenClaw 将消息写入文件，由定时任务读取并保存到 RDS。

**实现方式**:

1. OpenClaw 配置消息日志文件
2. 创建文件监听器 (inotify)
3. 新消息写入时触发同步

**优点**: 简单可靠
**缺点**: 有延迟（秒级）

---

## 推荐配置: 方案1 + 方案3 组合

### 即时层 (方案1)
AI 助手在处理消息时主动保存。

### 补偿层 (方案3)
定时任务每10分钟检查是否有漏保存的消息。

```
飞书消息
    ↓
┌──────────────────┐
│ AI助手处理       │ ← 主动保存 (方案1)
│ 调用feishu_hook  │
└──────────────────┘
    ↓
   RDS
    ↑
┌──────────────────┐
│ 定时任务         │ ← 补偿同步 (方案3)
│ 每10分钟检查     │
└──────────────────┘
```

---

## 当前状态

✅ **方案3 已配置**: 定时任务 `feishu-rds-sync` 每10分钟同步队列

⏳ **方案1 待配置**: 需要在 AI 助手处理逻辑中添加保存调用

---

## 立即启用方案1

作为 Marvin AI 助手，我将在每次收到你的消息时自动保存到 RDS。

**验证方式**:
发送任意消息后，检查:
```bash
python3 tools/feishu_rds.py stats
```

总消息数应该增加。

---

## 故障排查

### 保存失败怎么办？
1. 检查RDS连接: `python3 tools/rds_pool.py test`
2. 查看本地队列: `python3 tools/feishu_sync.py status`
3. 手动同步: `python3 tools/feishu_sync.py sync`

### 消息重复？
表中有 `message_id` 唯一约束，重复保存会被忽略。

### 性能问题？
- 连接池复用，无频繁创建开销
- 异步保存，不影响响应速度
- 本地队列兜底，RDS故障不阻塞

---

**配置完成时间**: 2026-02-17 09:00
**状态**: 方案3运行中，方案1待启用