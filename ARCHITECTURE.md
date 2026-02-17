# Marvin 四层架构整合指南

## 架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        交互层 - 飞书 (Feishu)                      │
│  ├─ 即时消息 (DM/群聊)                                             │
│  ├─ 消息自动同步到 RDS                                             │
│  └─ 任务/问题自动转 GitHub Issue                                   │
├─────────────────────────────────────────────────────────────────┤
│                        数据层 - 阿里云 RDS (PostgreSQL)            │
│  ├─ restaurants     - 餐厅数据                                    │
│  ├─ system_metrics  - 系统监控指标                                │
│  ├─ emails          - 邮件归档                                    │
│  ├─ memories        - AI 记忆                                     │
│  ├─ tasks           - 任务管理                                    │
│  ├─ webhook_logs    - Webhook 日志                               │
│  └─ feishu_messages - 飞书消息历史 (NEW)                          │
├─────────────────────────────────────────────────────────────────┤
│                        执行层 - 阿里云 ECS (OpenClaw)              │
│  ├─ OpenClaw 服务                                                 │
│  ├─ 定时任务 (Cron)                                               │
│  ├─ 工具脚本 (Python)                                             │
│  ├─ Docker 容器化支持 (NEW)                                       │
│  └─ 工作流引擎 (NEW)                                              │
├─────────────────────────────────────────────────────────────────┤
│                        代码层 - GitHub                            │
│  ├─ 备份仓库 (marvin-backup)                                      │
│  ├─ GitHub Issues - 任务/问题追踪                                 │
│  ├─ GitHub Actions - 自动化工作流                                 │
│  ├─ GitHub Pages - 状态仪表盘                                     │
│  └─ 数据可视化 (NEW)                                              │
└─────────────────────────────────────────────────────────────────┘
```

## 层间整合

### 1. 飞书 ↔ RDS (交互层 ↔ 数据层)

**功能**: 所有飞书消息自动存储到 RDS (健壮版)

**工具**: 
- `tools/rds_pool.py` - 连接池管理
- `tools/feishu_rds.py` - RDS操作
- `tools/feishu_sync.py` - 同步协调

**架构**:
```
飞书消息
    ↓
┌─────────────────────────────────────┐
│  feishu_sync.py (同步协调器)         │
│  - 优先尝试 RDS 保存                 │
│  - 失败时写入本地队列                 │
└─────────────────────────────────────┘
    ↓ 成功                    ↓ 失败
┌─────────────┐         ┌─────────────────────┐
│  RDS        │         │ 本地队列文件         │
│  (PostgreSQL)│        │ feishu_messages_    │
└─────────────┘         │   queue.json        │
                        └─────────────────────┘
                                    ↓
                        ┌─────────────────────┐
                        │ 定时任务每10分钟同步 │
                        │ feishu-rds-sync     │
                        └─────────────────────┘
```

**健壮性设计**:
- 连接池复用 (maxconn=10)
- 自动重试 (3次)
- 本地队列兜底
- 定时同步补偿

**使用**:
```bash
# 测试连接
python3 tools/rds_pool.py test

# 保存测试消息
python3 tools/feishu_sync.py test

# 查看统计
python3 tools/feishu_rds.py stats

# 搜索历史
python3 tools/feishu_rds.py search "关键词"

# 手动同步队列
python3 tools/feishu_sync.py sync
```

**表结构**:
```sql
CREATE TABLE feishu_messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(100) UNIQUE,
    sender_id VARCHAR(100),
    sender_name VARCHAR(100),
    chat_type VARCHAR(20),
    content TEXT,
    is_processed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**详细文档**: [docs/FEISHU-RDS-SYNC.md](docs/FEISHU-RDS-SYNC.md)

### 2. RDS ↔ GitHub (数据层 ↔ 代码层)

**功能**: RDS 数据自动导出到 GitHub 仓库

**工具**: `tools/rds_github_sync.py`

