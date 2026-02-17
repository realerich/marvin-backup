# HEARTBEAT.md

## GitHub 代码层核心（防崩溃设计）
- **仓库**: https://github.com/realerich/marvin-backup
- **状态页面**: https://realerich.github.io/marvin-backup/
- **自动同步**: 每 6 小时同步关键文件到 GitHub
- **工具**: `python3 tools/github_core.py backup` - 手动备份
- **Issues**: 自动追踪系统警报和任务

## Moltbook (每 30 分钟)
- 自动运行: `/root/.openclaw/workspace/moltbook_heartbeat.sh`
- 检查: 私信、信息流更新
- 日志: `/var/log/moltbook-heartbeat.log`

## 每日备份 (每天 03:00)
- 自动运行: `/root/marvin-backup-github/marvin_daily_backup.sh`
- 推送到 GitHub

## 任务日报 (每天 09:00)
- 生成任务报告

## 智能邮件检查 (每小时)
- 自动运行: `cd /root/.openclaw/workspace && python3 tools/email_smart.py`
- 功能:
  - 🔴 自动识别重要邮件（安全/账单/会议）
  - 🟢 过滤促销广告邮件
  - 📊 发送分类摘要报告
  - 💡 仅重要邮件立即通知

## 系统监控 (每小时)
- 自动运行: `cd /root/.openclaw/workspace && python3 tools/system_monitor.py`
- 监控: CPU、内存、磁盘、网络、OpenClaw服务状态
- 报警: 自动检测异常并通知

## 记忆系统 (已启用)
- 工具: `python3 tools/memory_local.py search <查询>`
- 功能: 向量语义搜索、关键词搜索
- 用途: 快速检索历史信息和上下文

## 日历集成 (已配置)
- 工具: `python3 tools/calendar_tool.py`
- 功能: 自然语言解析日程、创建事件、自动提醒
- 状态: 基础框架已就绪，需配置Google/飞书API

## 语音能力 (已配置)
- 工具: `python3 tools/voice_tool.py tts/stt`
- 功能: 文字转语音(TTS)、语音转文字(STT)
- 用途: 语音消息处理、语音回复

## 智能工作流 (已启用)
- 工具: `python3 tools/workflow_engine.py`
- 功能: 条件触发、多步骤自动化
- 预置模板: 邮件转日历、磁盘清理、每日汇总

## 浏览器自动化 (已配置)
- 工具: `python3 tools/browser_auto.py`
- 功能: 表单自动填写、数据抓取、页面监控
- 用途: 自动化网页操作、价格监控

## RDS数据库 (已创建)
- 工具: `python3 tools/rds_master.py`
- 功能: 餐厅数据、系统监控、邮件归档、记忆存储、Webhook日志
- 表: restaurants, system_metrics, emails, memories, webhook_logs, tasks
- 文档: `tools/RDS-README.md`
