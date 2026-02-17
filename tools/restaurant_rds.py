#!/usr/bin/env python3
"""
餐厅数据RDS工具
导入CSV、地理搜索、附近推荐
"""

import json
import csv
from datetime import datetime
from pathlib import Path
from rds_manager import RDSManager

class RestaurantRDS:
    """餐厅RDS管理"""
    
    def __init__(self):
        self.rds = RDSManager()
    
    def import_from_csv(self, csv_file):
        """从CSV导入餐厅数据"""
        imported = 0
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                with open(csv_file, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            sql = """
                            INSERT INTO restaurants 
                            (name, address, city, district, lat, lng, rating, category, tags, phone)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            ON CONFLICT DO NOTHING
                            """
                            cursor.execute(sql, (
                                row.get('店名', ''),
                                row.get('地址', ''),
                                row.get('城市', ''),
                                row.get('区域', ''),
                                float(row['纬度']) if row.get('纬度') else None,
                                float(row['经度']) if row.get('经度') else None,
                                float(row['推荐分']) if row.get('推荐分') else None,
                                row.get('类别', ''),
                                json.dumps(row.get('标签', '').split(',') if row.get('标签') else []),
                                row.get('电话', '')
                            ))
                            imported += 1
                            if imported % 10 == 0:
                                conn.commit()
                        except Exception as e:
                            print(f"⚠️ 导入失败 {row.get('店名')}: {e}")
                            continue
                
                conn.commit()
        
        return f"✅ 已导入 {imported} 家餐厅"
    
    def search_nearby(self, lat, lng, radius_km=5, limit=10):
        """搜索附近的餐厅"""
        # 使用Haversine公式计算距离 - PostgreSQL版本
        sql = """
        SELECT *, 
            (6371 * ACOS(
                COS(RADIANS(%s)) * COS(RADIANS(lat)) * 
                COS(RADIANS(lng) - RADIANS(%s)) + 
                SIN(RADIANS(%s)) * SIN(RADIANS(lat))
            )) AS distance
        FROM restaurants
        WHERE lat IS NOT NULL AND lng IS NOT NULL
        AND (6371 * ACOS(
                COS(RADIANS(%s)) * COS(RADIANS(lat)) * 
                COS(RADIANS(lng) - RADIANS(%s)) + 
                SIN(RADIANS(%s)) * SIN(RADIANS(lat))
            )) < %s
        ORDER BY distance
        LIMIT %s
        """
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, (lat, lng, lat, lat, lng, lat, radius_km, limit))
                results = cursor.fetchall()
        
        return results
    
    def search_by_city(self, city, min_rating=None, limit=20):
        """按城市搜索"""
        sql = "SELECT * FROM restaurants WHERE city = %s"
        params = [city]
        
        if min_rating:
            sql += " AND rating >= %s"
            params.append(min_rating)
        
        sql += " ORDER BY rating DESC LIMIT %s"
        params.append(limit)
        
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql, params)
                return cursor.fetchall()
    
    def get_stats(self):
        """获取统计信息"""
        with self.rds.get_connection() as conn:
            with conn.cursor() as cursor:
                # 总数
                cursor.execute("SELECT COUNT(*) as total FROM restaurants")
                total = cursor.fetchone()[0]
                
                # 按城市统计
                cursor.execute("SELECT city, COUNT(*) as count FROM restaurants GROUP BY city")
                by_city = cursor.fetchall()
                
                # 平均评分
                cursor.execute("SELECT AVG(rating) as avg_rating FROM restaurants WHERE rating > 0")
                avg_rating = cursor.fetchone()[0]
                
                return {
                    'total': total,
                    'by_city': [{'city': c[0], 'count': c[1]} for c in by_city],
                    'avg_rating': round(avg_rating, 2) if avg_rating else 0
                }
    
    def format_nearby_results(self, results):
        """格式化附近餐厅结果"""
        if not results:
            return "📭 附近没有找到餐厅"
        
        msg = f"📍 找到 {len(results)} 家附近餐厅\n"
        msg += "=" * 50 + "\n\n"
        
        # 列顺序: id, name, address, city, district, lat, lng, rating, category, tags, phone, created_at, updated_at, distance
        for r in results:
            name = r[1]
            address = r[2]
            rating = r[7]
            category = r[8]
            distance = r[13] if len(r) > 13 else 0
            msg += f"🏪 {name}\n"
            msg += f"   ⭐ {rating or 'N/A'}  📍 {distance:.2f}km\n"
            msg += f"   📍 {address or '地址未知'}\n"
            if category:
                msg += f"   🏷️ {category}\n"
            msg += "\n"
        
        return msg


def main():
    import sys
    
    tool = RestaurantRDS()
    
    if len(sys.argv) < 2:
        print("🍽️ 餐厅RDS工具")
        print("\n用法:")
        print("  python3 restaurant_rds.py import <csv文件>     # 导入CSV")
        print("  python3 restaurant_rds.py nearby <lat> <lng> [半径km]  # 附近搜索")
        print("  python3 restaurant_rds.py city <城市> [最低评分]        # 按城市搜索")
        print("  python3 restaurant_rds.py stats                         # 统计信息")
        print("\n示例:")
        print("  python3 restaurant_rds.py import restaurants.csv")
        print("  python3 restaurant_rds.py nearby 23.1291 113.2644 3")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'import':
        csv_file = sys.argv[2]
        result = tool.import_from_csv(csv_file)
        print(result)
    
    elif cmd == 'nearby':
        lat = float(sys.argv[2])
        lng = float(sys.argv[3])
        radius = float(sys.argv[4]) if len(sys.argv) > 4 else 5
        results = tool.search_nearby(lat, lng, radius)
        print(tool.format_nearby_results(results))
    
    elif cmd == 'city':
        city = sys.argv[2]
        min_rating = float(sys.argv[3]) if len(sys.argv) > 3 else None
        results = tool.search_by_city(city, min_rating)
        print(f"找到 {len(results)} 家餐厅:")
        for r in results[:10]:
            print(f"  🏪 {r['name']} ⭐{r['rating']}")
    
    elif cmd == 'stats':
        stats = tool.get_stats()
        print("📊 餐厅统计")
        print("=" * 40)
        print(f"总数量: {stats['total']}")
        print(f"平均评分: {stats['avg_rating']}")
        print("\n按城市分布:")
        for c in stats['by_city']:
            print(f"  {c['city']}: {c['count']}家")
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
