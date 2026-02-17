#!/bin/bash
# 高德地图 API 工具脚本
# Usage: ./gaode_map.sh <command> [args]

KEY="cc5130adf53b9696f8eef9444eeb6845"
BASE_URL="https://restapi.amap.com/v3"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

show_help() {
    echo "高德地图 API 工具"
    echo ""
    echo "用法:"
    echo "  $0 ip                    # IP 定位"
    echo "  $0 geo <地址>            # 地理编码 (地址→坐标)"
    echo "  $0 regeo <经度> <纬度>   # 逆地理编码 (坐标→地址)"
    echo "  $0 nearby <关键词> <城市> # 周边搜索"
    echo "  $0 route <起点> <终点>   # 驾车路线规划"
    echo "  $0 weather <城市>        # 实时天气"
    echo ""
    echo "示例:"
    echo "  $0 geo '广州市天河区珠江新城'"
    echo "  $0 nearby 餐厅 广州"
    echo "  $0 route '天河城' '北京路'"
}

# IP 定位
cmd_ip() {
    echo -e "${YELLOW}正在获取 IP 定位...${NC}"
    curl -s "${BASE_URL}/ip?key=${KEY}" | python3 -m json.tool 2>/dev/null || curl -s "${BASE_URL}/ip?key=${KEY}"
}

