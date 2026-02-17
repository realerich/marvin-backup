# 🔐 关键基础设施配置

**重要**: 此文件包含所有关键系统配置，必须确保备份和安全。

---

## 🗄️ RDS PostgreSQL 数据库

| 配置项 | 值 |
|:---|:---|
| **主机** | pgm-j6c0rrysy447d8tc.pg.rds.aliyuncs.com |
| **端口** | 5432 |
| **数据库** | marvin_db |
| **用户名** | marvin |
| **密码** | Crimson@13 |
| **类型** | PostgreSQL 14.20 |
| **配置位置** | /root/.openclaw/workspace/config/rds_config.json |

**已创建的表**:
- `restaurants` - 65家餐厅数据
- `system_metrics` - 系统监控指标
- `emails` - 邮件归档
- `memories` - 记忆存储
- `webhook_logs` - Webhook日志
- `tasks` - 任务管理

**连接测试**:
```bash
cd /root/.openclaw/workspace && python3 tools/rds_manager.py test
```

---

## 📧 邮件系统

### Gmail 配置
| 配置项 | 值 |
|:---|:---|
| **邮箱** | liuky.personal@gmail.com |
| **应用密码** | ozbhujwthkzcovwi |
| **配置位置** | /root/.openclaw/workspace/config/email_config.json |

### Cloudflare Email 路由
| 配置项 | 值 |
|:---|:---|
| **域名** | liuky.net |
| **收件邮箱** | me@liuky.net |
| **转发目标** | liuky.personal@gmail.com |

---

## 🗺️ 地图服务

### 高德/AMap API
| 配置项 | 值 |
|:---|:---|
| **API Key** | cc5130adf53b9696f8eef9444eeb6845 |
| **用途** | 地理编码、POI搜索、路线规划 |
| **配置位置** | /root/.openclaw/workspace/tools/gaode_map.sh |

---

## 💾 备份系统

### 本地备份
| 配置项 | 值 |
|:---|:---|
| **备份目录** | /root/.openclaw/workspace/backups/packages/ |
| **最新备份** | v1.2-rds-postgresql.tar.gz |
| **一键恢复** | ./marvin-restore.sh |
| **恢复工具** | /root/.openclaw/workspace/tools/restore_tools.py |

### GitHub 备份
| 配置项 | 值 |
|:---|:---|
| **脚本** | /root/marvin-backup-github/marvin_daily_backup.sh |
| **定时** | 每天 03:00 |
| **目标仓库** | marvin-backup |

---

## ⏰ 定时任务 (Cron)

| 任务 | 频率 | 功能 |
|:---|:---:|:---|
| Moltbook心跳 | 30分钟 | 检查私信、信息流 |
| 智能邮件检查 | 每小时 | 分类邮件、发送摘要 |
| 系统监控 | 每小时 | CPU/内存/磁盘监控 |
| 每日备份 | 03:00 | GitHub备份 |
| 任务日报 | 09:00 | 生成任务报告 |

---

## 🔧 工具套件 (28个)

**位置**: /root/.openclaw/workspace/tools/

### 核心工具
| 工具 | 功能 |
|:---|:---|
| rds_manager.py | RDS连接管理 |
| rds_master.py | RDS综合入口 |
| system_monitor.py | 系统监控 |

### 数据工具
| 工具 | 功能 |
|:---|:---|
| restaurant_rds.py | 餐厅数据管理 |
| metrics_rds.py | 监控指标存储 |
| email_rds.py | 邮件归档 |
| memory_rds.py | 记忆存储 |
| webhook_rds.py | Webhook日志 |

### 邮件工具
| 工具 | 功能 |
|:---|:---|
| email_tool.py | 邮件收发 |
| email_smart.py | 智能分类 |
| email_cleaner.py | 邮件清理 |

### 其他工具
| 工具 | 功能 |
|:---|:---|
| gaode_map.py | 高德地图API |
| viz_tool.py | 数据可视化 |
| doc_tool.py | 文档处理 |
| webhook_tool.py | Webhook触发器 |
| workflow_engine.py | 工作流引擎 |
| backup_tools.py | 备份工具 |
| restore_tools.py | 恢复工具 |

---

## 📝 配置文件位置

```
/root/.openclaw/workspace/
├── config/
│   ├── rds_config.json          # RDS连接信息
│   ├── email_config.json        # 邮箱配置
│   ├── webhooks.json           # Webhook配置
│   └── monitor_config.json     # 监控阈值
├── memory/
│   └── 2026-02-16.md           # 每日记忆
├── HEARTBEAT.md                # 心跳配置
├── MEMORY.md                   # 长期记忆
└── INFRASTRUCTURE.md           # 本文件
```

---

## 🔄 恢复流程

如果系统崩溃:

```bash
# 1. 解压备份
tar -xzf v1.2-rds-postgresql.tar.gz
cd v1.2-rds-postgresql

# 2. 恢复文件
./restore.sh

# 3. 安装依赖
./install-deps.sh
pip3 install psycopg2-binary --break-system-packages

# 4. 验证连接
python3 tools/rds_manager.py test
```

---

## ⚠️ 重要提醒

1. **永远不要删除此文件**
2. **定期备份到安全位置**
3. **更新配置后同步更新此文件**
4. **RDS密码不要泄露**

**最后更新**: 2026-02-16
