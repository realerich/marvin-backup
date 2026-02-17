#!/usr/bin/env python3
"""
高德地图 API Python 工具
用于餐厅位置解析和地理分析
"""

import requests
import json
import csv
import time
from urllib.parse import quote

KEY = "cc5130adf53b9696f8eef9444eeb6845"
BASE_URL = "https://restapi.amap.com/v3"

class GaodeMap:
    def __init__(self, api_key=KEY):
        self.key = api_key
        self.session = requests.Session()
    
    def geocode(self, address, city=None):
        """地理编码: 地址 → 坐标"""
        url = f"{BASE_URL}/geocode/geo"
        params = {
            "key": self.key,
            "address": address,
            "output": "json"
        }
        if city:
            params["city"] = city
        
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            
            if data.get("status") == "1" and data.get("geocodes"):
                result = data["geocodes"][0]
                return {
                    "success": True,
                    "address": result.get("formatted_address"),
                    "location": result.get("location"),  # "lng,lat"
                    "province": result.get("province"),
                    "city": result.get("city"),
                    "district": result.get("district"),
                    "adcode": result.get("adcode")
                }
            return {"success": False, "error": data.get("info", "未知错误")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def regeocode(self, lng, lat):
        """逆地理编码: 坐标 → 地址"""
        url = f"{BASE_URL}/geocode/regeo"
        params = {
            "key": self.key,
            "location": f"{lng},{lat}",
            "extensions": "all",
            "output": "json"
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            
            if data.get("status") == "1":
                regeo = data.get("regeocode", {})
                addr = regeo.get("addressComponent", {})
                return {
                    "success": True,
                    "formatted_address": regeo.get("formatted_address"),
                    "province": addr.get("province"),
                    "city": addr.get("city"),
                    "district": addr.get("district"),
                    "street": addr.get("street"),
                    "pois": [p.get("name") for p in regeo.get("pois", [])[:5]]
                }
            return {"success": False, "error": data.get("info")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def search_poi(self, keywords, city="广州", page=1):
        """POI 搜索"""
        url = f"{BASE_URL}/place/text"
        params = {
            "key": self.key,
            "keywords": keywords,
            "city": city,
            "offset": 10,
            "page": page,
            "extensions": "all",
            "output": "json"
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            
            if data.get("status") == "1":
                pois = []
                for poi in data.get("pois", []):
                    pois.append({
                        "name": poi.get("name"),
                        "address": poi.get("address"),
                        "location": poi.get("location"),
                        "tel": poi.get("tel"),
                        "type": poi.get("type"),
                        "rating": poi.get("biz_ext", {}).get("rating")
                    })
                return {"success": True, "count": data.get("count"), "pois": pois}
            return {"success": False, "error": data.get("info")}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def driving_route(self, origin, destination):
        """驾车路线规划"""
        # 先解析起点和终点
        orig_geo = self.geocode(origin)
        dest_geo = self.geocode(destination)
        
        if not orig_geo["success"] or not dest_geo["success"]:
            return {"success": False, "error": "无法解析起点或终点"}
        
        url = f"{BASE_URL}/direction/driving"
        params = {
            "key": self.key,
            "origin": orig_geo["location"],
            "destination": dest_geo["location"],
            "extensions": "all"
        }
        
        try:
            resp = self.session.get(url, params=params, timeout=10)
            data = resp.json()
            
            if data.get("status") == "1" and data.get("route", {}).get("paths"):
                path = data["route"]["paths"][0]
                return {
                    "success": True,
                    "origin": origin,
                    "destination": destination,
                    "distance": int(path.get("distance", 0)),  # 米
                    "duration": int(path.get("duration", 0)),  # 秒
                    "tolls": path.get("tolls"),
                    "traffic_lights": path.get("traffic_lights")
                }
            return {"success": False, "error": data.get("info")}
        except Exception as e:
            return {"success": False, "error": str(e)}


def batch_geocode_restaurants(csv_file):
    """批量解析餐厅地址获取坐标"""
    gaode = GaodeMap()
    
    results = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        restaurants = list(reader)
    
    print(f"开始批量解析 {len(restaurants)} 家餐厅...")
    
    for i, r in enumerate(restaurants, 1):
        name = r.get('店名', '')
        district = r.get('城区', '')
        
        # 构建搜索地址
        address = f"广州市{district}{name}"
        
        result = gaode.geocode(address)
        if result["success"]:
            r['经度'] = result['location'].split(',')[0]
            r['纬度'] = result['location'].split(',')[1]
            r['完整地址'] = result['address']
            print(f"✅ {i}/{len(restaurants)} {name}: {result['location']}")
        else:
            r['经度'] = ''
            r['纬度'] = ''
            r['完整地址'] = ''
            print(f"❌ {i}/{len(restaurants)} {name}: 解析失败 - {result.get('error')}")
        
        # 避免请求过快
        time.sleep(0.2)
    
    # 保存结果
    output_file = csv_file.replace('.csv', '_with_coords.csv')
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = list(restaurants[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(restaurants)
    
    print(f"\n完成！已保存到: {output_file}")
    return output_file


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("高德地图 API 工具")
        print("\n用法:")
        print("  python3 gaode_map.py geo <地址> [城市]")
        print("  python3 gaode_map.py regeo <经度> <纬度>")
        print("  python3 gaode_map.py search <关键词> [城市]")
        print("  python3 gaode_map.py route <起点> <终点>")
        print("  python3 gaode_map.py batch <csv文件>")
        print("\n示例:")
        print("  python3 gaode_map.py geo '沙面侨美' 广州")
        print("  python3 gaode_map.py batch restaurants_full.csv")
        sys.exit(1)
    
    gaode = GaodeMap()
    cmd = sys.argv[1]
    
    if cmd == "geo":
        result = gaode.geocode(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "regeo":
        result = gaode.regeocode(sys.argv[2], sys.argv[3])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "search":
        result = gaode.search_poi(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "广州")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "route":
        if len(sys.argv) < 4:
            print("用法: route <起点> <终点>")
            sys.exit(1)
        result = gaode.driving_route(sys.argv[2], sys.argv[3])
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    elif cmd == "batch":
        if len(sys.argv) < 3:
            print("用法: batch <csv文件>")
            sys.exit(1)
        batch_geocode_restaurants(sys.argv[2])
    
    else:
        print(f"未知命令: {cmd}")
