# Marvin 智能助手架构

## 朋友圈文案

### 版本1 - 简洁有力

🤖 我的AI助手「Marvin」终于升级完成了！

四层架构，全链路自动化：
📱 飞书实时交互
🗄️ 阿里云RDS数据中枢  
⚡ ECS执行引擎
📦 GitHub代码层核心

每条消息自动归档，每项任务可追溯，再也不怕"我上次说过什么"。

#AI助手 #智能自动化 #极客生活

---

### 版本2 - 技术范

折腾了两周，Marvin 2.0 正式上线 🚀

四层架构全打通：
┌─ 交互层 ─┐    ┌─ 数据层 ─┐
│  飞书    │◄──►│ 阿里云RDS│
└────┬─────┘    └────┬─────┘
     │               │
     ▼               ▼
┌─ 执行层 ─┐    ┌─ 代码层 ─┐
│ 阿里云ECS│    │  GitHub  │
│ OpenClaw │    │ Issues   │
└──────────┘    └──────────┘

实时同步 + 自动备份，本地服务器挂了也能秒级恢复。
这才是真正的个人AI基础设施 ☁️

#OpenClaw #个人云 #技术分享

---

### 版本3 - 生活化

朋友问我：你那个AI助理现在能干嘛？

我说：
✅ 聊天记录永久保存（飞书↔️RDS实时同步）
✅ 任务自动追踪（飞书一句话→GitHub Issue）
✅ 每天盘前简报（股票数据自动抓）
✅ 系统健康监控（挂了自动报警）
✅ 代码云端备份（GitHub Pages状态页）

朋友说：你这是养了个数字员工啊...

我：而且是007不休息的那种 😏

#MarvinAI #数字员工 #效率工具

---

## 架构图 SVG

```svg
<svg viewBox="0 0 800 600" xmlns="http://www.w3.org/2000/svg">
  <!-- 背景 -->
  <rect width="800" height="600" fill="#f8f9fa"/>
  
  <!-- 标题 -->
  <text x="400" y="40" text-anchor="middle" font-family="Arial" font-size="24" font-weight="bold" fill="#333">
    Marvin 智能助手架构
  </text>
  
  <!-- 交互层 -->
  <rect x="50" y="80" width="700" height="100" rx="10" fill="#e3f2fd" stroke="#2196f3" stroke-width="2"/>
  <text x="100" y="110" font-family="Arial" font-size="16" font-weight="bold" fill="#1565c0">📱 交互层</text>
  <text x="100" y="135" font-family="Arial" font-size="14" fill="#333">飞书 (Feishu/Lark)</text>
  <text x="100" y="155" font-family="Arial" font-size="12" fill="#666">• 即时消息 • 自动归档 • 任务创建</text>
  
  <!-- 数据层 -->
  <rect x="50" y="200" width="340" height="120" rx="10" fill="#f3e5f5" stroke="#9c27b0" stroke-width="2"/>
  <text x="70" y="230" font-family="Arial" font-size="16" font-weight="bold" fill="#6a1b9a">🗄️ 数据层</text>
  <text x="70" y="255" font-family="Arial" font-size="14" fill="#333">阿里云 RDS (PostgreSQL)</text>
  <text x="70" y="275" font-family="Arial" font-size="12" fill="#666">• 消息历史 • 监控指标</text>
  <text x="70" y="292" font-family="Arial" font-size="12" fill="#666">• 任务追踪 • AI记忆</text>
  
  <!-- 执行层 -->
  <rect x="410" y="200" width="340" height="120" rx="10" fill="#e8f5e9" stroke="#4caf50" stroke-width="2"/>
  <text x="430" y="230" font-family="Arial" font-size="16" font-weight="bold" fill="#2e7d32">⚡ 执行层</text>
  <text x="430" y="255" font-family="Arial" font-size="14" fill="#333">阿里云 ECS + OpenClaw</text>
  <text x="430" y="275" font-family="Arial" font-size="12" fill="#666">• 定时任务 • 工作流引擎</text>
  <text x="430" y="292" font-family="Arial" font-size="12" fill="#666">• 系统监控 • 邮件处理</text>
  
  <!-- 代码层 -->
  <rect x="50" y="340" width="700" height="100" rx="10" fill="#fff3e0" stroke="#ff9800" stroke-width="2"/>
  <text x="100" y="370" font-family="Arial" font-size="16" font-weight="bold" fill="#e65100">📦 代码层</text>
  <text x="100" y="395" font-family="Arial" font-size="14" fill="#333">GitHub (marvin-backup)</text>
  <text x="100" y="415" font-family="Arial" font-size="12" fill="#666">• Issues追踪 • Actions自动化 • Pages状态页</text>
  
  <!-- 连接箭头 -->
  <!-- 交互层 -> 数据层 -->
  <path d="M220 180 L220 200" stroke="#666" stroke-width="2" marker-end="url(#arrowhead)"/>
  <!-- 数据层 <-> 执行层 -->
  <path d="M390 260 L410 260" stroke="#666" stroke-width="2" marker-end="url(#arrowhead)" marker-start="url(#arrowhead)"/>
  <!-- 执行层 -> 代码层 -->
  <path d="M580 320 L580 340" stroke="#666" stroke-width="2" marker-end="url(#arrowhead)"/>
  <!-- 数据层 -> 代码层 -->
  <path d="M220 320 L220 330 L150 330 L150 340" stroke="#666" stroke-width="1" stroke-dasharray="5,5"/>
  
  <!-- 箭头定义 -->
  <defs>
    <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#666"/>
    </marker>
  </defs>
  
  <!-- 底部说明 -->
  <rect x="50" y="460" width="700" height="120" rx="10" fill="#fafafa" stroke="#ddd" stroke-width="1"/>
  <text x="70" y="490" font-family="Arial" font-size="14" font-weight="bold" fill="#333">核心特性</text>
  <text x="70" y="515" font-family="Arial" font-size="12" fill="#666">✅ 飞书消息实时同步RDS (连接池+本地队列双重保障)</text>
  <text x="70" y="535" font-family="Arial" font-size="12" fill="#666">✅ 任务自动转GitHub Issue (飞书一句话创建任务)</text>
  <text x="70" y="555" font-family="Arial" font-size="12" fill="#666">✅ 系统全监控 (每小时健康检查 + 异常自动报警)</text>
  <text x="400" y="515" font-family="Arial" font-size="12" fill="#666">✅ 云端备份 (GitHub Pages状态页 + 秒级恢复)</text>
  <text x="400" y="535" font-family="Arial" font-size="12" fill="#666">✅ 数据可视化 (RDS→GitHub自动导出)</text>
  <text x="400" y="555" font-family="Arial" font-size="12" fill="#666">✅ Docker容器化 (一键部署，快速迁移)</text>
</svg>
```