**使用**:
```bash
# 导出所有数据
python3 tools/rds_github_sync.py all

# 导出监控指标
python3 tools/rds_github_sync.py metrics

# 导出任务数据
python3 tools/rds_github_sync.py tasks
```

**输出文件**:
- `data/system_metrics_7d.json` - 7天监控指标
- `data/tasks.json` - 任务列表
- `data/dashboard.json` - 仪表盘数据

### 3. 飞书 ↔ GitHub (交互层 ↔ 代码层)

**功能**: 飞书消息自动转换为 GitHub Issue

**工具**: `tools/feishu_to_github.py`

**触发词**:
- `[TASK]` / `任务:` / `todo:` → 创建任务 Issue
- `[BUG]` / `bug:` / `错误:` → 创建 Bug Issue
- `[FEATURE]` / `feature:` → 创建功能请求 Issue

**使用**:
```bash
# 扫描未处理消息
python3 tools/feishu_to_github.py scan

# 转换单条消息
python3 tools/feishu_to_github.py convert "记得修复邮件脚本"
```

### 4. ECS ↔ GitHub (执行层 ↔ 代码层)

**功能**: ECS 健康状态自动上报到 GitHub

**工具**: `.github/workflows/health-check.yml`

**功能**:
- 每30分钟从 RDS 获取最新状态
- 更新 `status.json` 到仓库
- 生成状态徽章显示在 README

### 5. 全链路工作流

**工具**: `tools/workflow_engine.py`

**预定义工作流**:

| 工作流 | 触发 | 步骤 |
|--------|------|------|
| morning_routine | 每天 8:00 | 盘前简报 → 检查邮件 → 同步 GitHub |
| system_health_check | 每小时 | 系统监控 → 检查警报 → 更新 GitHub |
| data_sync | 每6小时 | 导出指标 → 导出任务 → 同步飞书到 GitHub |
| daily_cleanup | 每天 2:00 | 归档邮件 → 清理日志 → GitHub 备份 |

**使用**:
```bash
# 列出所有工作流
python3 tools/workflow_engine.py list

# 运行指定工作流
python3 tools/workflow_engine.py run morning_routine

# 运行所有工作流
python3 tools/workflow_engine.py run-all
```

## 部署指南

### Docker 部署 (推荐)

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f marvin
```

### 环境变量配置

复制 `.env.example` 为 `.env`，填写实际值：

```bash
# GitHub
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx

# 阿里云 RDS
RDS_HOST=pgm-xxxxx.pg.rds.aliyuncs.com
RDS_PORT=5432
RDS_DB=marvin_db
RDS_USER=marvin
RDS_PASSWORD=your_password
```

### GitHub Actions Secrets 配置

在 GitHub 仓库设置中添加以下 Secrets：

- `RDS_HOST` - RDS 主机地址
- `RDS_PORT` - RDS 端口
- `RDS_DB` - 数据库名
- `RDS_USER` - 用户名
- `RDS_PASSWORD` - 密码

## 监控与故障排查

### 检查各层状态

```bash
# 交互层 (飞书)
curl -s https://api.github.com/repos/realerich/marvin-backup/issues | jq length

# 数据层 (RDS)
python3 tools/rds_manager.py test

# 执行层 (ECS)
python3 tools/system_monitor.py

# 代码层 (GitHub)
python3 tools/github_core.py issues
```

### 快速恢复

如果 ECS 崩溃：

```bash
# 1. 从 GitHub 克隆代码
git clone https://github.com/realerich/marvin-backup.git
cd marvin-backup

# 2. Docker 启动
docker-compose up -d

# 3. 恢复配置
# 从备份或 Secrets 恢复 config/ 目录
```

## 扩展建议

1. **添加更多数据源**: 日历、天气、股票等
2. **增强 AI 分析**: 消息情感分析、任务优先级自动判断
3. **可视化仪表盘**: Grafana 连接 RDS 数据
4. **移动端支持**: 飞书小程序查看系统状态

---

**最后更新**: 2026-02-17
**版本**: v2.0 - 四层架构完整整合