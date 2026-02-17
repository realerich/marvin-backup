# OCR 餐厅清单数据提取脚本
"""
从 NAV广佛必吃清单 图片中提取结构化数据
"""

import pytesseract
from PIL import Image
import re

def extract_restaurant_data(image_path):
    """提取餐厅清单数据"""
    img = Image.open(image_path)
    
    # OCR识别
    text = pytesseract.image_to_string(img, lang='chi_sim+eng')
    
    # 解析逻辑（基于表格结构）
    lines = text.split('\n')
    restaurants = []
    
    for line in lines:
        # 匹配餐厅行（序号 + 店名 + 评分模式）
        match = re.match(r'(\d+)\s+([\u4e00-\u9fa5]+(?:[（(][^)]+[)）])?)\s+(\d+\.\d+)', line)
        if match:
            restaurants.append({
                'rank': match.group(1),
                'name': match.group(2),
                'score': match.group(3),
                'raw': line
            })
    
    return restaurants

# 使用示例
if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1:
        data = extract_restaurant_data(sys.argv[1])
        for r in data[:10]:
            print(f"{r['rank']}. {r['name']} - {r['score']}分")
