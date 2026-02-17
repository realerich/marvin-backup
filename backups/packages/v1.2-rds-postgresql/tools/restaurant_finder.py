#!/usr/bin/env python3
"""
餐厅推荐查询工具
基于高德地图坐标，提供附近餐厅推荐和导航链接
"""

import csv
import json
import math
from urllib.parse import quote

CSV_FILE = "/root/.openclaw/workspace/restaurants_full_with_coords.csv"

def load_restaurants():
    """加载餐厅数据"""
    restaurants = []
    with open(CSV_FILE, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # 只加载有坐标的
            if row.get('经度') and row.get('纬度'):
                try:
                    row['经度'] = float(row['经度'])
                    row['纬度'] = float(row['纬度'])
                    row['评分'] = float(row.get('推荐分', 0))
                    row['人均'] = int(row.get('人均', 0)) if row.get('人均') and row.get('人均').isdigit() else 0
                    restaurants.append(row)
                except:
                    continue
    return restaurants

def haversine_distance(lng1, lat1, lng2, lat2):
    """计算两点间距离（公里）"""
    R = 6371  # 地球半径
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lng = math.radians(lng2 - lng1)
    
    a = math.sin(delta_lat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lng/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def get_nearby_restaurants(user_lng, user_lat, max_distance_km=5, min_score=0, list_type=None, limit=5):
    """获取附近的餐厅"""
    restaurants = load_restaurants()
    
    # 计算距离
    for r in restaurants:
        r['距离'] = haversine_distance(user_lng, user_lat, r['经度'], r['纬度'])
    
    # 筛选
    filtered = [r for r in restaurants if r['距离'] <= max_distance_km]
    if min_score > 0:
        filtered = [r for r in filtered if r['评分'] >= min_score]
    if list_type:
        filtered = [r for r in filtered if r.get('清单') == list_type]
    
    # 按距离排序，然后按评分
    filtered.sort(key=lambda x: (x['距离'], -x['评分']))
    
    return filtered[:limit]

def get_restaurants_by_district(district, list_type=None, min_score=0, limit=10):
    """按区域获取餐厅"""
    restaurants = load_restaurants()
    
    # 筛选区域（支持模糊匹配）
    filtered = []
    for r in restaurants:
        r_area = r.get('城区', '')
        if district in r_area or r_area in district:
            filtered.append(r)
    
    if list_type:
        filtered = [r for r in filtered if r.get('清单') == list_type]
    if min_score > 0:
        filtered = [r for r in filtered if r['评分'] >= min_score]
    
    # 按评分排序
    filtered.sort(key=lambda x: -x['评分'])
    
    return filtered[:limit]

def generate_nav_link(name, lng, lat, mode='car'):
    """生成高德导航链接"""
    # 高德 URL Scheme
    # mode: car(驾车), bus(公交), ride(骑行), walk(步行)
    encoded_name = quote(name)
    return f"https://uri.amap.com/navigation?to={lng},{lat},{encoded_name}&mode={mode}&policy=1"

def format_restaurant(r, show_distance=False):
    """格式化餐厅信息"""
    info = f"📍 {r.get('店名', 'N/A')}"
    info += f" | ⭐{r['评分']:.2f}分"
    if r.get('人均', 0) > 0:
        info += f" | ¥{r['人均']}"
    info += f" | {r.get('类别', 'N/A')}"
    info += f" | {r.get('城区', 'N/A')}"
    if show_distance and '距离' in r:
        info += f" | 📏{r['距离']:.1f}km"
    return info

def recommend_by_location(location_desc, max_distance=3, list_type=None):
    """根据位置描述推荐餐厅"""
    # 常见地点坐标库（广州）
    location_coords = {
        '沙面': (113.244, 23.107),
        '上下九': (113.243, 23.115),
        '北京路': (113.272, 23.128),
        '天河城': (113.324, 23.138),
        '珠江新城': (113.324, 23.120),
        '体育西': (113.321, 23.137),
        '江南西': (113.273, 23.095),
        '东山口': (113.293, 23.130),
        '客村': (113.316, 23.100),
        '芳村': (113.209, 23.098),
        '番禺': (113.384, 22.937),
        '海珠': (113.262, 23.105),
        '荔湾': (113.226, 23.106),
        '越秀': (113.267, 23.130),
        '天河': (113.335, 23.138),
    }
    
    # 匹配位置
    matched_location = None
    for loc, coords in location_coords.items():
        if loc in location_desc or location_desc in loc:
            matched_location = (loc, coords)
            break
    
    if not matched_location:
        # 尝试按区域匹配
        for r in load_restaurants():
            district = r.get('城区', '')
            if district and (district in location_desc or location_desc in district):
                # 使用该区域的第一个餐厅坐标作为参考
                matched_location = (district, (r['经度'], r['纬度']))
                break
    
    if not matched_location:
        return None, f"未知位置: {location_desc}。支持: {', '.join(location_coords.keys())}"
    
    loc_name, (lng, lat) = matched_location
    restaurants = get_nearby_restaurants(lng, lat, max_distance_km=max_distance, list_type=list_type, limit=5)
    
    return restaurants, loc_name

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("🍽️ 餐厅推荐查询工具")
        print("\n用法:")
        print("  python3 restaurant_finder.py nearby <经度> <纬度> [距离km] [类型]")
        print("  python3 restaurant_finder.py district <区域> [类型] [最低评分]")
        print("  python3 restaurant_finder.py location <位置描述> [距离km]")
        print("  python3 restaurant_finder.py nav <店名>")
        print("\n示例:")
        print("  python3 restaurant_finder.py nearby 113.244 23.107 3 必吃")
        print("  python3 restaurant_finder.py district 荔湾 必吃 4.0")
        print("  python3 restaurant_finder.py location 北京路 2")
        print("  python3 restaurant_finder.py nav '侨美（沙面）'")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == "nearby":
        if len(sys.argv) < 4:
            print("用法: nearby <经度> <纬度> [距离km] [类型:必吃/值得试]")
            sys.exit(1)
        lng = float(sys.argv[2])
        lat = float(sys.argv[3])
        distance = float(sys.argv[4]) if len(sys.argv) > 4 else 3
        list_type = sys.argv[5] if len(sys.argv) > 5 else None
        
        restaurants = get_nearby_restaurants(lng, lat, max_distance_km=distance, list_type=list_type)
        
        print(f"📍 您当前位置 ({lng}, {lat})")
        print(f"📏 {distance}km 内找到 {len(restaurants)} 家餐厅:\n")
        for i, r in enumerate(restaurants, 1):
            print(f"{i}. {format_restaurant(r, show_distance=True)}")
            print(f"   🧭 导航: {generate_nav_link(r['店名'], r['经度'], r['纬度'])}")
            print()
    
    elif cmd == "district":
        if len(sys.argv) < 3:
            print("用法: district <区域> [类型] [最低评分]")
            sys.exit(1)
        district = sys.argv[2]
        list_type = sys.argv[3] if len(sys.argv) > 3 else None
        min_score = float(sys.argv[4]) if len(sys.argv) > 4 else 0
        
        restaurants = get_restaurants_by_district(district, list_type, min_score)
        
        type_str = f" [{list_type}]" if list_type else ""
        score_str = f" (≥{min_score}分)" if min_score > 0 else ""
        print(f"📍 {district}{type_str}{score_str} 共 {len(restaurants)} 家:\n")
        for i, r in enumerate(restaurants, 1):
            print(f"{i}. {format_restaurant(r)}")
            print(f"   🧭 导航: {generate_nav_link(r['店名'], r['经度'], r['纬度'])}")
            print()
    
    elif cmd == "location":
        if len(sys.argv) < 3:
            print("用法: location <位置描述> [距离km]")
            sys.exit(1)
        location = sys.argv[2]
        distance = float(sys.argv[3]) if len(sys.argv) > 3 else 3
        
        restaurants, loc_name = recommend_by_location(location, distance)
        
        if restaurants is None:
            print(f"❌ {loc_name}")
            sys.exit(1)
        
        print(f"📍 {loc_name} 附近 {distance}km 内推荐:\n")
        for i, r in enumerate(restaurants, 1):
            print(f"{i}. {format_restaurant(r, show_distance=True)}")
            print(f"   🧭 导航: {generate_nav_link(r['店名'], r['经度'], r['纬度'])}")
            print()
    
    elif cmd == "nav":
        if len(sys.argv) < 3:
            print("用法: nav <店名>")
            sys.exit(1)
        name = sys.argv[2]
        
        # 搜索餐厅
        restaurants = load_restaurants()
        found = [r for r in restaurants if name in r.get('店名', '')]
        
        if not found:
            print(f"❌ 未找到: {name}")
            sys.exit(1)
        
        for r in found:
            print(f"📍 {r['店名']}")
            print(f"   地址: {r.get('完整地址', 'N/A')}")
            print(f"   坐标: {r['经度']},{r['纬度']}")
            print(f"   🚗 驾车导航: {generate_nav_link(r['店名'], r['经度'], r['纬度'], 'car')}")
            print(f"   🚶 步行导航: {generate_nav_link(r['店名'], r['经度'], r['纬度'], 'walk')}")
            print(f"   🚌 公交导航: {generate_nav_link(r['店名'], r['经度'], r['纬度'], 'bus')}")
            print()
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == "__main__":
    main()
