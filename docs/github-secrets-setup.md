# GitHub Secrets 配置指南

## 需要配置的Secrets

在你的GitHub仓库设置中添加以下Secrets：

| Secret名称 | 值 | 说明 |
|-----------|-----|------|
| `RDS_HOST` | `pgm-j6c0rrysy447d8tc.pg.rds.aliyuncs.com` | RDS地址 |
| `RDS_PORT` | `5432` | 数据库端口 |
| `RDS_DB` | `marvin_db` | 数据库名 |
| `RDS_USER` | `marvin` | 数据库用户名 |
| `RDS_PASSWORD` | `Crimson@13` | 数据库密码 |

## 配置步骤

1. 访问 GitHub仓库 → Settings → Secrets and variables → Actions
2. 点击 "New repository secret"
3. 依次添加上述5个Secrets

## 本地服务器环境变量

SSH登录服务器，执行：
```bash
echo 'export RDS_HOST="pgm-j6c0rrysy447d8tc.pg.rds.aliyuncs.com"' >> ~/.bashrc
echo 'export RDS_PORT="5432"' >> ~/.bashrc
echo 'export RDS_DB="marvin_db"' >> ~/.bashrc
echo 'export RDS_USER="marvin"' >> ~/.bashrc
echo 'export RDS_PASSWORD="Crimson@13"' >> ~/.bashrc
source ~/.bashrc
```

## 验证配置

```bash
cd /root/.openclaw/workspace
python3 marvin_db.py
```

## GitHub Actions功能

配置完成后，GitHub Actions将自动：
- ✅ 每天凌晨4点验证RDS连接
- ✅ 自动导出数据库备份
- ✅ 保留7天备份文件
