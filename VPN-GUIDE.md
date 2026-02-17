# 🌐 VPS + WireGuard VPN 完整部署指南

适用场景：科学上网，适配桌面(Windows/Mac/Linux)和安卓手机

---

## 1️⃣ 购买VPS

### 推荐服务商

| 服务商 | 价格 | 特点 | 推荐位置 |
|:---|:---:|:---|:---|
| **Vultr** | $5/月 | 按小时计费，IP可换 | 日本东京、新加坡 |
| **DigitalOcean** | $6/月 | 稳定性好 | 新加坡、旧金山 |
| **Linode** | $5/月 | 老牌稳定 | 日本东京 |
| **搬瓦工** | $49/年 | CN2线路，速度快 | 洛杉矶DC9 |
| **AWS Lightsail** | $5/月 | 大厂出品 | 东京、首尔 |

### 配置选择
- **系统**: Ubuntu 22.04 LTS (推荐)
- **配置**: 1核 / 512MB-1GB内存 / 25GB SSD (最便宜的就行)
- **带宽**: 1TB/月流量足够

### 购买步骤 (以Vultr为例)
1. 注册账号 vultr.com
2. 充值 $10 (支持支付宝/微信)
3. Deploy New Server
4. 选择：Cloud Compute → Tokyo → Ubuntu 22.04
5. 选 $5/月套餐，Deploy Now
6. 保存IP地址和root密码

---

## 2️⃣ 服务端安装

### 方法A：一键脚本（推荐）

```bash
# 1. 登录VPS
ssh root@你的VPS_IP

# 2. 下载并运行脚本
wget https://raw.githubusercontent.com/angristan/wireguard-install/master/wireguard-install.sh
chmod +x wireguard-install.sh
./wireguard-install.sh

# 3. 按提示选择：
# - IPv4
# - 端口 51820 (默认)
# - DNS 1.1.1.1
# - 添加第一个客户端，输入名字如 "phone"

# 4. 安装完成会显示客户端配置和二维码
```

### 方法B：手动安装（本机脚本）

```bash
# 1. 将脚本传到VPS
scp /root/.openclaw/workspace/tools/vpn_setup_wireguard.sh root@你的VPS_IP:/root/

# 2. SSH登录VPS执行
ssh root@你的VPS_IP
chmod +x vpn_setup_wireguard.sh
./vpn_setup_wireguard.sh
```

---

## 3️⃣ 客户端配置

### 📱 安卓手机

**安装APP**：
1. Google Play 搜索 "WireGuard" 安装
   - 或下载 APK: https://download.wireguard.com/android-client/

**添加配置**：
1. 打开 WireGuard App
2. 点击右下角 `+` 按钮
3. 选择 **"从二维码创建"** 或 **"从文件或压缩包创建"**
4. 扫描服务器上显示的二维码，或导入配置文件

**使用方法**：
- 点击隧道开关连接/断开
- 连接成功后状态栏显示钥匙图标🔑

### 💻 Windows 桌面

**下载安装**：
1. 官网下载: https://download.wireguard.com/windows-client/
2. 安装后右键点击托盘图标 → "Add Empty Tunnel"

**导入配置**：
- 方法1：复制服务器上的配置文本，粘贴到新建的隧道
- 方法2：保存为 `.conf` 文件，选择 "Import tunnel from file"

**激活连接**：
- 选中隧道，点击 "Activate"

### 🍎 macOS

**下载安装**：
1. App Store 搜索 "WireGuard" 安装
   - 或 Homebrew: `brew install wireguard-tools`

**导入配置**：
- 点击 "Add Tunnel" → "Add from file or archive"
- 选择配置文件或扫描二维码

### 🐧 Linux (Ubuntu/Debian)

```bash
# 安装
sudo apt install wireguard

# 保存配置文件
sudo nano /etc/wireguard/wg0.conf
# 粘贴服务器生成的配置

# 启动
sudo wg-quick up wg0

# 停止
sudo wg-quick down wg0

# 开机启动
sudo systemctl enable wg-quick@wg0
```

---

## 4️⃣ 多设备配置

一台服务器可以支持多个客户端：

```bash
# SSH到服务器
ssh root@你的VPS_IP

# 添加新客户端
./wireguard-install.sh
# 选择 "Add a new client"
# 输入设备名如 "laptop"、"ipad"

# 每个设备会生成独立配置
```

---

## 5️⃣ 优化设置

### 修改DNS为国内优化

编辑客户端配置，修改DNS行：
```
DNS = 223.5.5.5, 119.29.29.29  # 阿里DNS + 腾讯DNS
```

### 分流规则（可选）

不改全局流量，只代理特定网站：
```
# 修改客户端配置中的 AllowedIPs
# 只代理特定IP段，其他直连
AllowedIPs = 8.8.8.8/32, 1.1.1.1/32  # 只代理DNS
```

### 国内直连加速

安装 clash 或 v2ray 做分流（进阶）：
```bash
# 安装 clash
wget https://github.com/Dreamacro/clash/releases/download/v1.17.0/clash-linux-amd64-v1.17.0.gz
gunzip clash-linux-amd64-v1.17.0.gz
chmod +x clash-linux-amd64
```

---

## 6️⃣ 故障排除

### 连接不上？

```bash
# 服务器端检查
ssh root@你的VPS_IP
wg show                    # 查看连接状态
systemctl status wg-quick@wg0  # 查看服务状态

# 检查防火墙
iptables -L | grep 51820  # 确保端口开放
```

### 有连接但无法上网？

```bash
# 服务器检查IP转发
cat /proc/sys/net/ipv4/ip_forward
# 应该显示 1，如果不是：
echo 1 > /proc/sys/net/ipv4/ip_forward
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
```

### 速度慢？

1. **换服务器位置**：尝试日本、新加坡、美国西岸
2. **更换端口**：部分运营商QoS限制，换端口如 443、8080
3. **启用BBR加速**：
   ```bash
   echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
   echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
   sysctl -p
   ```

---

## 7️⃣ 安全建议

1. **定期更新系统**：
   ```bash
   apt update && apt upgrade -y
   ```

2. **修改SSH端口**（防止暴力破解）：
   ```bash
   nano /etc/ssh/sshd_config
   # 修改 Port 22 为其他端口如 2222
   systemctl restart sshd
   ```

3. **启用防火墙**（仅开放必要端口）：
   ```bash
   ufw default deny incoming
   ufw default allow outgoing
   ufw allow 51820/udp
   ufw allow 2222/tcp  # SSH端口
   ufw enable
   ```

---

## 📋 总结

**总成本**：¥25-35/月 (VPS费用)
**部署时间**：30分钟
**维护成本**：几乎为零

**优势**：
- ✅ 私人专属，不与他人共享
- ✅ WireGuard协议轻量快速
- ✅ 全平台支持
- ✅ 一键脚本，配置简单

**祝使用愉快！** 🎉
