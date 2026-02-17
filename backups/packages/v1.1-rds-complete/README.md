# Marvin 工具包

完整备份包含18个工具脚本和配置。

## 快速恢复

```bash
# 1. 解压
tar -xzf marvin-tools-*.tar.gz
cd marvin-tools-*

# 2. 恢复文件
./restore.sh

# 3. 安装依赖
./install-deps.sh

# 4. 配置API密钥
# 编辑 /root/.openclaw/workspace/config/email_config.json

# 5. 恢复cron任务（手动）
```

## 工具清单

| 工具 | 功能 |
|:---|:---|
| gaode_map.py | 高德地图API |
| restaurant_finder.py | 餐厅推荐 |
| email_tool.py | 邮件收发 |
| email_smart.py | 智能邮件分类 |
| memory_local.py | 向量语义搜索 |
| viz_tool.py | 数据可视化 |
| doc_tool.py | 文档处理 |
| webhook_tool.py | Webhook触发器 |
| system_monitor.py | 系统监控 |
| calendar_tool.py | 日历集成 |
| voice_tool.py | 语音能力 |
| workflow_engine.py | 工作流引擎 |
| browser_auto.py | 浏览器自动化 |

## 备份信息

- 备份时间: 2026-02-16 19:17:42
- 版本: 1.0
- 工具数量: 18
