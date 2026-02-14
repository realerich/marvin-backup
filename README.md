# 🤖 Marvin Backup Repository

Marvin AI 助手的完整备份仓库，包含自动化工作流、文档和配置。

## 📁 仓库结构

```
.
├── .github/
│   ├── workflows/          # GitHub Actions 工作流
│   │   ├── daily-backup.yml      # 每日自动备份 + Release
│   │   ├── backup-verify.yml     # 备份验证
│   │   ├── pages.yml             # GitHub Pages 部署
│   │   ├── auto-label.yml        # Issue/PR 自动标签
│   │   ├── code-quality.yml      # 代码质量检查
│   │   ├── auto-merge.yml        # 自动合并 PR
│   │   └── notify.yml            # 发布通知
│   ├── ISSUE_TEMPLATE/     # Issue 模板
│   └── dependabot.yml      # 依赖自动更新
├── docs/                   # 项目文档
│   ├── capability-expansion-plan.md
│   └── feishu-project-setup.md
├── memory/                 # 记忆文件
├── task_manager.py         # 任务管理系统
└── README.md              # 本文件
```

## 🚀 自动化功能

### 1. 每日自动备份
- **触发**: 每天凌晨 2 点 (UTC+8)
- **功能**: 
  - 自动提交当日变更
  - 创建版本标签 (语义化版本)
  - 生成 GitHub Release
  - 上传备份 Artifact
- **手动触发**: 支持 workflow_dispatch

### 2. GitHub Pages 文档站
- **URL**: https://realerich.github.io/marvin-backup/
- **自动部署**: docs/ 目录或 README 变更时触发
- **功能**: 现代化文档展示界面

### 3. Issue/PR 自动管理
- **自动标签**: 根据标题/内容自动打标签
- **自动分配**: 新 Issue 自动分配给维护者
- **自动评论**: Issue 创建时发送欢迎信息

### 4. 代码质量检查
- **Black**: 代码格式化检查
- **isort**: 导入排序检查
- **flake8**: 代码风格检查
- **pylint**: 静态代码分析

### 5. 依赖自动更新
- **Dependabot**: 每周一自动检查依赖更新
- **自动合并**: 安全更新自动合并

### 6. 通知系统
- **发布通知**: Release 创建时自动通知

## 🛠️ 自托管 Runner (可选)

如需在自己的服务器上运行 Actions：

```bash
# 1. 下载 runner
curl -o actions-runner-linux-x64-2.311.0.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.311.0/actions-runner-linux-x64-2.311.0.tar.gz

# 2. 解压
tar xzf actions-runner-linux-x64-2.311.0.tar.gz

# 3. 配置 (从 GitHub Settings -> Actions -> Runners 获取 token)
./config.sh --url https://github.com/realerich/marvin-backup --token <TOKEN>

# 4. 启动
./run.sh
```

## 🔐 Secrets 配置

在仓库 Settings -> Secrets -> Actions 中配置：

| Secret | 说明 |
|--------|------|
| `RDS_HOST` | 阿里云 RDS 主机地址 |
| `RDS_USER` | 数据库用户名 |
| `RDS_PASSWORD` | 数据库密码 |
| `RDS_DB` | 数据库名称 |

## 📊 任务管理

使用飞书 Bitable 管理任务，支持：
- 每日自动日报生成
- 任务状态追踪
- 优先级管理

```bash
# 生成日报
python3 task_manager.py report
```

## 📝 创建 Issue

我们提供多种 Issue 模板：

- 🐛 **Bug 报告**: 报告问题或错误
- ✨ **功能请求**: 提议新功能
- 📋 **任务**: 创建常规任务

访问 [Issues 页面](../../issues/new/choose) 使用模板。

## 🔄 版本发布

版本采用语义化版本控制 (Semantic Versioning)：

- **Major (X.0.0)**: 重大变更，不兼容更新
- **Minor (0.X.0)**: 新功能，向后兼容
- **Patch (0.0.X)**: 问题修复，向后兼容

发布自动创建，无需手动干预。

## 📞 联系方式

- **GitHub Issues**: [提交问题](../../issues)
- **Discussions**: [一般讨论](../../discussions)

---

*本仓库由 GitHub Actions 自动维护* 🤖