# 地理编码 (地址→坐标)
cmd_geo() {
    local address="$1"
    if [ -z "$address" ]; then
        echo "错误: 请提供地址"
        echo "用法: $0 geo '广州市天河区'"
        exit 1
    fi
    
    echo -e "${YELLOW}正在解析地址: $address${NC}"
    local encoded_address=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$address'))" 2>/dev/null || echo "$address")
    
    curl -s "${BASE_URL}/geocode/geo?address=${encoded_address}&key=${KEY}" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('status') == '1' and data.get('geocodes'):
    for item in data['geocodes'][:3]:
        print(f\"📍 {item.get('formatted_address', 'N/A')}\")
        print(f\"   坐标: {item.get('location', 'N/A')}\")
        print(f\"   行政区: {item.get('province', '')} {item.get('city', '')} {item.get('district', '')}\")
        print()
else:
    print('未找到结果或出错:', data.get('info', 'Unknown'))
"
}

# 逆地理编码 (坐标→地址)
cmd_regeo() {
    local lng="$1"
    local lat="$2"
    
    if [ -z "$lng" ] || [ -z "$lat" ]; then
        echo "错误: 请提供经纬度"
        echo "用法: $0 regeo 113.3245 23.1064"
        exit 1
    fi
    
    echo -e "${YELLOW}正在解析坐标: $lng,$lat${NC}"
    curl -s "${BASE_URL}/geocode/regeo?output=json&location=${lng},${lat}&key=${KEY}&extensions=all" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('status') == '1':
    regeo = data.get('regeocode', {})
    print(f\"📍 {regeo.get('formatted_address', 'N/A')}\")
    addr = regeo.get('addressComponent', {})
    print(f\"   省/市/区: {addr.get('province', '')} {addr.get('city', '')} {addr.get('district', '')}\")
    print(f\"   街道: {addr.get('street', '')} {addr.get('streetNumber', '')}\")
    print(f\"   商圈: {', '.join(addr.get('businessAreas', [])[:3])}\")
else:
    print('未找到结果或出错:', data.get('info', 'Unknown'))
"
}

# 周边搜索
cmd_nearby() {
    local keyword="$1"
    local city="${2:-广州}"
    
    if [ -z "$keyword" ]; then
        echo "错误: 请提供搜索关键词"
        echo "用法: $0 nearby 餐厅 广州"
        exit 1
    fi
    
    echo -e "${YELLOW}正在搜索: $keyword (城市: $city)${NC}"
    local encoded_kw=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$keyword'))" 2>/dev/null || echo "$keyword")
    local encoded_city=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$city'))" 2>/dev/null || echo "$city")
    
    curl -s "${BASE_URL}/place/text?keywords=${encoded_kw}&city=${encoded_city}&offset=10&page=1&key=${KEY}&extensions=all" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('status') == '1' and data.get('pois'):
    print(f\"找到 {len(data['pois'])} 个结果:\")
    for i, poi in enumerate(data['pois'][:10], 1):
        print(f\"{i}. {poi.get('name', 'N/A')}\")
        print(f\"   📍 {poi.get('address', 'N/A')}\")
        print(f\"   🏷️ 类型: {poi.get('type', 'N/A')}\")
        print(f\"   📞 电话: {poi.get('tel', 'N/A')}\")
        print(f\"   ⭐ 评分: {poi.get('biz_ext', {}).get('rating', 'N/A')}\")
        print()
else:
    print('未找到结果:', data.get('info', 'Unknown'))
"
}

# 驾车路线规划
cmd_route() {
    local origin="$1"
    local destination="$2"
    
    if [ -z "$origin" ] || [ -z "$destination" ]; then
        echo "错误: 请提供起点和终点"
        echo "用法: $0 route '天河城' '北京路'"
        exit 1
    fi
    
    echo -e "${YELLOW}正在规划路线: $origin → $destination${NC}"
    
    # 先获取起点和终点的坐标
    local orig_loc=$(curl -s "${BASE_URL}/geocode/geo?address=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$origin'))")&key=${KEY}" | python3 -c "import json, sys; d=json.load(sys.stdin); print(d['geocodes'][0]['location'] if d.get('geocodes') else '')")
    local dest_loc=$(curl -s "${BASE_URL}/geocode/geo?address=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$destination'))")&key=${KEY}" | python3 -c "import json, sys; d=json.load(sys.stdin); print(d['geocodes'][0]['location'] if d.get('geocodes') else '')")
    
    if [ -z "$orig_loc" ] || [ -z "$dest_loc" ]; then
        echo "无法获取起点或终点坐标"
        exit 1
    fi
    
    curl -s "${BASE_URL}/direction/driving?origin=${orig_loc}&destination=${dest_loc}&key=${KEY}&extensions=all" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('status') == '1' and data.get('route', {}).get('paths'):
    route = data['route']
    print(f\"🚗 路线规划: {route.get('origin', 'N/A')} → {route.get('destination', 'N/A')}\")
    for i, path in enumerate(route['paths'][:3], 1):
        print(f\"\\n方案 {i}:\")
        print(f\"   距离: {int(path.get('distance', 0))/1000:.1f} 公里\")
        print(f\"   预计时间: {int(path.get('duration', 0))/60:.0f} 分钟\")
        print(f\"   红绿灯: {path.get('traffic_lights', 'N/A')} 个\")
        print(f\"   过路费: ¥{path.get('tolls', 'N/A')}\")
        steps = path.get('steps', [])
        if steps:
            print(f\"   主要路段: {' → '.join([s.get('road', 'N/A') for s in steps[:5]])}\")
else:
    print('路线规划失败:', data.get('info', 'Unknown'))
"
}

# 天气查询
cmd_weather() {
    local city="${1:-广州}"
    
    echo -e "${YELLOW}正在查询 $city 天气...${NC}"
    local encoded_city=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$city'))" 2>/dev/null || echo "$city")
    
    curl -s "${BASE_URL}/weather/weatherInfo?city=${encoded_city}&key=${KEY}&extensions=all" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('status') == '1' and data.get('forecasts'):
    forecast = data['forecasts'][0]
    print(f\"🌤️ {forecast.get('city', 'N/A')} 天气预报\")
    print(f\"发布: {forecast.get('reporttime', 'N/A')}\")
    print()
    for day in forecast.get('casts', [])[:3]:
        print(f\"📅 {day.get('date', 'N/A')} ({day.get('week', 'N/A')})\")
        print(f\"   白天: {day.get('dayweather', 'N/A')} {day.get('daytemp', 'N/A')}°C {day.get('daywind', 'N/A')}风{day.get('daypower', 'N/A')}\")
        print(f\"   夜间: {day.get('nightweather', 'N/A')} {day.get('nighttemp', 'N/A')}°C\")
        print()
else:
    print('查询失败:', data.get('info', 'Unknown'))
"
}

# 主命令分发
case "$1" in
    ip)
        cmd_ip
        ;;
    geo)
        cmd_geo "$2"
        ;;
    regeo)
        cmd_regeo "$2" "$3"
        ;;
    nearby)
        cmd_nearby "$2" "$3"
        ;;
    route)
        cmd_route "$2" "$3"
        ;;
    weather)
        cmd_weather "$2"
        ;;
    *)
        show_help
        ;;
esac
