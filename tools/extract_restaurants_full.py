# OCR 餐厅清单完整数据提取脚本
"""
从 NAV广佛必吃清单 图片中提取全部65家餐厅数据
"""

import pytesseract
from PIL import Image
import re
import json
import csv

def extract_all_restaurants(image_path):
    """提取全部餐厅数据"""
    img = Image.open(image_path)
    
    # 使用表格优化配置
    custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
    text = pytesseract.image_to_string(img, lang='chi_sim+eng', config=custom_config)
    
    lines = text.split('\n')
    
    # 两个清单的数据
    must_eat = []      # 必吃清单
    worth_trying = []  # 值得试清单
    
    current_section = None
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # 识别清单标题
        if '必吃清单' in line or '必吃' in line:
            current_section = 'must_eat'
            continue
        elif '值得试' in line or '值得试清单' in line:
            current_section = 'worth_trying'
            continue
        
        # 跳过表头行
        if any(kw in line for kw in ['序号', '店名', '推荐', '定位', '城区', '类别']):
            continue
            
        # 解析餐厅数据行
        # 格式: 序号 店名 老字号 定位 城区 类别 茶市/饭市 人均 口味 服务 环境 稳定度
        parts = re.split(r'\s+', line)
        
        if len(parts) >= 3:
            try:
                # 尝试解析序号（数字开头）
                rank = int(parts[0])
                
                # 查找评分（通常是 x.x 或 x.xx 格式）
                score = None
                score_idx = -1
                for i, p in enumerate(parts):
                    if re.match(r'^\d+\.\d+$', p):
                        score = float(p)
                        score_idx = i
                        break
                
                if score and current_section:
                    # 店名通常在序号之后、评分之前
                    name_parts = parts[1:score_idx] if score_idx > 1 else [parts[1] if len(parts) > 1 else '未知']
                    name = ' '.join(name_parts)
                    
                    # 提取其他字段
                    district = parts[score_idx + 2] if len(parts) > score_idx + 2 else ''
                    category = parts[score_idx + 3] if len(parts) > score_idx + 3 else ''
                    
                    # 人均（通常是数字）
                    price = ''
                    for p in parts[score_idx:]:
                        if p.isdigit() and 10 < int(p) < 1000:
                            price = p
                            break
                    
                    restaurant = {
                        'rank': rank,
                        'name': name,
                        'score': score,
                        'district': district,
                        'category': category,
                        'price': price,
                        'raw': line[:100]
                    }
                    
                    if current_section == 'must_eat':
                        must_eat.append(restaurant)
                    else:
                        worth_trying.append(restaurant)
                        
            except (ValueError, IndexError):
                continue
    
    return {'must_eat': must_eat, 'worth_trying': worth_trying}

def save_to_csv(data, output_path):
    """保存为CSV"""
    all_restaurants = []
    
    for r in data['must_eat']:
        r['list'] = '必吃清单'
        all_restaurants.append(r)
    
    for r in data['worth_trying']:
        r['list'] = '值得试清单'
        all_restaurants.append(r)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['list', 'rank', 'name', 'score', 'district', 'category', 'price'])
        writer.writeheader()
        writer.writerows(all_restaurants)
    
    return all_restaurants

def save_to_json(data, output_path):
    """保存为JSON"""
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    import sys
    image_path = sys.argv[1] if len(sys.argv) > 1 else '/root/.openclaw/media/inbound/6b26c6d8-e58e-4b13-acde-31afed626713.jpg'
    
    print("正在提取餐厅数据...")
    data = extract_all_restaurants(image_path)
    
    print(f"\n提取完成:")
    print(f"- 必吃清单: {len(data['must_eat'])} 家")
    print(f"- 值得试清单: {len(data['worth_trying'])} 家")
    print(f"- 总计: {len(data['must_eat']) + len(data['worth_trying'])} 家")
    
    # 保存文件
    csv_path = '/root/.openclaw/workspace/restaurants_full.csv'
    json_path = '/root/.openclaw/workspace/restaurants_full.json'
    
    all_data = save_to_csv(data, csv_path)
    save_to_json(data, json_path)
    
    print(f"\n已保存:")
    print(f"- CSV: {csv_path}")
    print(f"- JSON: {json_path}")
    
    # 打印预览
    print("\n=== 必吃清单 TOP 5 ===")
    for r in data['must_eat'][:5]:
        print(f"{r['rank']:2d}. {r['name']:20s} {r['score']:.2f}分 {r['district']:8s} {r['category']:8s} ¥{r['price']}")
    
    print("\n=== 值得试清单 TOP 5 ===")
    for r in data['worth_trying'][:5]:
        print(f"{r['rank']:2d}. {r['name']:20s} {r['score']:.2f}分 {r['district']:8s} {r['category']:8s} ¥{r['price']}")
