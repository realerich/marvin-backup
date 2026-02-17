# 飞书文件推送解决方案

## 问题分析

**现状**:
- 我可以生成文件（图片、文档、数据等）
- 但无法直接通过飞书发送文件给你
- 需要你手动登录服务器下载

**根本原因**:
1. 飞书API对Bot的文件上传有严格限制
2. Bot没有自己的云盘空间
3. 需要用户先创建文件夹并分享给Bot才能操作
4. OpenClaw的message工具当前环境不支持直接发送文件附件

## 推荐解决方案

### 方案1: HTTP文件服务器（推荐）

在ECS上运行一个简单的HTTP服务器，将output目录暴露为可下载链接。

**实施步骤**:

1. **安装并启动HTTP服务器**
```bash
# 使用Python内置HTTP服务器
cd /root/.openclaw/workspace/output
python3 -m http.server 8080 --bind 0.0.0.0

# 或使用nohup后台运行
nohup python3 -m http.server 8080 --bind 0.0.0.0 > /dev/null 2>&1 &
```

2. **配置Nginx反向代理**（可选，更安全）
```nginx
server {
    listen 80;
    server_name files.your-domain.com;
    
    location / {
        alias /root/.openclaw/workspace/output/;
        autoindex on;
        autoindex_exact_size off;
        autoindex_localtime on;
    }
}
```

3. **文件推送流程**
```
生成文件 → 保存到output/ → HTTP服务器暴露 → 发送链接给你
```

**优点**:
- 简单易用
- 支持所有文件类型
- 可直接点击下载

**缺点**:
- 需要开放端口
- 需要域名或IP访问

---

### 方案2: GitHub中转

将文件上传到GitHub仓库，利用GitHub的Raw链接分享。

**已实现** ✅

```python
# 使用工具
python3 tools/feishu_push.py <文件路径> github

# 示例
python3 tools/feishu_push.py output/marvin_architecture.png github

# 输出: 
# https://github.com/realerich/marvin-backup/blob/main/output/marvin_architecture.png
```

**优点**:
- 无需额外服务器
- 版本控制
- 永久链接

**缺点**:
- 大文件有限制(100MB)
- 需要git提交
- 私密文件不适合

---

### 方案3: 转为飞书文档

将文本内容转为飞书云文档直接分享。

**适用场景**: 文本报告、数据分析、日志

**待实现**: 需要飞书API权限配置

---

### 方案4: 邮件发送

作为备选方案，发送到你的邮箱。

**已配置** ✅

```python
from email_tool import send_email

send_email(
    to="liuky.personal@gmail.com",
    subject="文件: 架构图",
    body="请查看附件",
    attachments=["output/marvin_architecture.png"]
)
```

---

## 实施建议

### 短期方案（立即可用）

**组合使用**: GitHub + 邮件

1. 小文件/图片 → GitHub中转
2. 大文件/私密文件 → 邮件发送
3. 文本内容 → 直接发送摘要

**自动推送脚本**:
```bash
#!/bin/bash
# 文件生成后自动推送

FILE=$1
FILENAME=$(basename $FILE)

# 上传到GitHub
cd /root/.openclaw/workspace
cp $FILE output/
git add output/$FILENAME
git commit -m "添加文件: $FILENAME"
git push github main

# 生成链接
URL="https://github.com/realerich/marvin-backup/blob/main/output/$FILENAME"
echo "文件已上传: $URL"
```

### 长期方案（推荐）

**搭建HTTP文件服务器**:

1. 购买一个便宜域名（如 `marvin-files.liuky.net`）
2. 配置DNS指向ECS
3. 使用Nginx提供文件服务
4. 添加基础认证保护

**架构**:
```
用户请求文件
    ↓
域名 → Nginx (80/443)
    ↓
认证检查
    ↓
静态文件服务 (/root/.openclaw/workspace/output/)
    ↓
文件下载
```

---

## 当前可用的推送方式

### 方式1: GitHub链接（已实现）
```bash
python3 tools/feishu_push.py output/文件.png github
```

### 方式2: 发送文件摘要（已实现）
```bash
python3 tools/feishu_push.py output/文件.txt summary
```

### 方式3: SCP下载（手动）
```bash
# 在你的本地电脑执行
scp root@your-server-ip:/root/.openclaw/workspace/output/文件.png ./
```

---

## 下一步行动

请选择你要实施的方案：

1. **立即使用GitHub方案** - 无需额外配置
2. **搭建HTTP文件服务器** - 需要域名和Nginx配置
3. **配置邮件自动发送** - 已可用，适合私密文件

建议先用方案1（GitHub）过渡，同时准备方案2（HTTP服务器）作为长期解决方案。

---

*文档更新时间: 2026-02-17 09:15*