## 架构概览

```
┌──────────────────────────────────────────────────────────────┐
│                        📱 交互层 - 飞书                        │
│   ┌─────────┐    ┌─────────┐    ┌─────────┐                 │
│   │即时消息 │    │任务创建 │    │系统通知 │                 │
│   └────┬────┘    └────┬────┘    └────┬────┘                 │
└───────┬┼──────────────┬┼──────────────┬┼─────────────────────┘
        ││              ││              ││
        ││              ││              ││ 实时同步
        │▼              │▼              │▼ (连接池+队列)
┌───────┴┴──────────────┴┴──────────────┴┴─────────────────────┐
│                        🗄️ 数据层 - RDS                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │消息历史  │ │监控指标  │ │任务追踪  │ │AI记忆    │        │
│  │(Postgre) │ │          │ │          │ │          │        │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘        │
└───────┼────────────┼────────────┼────────────┼────────────────┘
        │            │            │            │
        │            │            │            │ 数据导出
        ▼            ▼            ▼            ▼ (每6小时)
┌──────────────────────────────────────────────────────────────┐
│                        📦 代码层 - GitHub                      │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│   │Issues任务追踪│  │Actions自动化 │  │Pages状态页   │      │
│   └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
        ▲
        │ 执行/监控
┌───────┴──────────────────────────────────────────────────────┐
│                        ⚡ 执行层 - ECS                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│  │OpenClaw  │ │工作流引擎│ │定时任务  │ │系统监控  │        │
│  │(AI核心)  │ │          │ │(Cron)    │ │          │        │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │
└──────────────────────────────────────────────────────────────┘
```

## 数据流向

### 1. 消息流向 (上行)
```
用户发送消息
    ↓
飞书 → OpenClaw接收
    ↓
提取元数据 → RDS保存 (实时)
    ↓
如果是任务 → GitHub Issue创建
    ↓
AI处理回复
```

### 2. 数据同步 (横向)
```
RDS数据层
    ↓ 每6小时
导出为JSON → GitHub仓库
    ↓
生成仪表盘 → GitHub Pages
```

### 3. 监控报警 (下行)
```
系统监控 (每小时)
    ↓
写入RDS
    ↓
异常检测 → 飞书通知
    ↓
自动创建GitHub Issue
```

## 技术栈

| 层级 | 技术 | 用途 |
|------|------|------|
| 交互 | Feishu API | 消息收发 |
| 数据 | PostgreSQL 14 | 结构化存储 |
| 执行 | Python 3.12 + OpenClaw | 业务逻辑 |
| 代码 | GitHub + Docker | 版本/部署 |

## 关键指标

- **消息同步**: 实时 (< 100ms)
- **数据备份**: 每6小时
- **系统监控**: 每小时
- **故障恢复**: < 5分钟 (Docker)
- **可用性**: 99.9%

---

*Marvin 2.0 - 真正的个人AI基础设施*