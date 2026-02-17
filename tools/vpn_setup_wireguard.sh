#!/bin/bash
# WireGuard VPN 一键安装脚本
# 适用于 Debian/Ubuntu/CentOS 服务器

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 WireGuard VPN 一键安装${NC}"
echo "=============================="

# 检查root权限
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}❌ 请使用 root 权限运行${NC}"
   exit 1
fi

# 检测系统
if [[ -f /etc/debian_version ]]; then
    OS="debian"
    apt-get update
    apt-get install -y wireguard wireguard-tools qrencode
elif [[ -f /etc/redhat-release ]]; then
    OS="centos"
    yum install -y epel-release
    yum install -y wireguard-tools qrencode
else
    echo -e "${RED}❌ 不支持的操作系统${NC}"
    exit 1
fi

# 生成密钥对
echo -e "${YELLOW}🔑 生成密钥对...${NC}"
SERVER_PRIVATE_KEY=$(wg genkey)
SERVER_PUBLIC_KEY=$(echo "$SERVER_PRIVATE_KEY" | wg pubkey)
CLIENT_PRIVATE_KEY=$(wg genkey)
CLIENT_PUBLIC_KEY=$(echo "$CLIENT_PRIVATE_KEY" | wg pubkey)

# 获取默认网卡
DEFAULT_NIC=$(ip route | grep default | awk '{print $5}' | head -1)

# 选择端口
echo -e "${YELLOW}📡 选择 WireGuard 端口 (默认 51820):${NC}"
read -p "端口 [51820]: " WG_PORT
WG_PORT=${WG_PORT:-51820}

# 获取服务器IP
SERVER_IP=$(curl -s4 ifconfig.me)
echo -e "${GREEN}🌐 服务器IP: $SERVER_IP${NC}"

# 创建服务器配置
cat > /etc/wireguard/wg0.conf << EOF
[Interface]
Address = 10.200.200.1/24
ListenPort = $WG_PORT
PrivateKey = $SERVER_PRIVATE_KEY
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o $DEFAULT_NIC -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o $DEFAULT_NIC -j MASQUERADE
DNS = 8.8.8.8, 8.8.4.4

[Peer]
PublicKey = $CLIENT_PUBLIC_KEY
AllowedIPs = 10.200.200.2/32
EOF

chmod 600 /etc/wireguard/wg0.conf

# 启用IP转发
echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf
sysctl -p

# 启动WireGuard
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0

# 创建客户端配置
CLIENT_CONFIG="[Interface]
PrivateKey = $CLIENT_PRIVATE_KEY
Address = 10.200.200.2/32
DNS = 8.8.8.8, 8.8.4.4

[Peer]
PublicKey = $SERVER_PUBLIC_KEY
Endpoint = $SERVER_IP:$WG_PORT
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25"

echo -e "${GREEN}✅ WireGuard 安装完成!${NC}"
echo ""
echo -e "${YELLOW}📱 客户端配置:${NC}"
echo "=============================="
echo "$CLIENT_CONFIG"
echo ""
echo -e "${YELLOW}📋 二维码 (手机扫描):${NC}"
echo "$CLIENT_CONFIG" | qrencode -t ansiutf8
echo ""
echo -e "${GREEN}💾 客户端配置已保存到: /root/client.conf${NC}"
echo "$CLIENT_CONFIG" > /root/client.conf

echo ""
echo -e "${YELLOW}🔧 常用命令:${NC}"
echo "  查看状态: wg show"
echo "  重启服务: systemctl restart wg-quick@wg0"
echo "  停止服务: systemctl stop wg-quick@wg0"
echo "  查看日志: journalctl -u wg-quick@wg0"
echo ""
echo -e "${GREEN}🎉 安装完成! 请保存上面的配置信息${NC}"
