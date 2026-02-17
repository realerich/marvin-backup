# 🗄️ RDS数据库工具套件

阿里云RDS全面利用方案

---

## 📋 已创建的表

| 表名 | 用途 | 核心功能 |
|:---|:---|:---|
| `restaurants` | 餐厅数据 | 地理坐标、附近搜索、按城市筛选 |
| `system_metrics` | 系统监控 | 时序存储、趋势分析、报警记录 |
| `emails` | 邮件归档 | 全文搜索、分类管理、未读统计 |
| `memories` | 记忆存储 | 关键词提取、重要性评分、访问统计 |
| `webhook_logs` | Webhook日志 | 调用记录、性能分析、故障追踪 |
| `tasks` | 任务管理 | 待办事项、优先级、截止日期 |

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip3 install pymysql --break-system-packages
```

### 2. 配置RDS连接

```bash
# 完整设置（创建所有表）
python3 tools/rds_master.py setup <RDS主机> <端口> <数据库> <用户名> <密码>

# 示例
python3 tools/rds_master.py setup rm-xxx.mysql.rds.aliyuncs.com 3306 marvin_db admin your_password
```

### 3. 导入现有数据

```bash
python3 tools/rds_master.py import-data
```

---

## 🛠️ 工具详解

### 🔧 rds_manager.py - 数据库管理

```bash
# 配置连接
python3 tools/rds_manager.py setup <host> <port> <db> <user> <pass>

# 初始化表结构
python3 tools/rds_manager.py init

# 测试连接
python3 tools/rds_manager.py test

# 查看状态
python3 tools/rds_manager.py status
```

### 🍽️ restaurant_rds.py - 餐厅数据

```bash
# 导入CSV
python3 tools/restaurant_rds.py import restaurants_full_with_coords.csv

# 附近搜索
python3 tools/restaurant_rds.py nearby 23.1291 113.2644 5

# 按城市搜索
python3 tools/restaurant_rds.py city 广州 4.5

# 统计信息
python3 tools/restaurant_rds.py stats
```

### 📊 metrics_rds.py - 系统监控

```bash
# 保存当前指标
python3 tools/metrics_rds.py save

# 查看趋势（最近24小时）
python3 tools/metrics_rds.py trend

# 每日汇总
python3 tools/metrics_rds.py daily 7

# 查看报警
python3 tools/metrics_rds.py alerts

# 清理旧数据（保留30天）
python3 tools/metrics_rds.py cleanup 30
```

### 📧 email_rds.py - 邮件归档

```bash
# 邮件统计
python3 tools/email_rds.py stats

# 搜索邮件
python3 tools/email_rds.py search "会议"

# 未读摘要
python3 tools/email_rds.py unread

# 清理旧营销邮件
python3 tools/email_rds.py cleanup 30
```

### 🧠 memory_rds.py - 记忆存储

```bash
# 添加记忆
python3 tools/memory_rds.py add "今天完成了RDS配置" "tech" 0.8

# 搜索记忆
python3 tools/memory_rds.py search "RDS"

# 最近记忆
python3 tools/memory_rds.py recent 24

# 热门记忆
python3 tools/memory_rds.py popular

# 统计
python3 tools/memory_rds.py stats

# 清理旧短期记忆
python3 tools/memory_rds.py cleanup 7
```

### 🔗 webhook_rds.py - Webhook日志

```bash
# 统计信息
python3 tools/webhook_rds.py stats

# 最近日志
python3 tools/webhook_rds.py recent

# 慢请求分析
python3 tools/webhook_rds.py slow 5000

# 清理旧日志
python3 tools/webhook_rds.py cleanup 30
```

### 🎯 rds_master.py - 综合入口

```bash
# 完整设置
python3 tools/rds_master.py setup <host> <port> <db> <user> <pass>

# 导入所有数据
python3 tools/rds_master.py import-data

# 查看所有统计
python3 tools/rds_master.py stats
```

---

## 💡 典型使用场景

### 场景1: 找附近的高分餐厅

```python
from tools.restaurant_rds import RestaurantRDS

tool = RestaurantRDS()
results = tool.search_nearby(lat=23.1291, lng=113.2644, radius_km=3, min_rating=4.5)
print(tool.format_nearby_results(results))
```

### 场景2: 记录系统监控

```python
from tools.metrics_rds import SystemMetricsRDS
import psutil

tool = SystemMetricsRDS()
stats = {
    'cpu': {'percent': psutil.cpu_percent(), 'count': psutil.cpu_count()},
    'memory': {...},
    'disk': {...},
    'network': {...}
}
tool.save_metrics(stats)
```

### 场景3: 归档邮件

```python
from tools.email_rds import EmailArchiveRDS

tool = EmailArchiveRDS()
for email in fetched_emails:
    category = classify_email(email)  # important/promo/normal
    tool.archive_email(email, category)
```

### 场景4: 存储重要记忆

```python
from tools.memory_rds import MemoryRDS

tool = MemoryRDS()
tool.add_memory(
    content="用户完成了GitHub邮箱更改",
    category="user_action",
    importance=0.8,
    source="chat"
)
```

---

## 📊 数据清理策略

| 数据类型 | 保留时间 | 清理命令 |
|:---|:---:|:---|
| 系统监控 | 30天 | `metrics_rds.py cleanup 30` |
| 营销邮件 | 30天 | `email_rds.py cleanup 30` |
| 短期记忆 | 7天 | `memory_rds.py cleanup 7` |
| Webhook日志 | 30天 | `webhook_rds.py cleanup 30` |

---

## 🔒 安全说明

- RDS密码存储在 `config/rds_config.json` (权限600)
- 所有连接使用SSL加密
- 建议定期轮换RDS密码
- 生产环境建议限制RDS访问IP

---

## 📝 下一步

1. **配置RDS连接** - 运行 `rds_master.py setup`
2. **导入餐厅数据** - CSV导入到数据库
3. **修改监控脚本** - 让 `system_monitor.py` 同时写入RDS
4. **集成邮件归档** - 修改 `email_smart.py` 归档到RDS
5. **迁移记忆系统** - 可选：从本地JSON迁移到RDS

**需要我帮你配置RDS连接吗？** 提供你的RDS连接信息即可。
