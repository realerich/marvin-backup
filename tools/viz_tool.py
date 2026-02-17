#!/usr/bin/env python3
"""
数据可视化工具
生成各种图表：柱状图、折线图、饼图、散点图等
"""

import matplotlib
matplotlib.use('Agg')  # 无GUI后端
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
import json
import os
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("/root/.openclaw/workspace/output/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

class ChartGenerator:
    """图表生成器"""
    
    @staticmethod
    def bar_chart(data, title="柱状图", x_label="", y_label="", output_file=None):
        """生成柱状图"""
        if not output_file:
            output_file = OUTPUT_DIR / f"bar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        if isinstance(data, dict):
            labels = list(data.keys())
            values = list(data.values())
        else:
            labels = [str(i) for i in range(len(data))]
            values = data
        
        bars = ax.bar(labels, values, color='steelblue', edgecolor='black')
        
        # 添加数值标签
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.1f}', ha='center', va='bottom')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(axis='y', alpha=0.3)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(output_file)
    
    @staticmethod
    def pie_chart(data, title="饼图", output_file=None):
        """生成饼图"""
        if not output_file:
            output_file = OUTPUT_DIR / f"pie_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        fig, ax = plt.subplots(figsize=(8, 8))
        
        if isinstance(data, dict):
            labels = list(data.keys())
            sizes = list(data.values())
        else:
            labels = [f"Item {i+1}" for i in range(len(data))]
            sizes = data
        
        colors = plt.cm.Set3(range(len(labels)))
        
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                           colors=colors, startangle=90)
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(output_file)
    
    @staticmethod
    def line_chart(x_data, y_data, title="折线图", x_label="", y_label="", output_file=None):
        """生成折线图"""
        if not output_file:
            output_file = OUTPUT_DIR / f"line_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.plot(x_data, y_data, marker='o', linewidth=2, markersize=6, color='steelblue')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(output_file)
    
    @staticmethod
    def scatter_plot(x_data, y_data, title="散点图", x_label="", y_label="", output_file=None):
        """生成散点图"""
        if not output_file:
            output_file = OUTPUT_DIR / f"scatter_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        ax.scatter(x_data, y_data, alpha=0.6, s=100, color='steelblue', edgecolors='black')
        
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(output_file)
    
    @staticmethod
    def restaurant_rating_chart(csv_file, output_file=None):
        """餐厅评分可视化"""
        import csv
        
        if not output_file:
            output_file = OUTPUT_DIR / f"restaurants_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        
        # 读取数据
        restaurants = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    row['推荐分'] = float(row['推荐分'])
                    restaurants.append(row)
                except:
                    continue
        
        # 按评分排序，取前15
        restaurants.sort(key=lambda x: x['推荐分'], reverse=True)
        top15 = restaurants[:15]
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
        
        # 左图：评分排名
        names = [r['店名'][:15] + '...' if len(r['店名']) > 15 else r['店名'] for r in top15]
        scores = [r['推荐分'] for r in top15]
        colors = ['gold' if s >= 4.5 else 'lightgreen' if s >= 4.0 else 'lightblue' for s in scores]
        
        bars = ax1.barh(range(len(names)), scores, color=colors, edgecolor='black')
        ax1.set_yticks(range(len(names)))
        ax1.set_yticklabels(names)
        ax1.set_xlabel('评分')
        ax1.set_title('餐厅评分 TOP 15', fontsize=14, fontweight='bold')
        ax1.invert_yaxis()
        
        # 添加数值标签
        for i, (bar, score) in enumerate(zip(bars, scores)):
            ax1.text(score + 0.05, i, f'{score:.2f}', va='center')
        
        # 右图：区域分布
        districts = {}
        for r in restaurants:
            d = r.get('城区', '未知')
            districts[d] = districts.get(d, 0) + 1
        
        district_names = list(districts.keys())
        district_counts = list(districts.values())
        
        ax2.pie(district_counts, labels=district_names, autopct='%1.1f%%', startangle=90)
        ax2.set_title('餐厅区域分布', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        plt.close()
        
        return str(output_file)


class ImageProcessor:
    """图像处理工具"""
    
    @staticmethod
    def resize_image(input_path, output_path=None, width=None, height=None, scale=None):
        """调整图片大小"""
        from PIL import Image
        
        img = Image.open(input_path)
        
        if scale:
            new_size = (int(img.width * scale), int(img.height * scale))
        elif width and height:
            new_size = (width, height)
        elif width:
            ratio = width / img.width
            new_size = (width, int(img.height * ratio))
        elif height:
            ratio = height / img.height
            new_size = (int(img.width * ratio), height)
        else:
            return input_path
        
        img_resized = img.resize(new_size, Image.Resampling.LANCZOS)
        
        if not output_path:
            output_path = OUTPUT_DIR / f"resized_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        img_resized.save(output_path, quality=90)
        return str(output_path)
    
    @staticmethod
    def add_watermark(input_path, text="Marvin AI", output_path=None):
        """添加水印"""
        from PIL import Image, ImageDraw, ImageFont
        
        img = Image.open(input_path)
        draw = ImageDraw.Draw(img)
        
        # 尝试加载字体，如果没有就用默认
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        # 在右下角添加文字
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = img.width - text_width - 20
        y = img.height - text_height - 20
        
        # 半透明背景
        draw.rectangle([x-10, y-5, x+text_width+10, y+text_height+5], 
                       fill=(0, 0, 0, 128))
        draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
        
        if not output_path:
            output_path = OUTPUT_DIR / f"watermarked_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        img.save(output_path, quality=90)
        return str(output_path)
    
    @staticmethod
    def create_thumbnail(input_path, size=(300, 300), output_path=None):
        """创建缩略图"""
        from PIL import Image
        
        img = Image.open(input_path)
        img.thumbnail(size)
        
        if not output_path:
            output_path = OUTPUT_DIR / f"thumb_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        
        img.save(output_path, quality=85)
        return str(output_path)


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("📊 数据可视化工具")
        print("\n用法:")
        print("  python3 viz_tool.py bar '{\"A\":10,\"B\":20,\"C\":15}' [标题]")
        print("  python3 viz_tool.py pie '{\"类别1\":30,\"类别2\":70}' [标题]")
        print("  python3 viz_tool.py line '[1,2,3,4,5]' '[10,20,15,25,30]' [标题]")
        print("  python3 viz_tool.py scatter '[1,2,3,4,5]' '[10,20,15,25,30]' [标题]")
        print("  python3 viz_tool.py restaurants <csv文件>")
        print("  python3 viz_tool.py resize <图片路径> --width 800")
        print("  python3 viz_tool.py watermark <图片路径> [文字]")
        print("\n示例:")
        print("  python3 viz_tool.py bar '{\"周一\":100,\"周二\":150,\"周三\":120}' '每日销售额'")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'bar':
        data = json.loads(sys.argv[2])
        title = sys.argv[3] if len(sys.argv) > 3 else "柱状图"
        result = ChartGenerator.bar_chart(data, title=title)
        print(f"✅ 图表已保存: {result}")
    
    elif cmd == 'pie':
        data = json.loads(sys.argv[2])
        title = sys.argv[3] if len(sys.argv) > 3 else "饼图"
        result = ChartGenerator.pie_chart(data, title=title)
        print(f"✅ 图表已保存: {result}")
    
    elif cmd == 'line':
        x = json.loads(sys.argv[2])
        y = json.loads(sys.argv[3])
        title = sys.argv[4] if len(sys.argv) > 4 else "折线图"
        result = ChartGenerator.line_chart(x, y, title=title)
        print(f"✅ 图表已保存: {result}")
    
    elif cmd == 'scatter':
        x = json.loads(sys.argv[2])
        y = json.loads(sys.argv[3])
        title = sys.argv[4] if len(sys.argv) > 4 else "散点图"
        result = ChartGenerator.scatter_plot(x, y, title=title)
        print(f"✅ 图表已保存: {result}")
    
    elif cmd == 'restaurants':
        csv_file = sys.argv[2] if len(sys.argv) > 2 else "/root/.openclaw/workspace/restaurants_full_with_coords.csv"
        result = ChartGenerator.restaurant_rating_chart(csv_file)
        print(f"✅ 餐厅图表已保存: {result}")
    
    elif cmd == 'resize':
        input_path = sys.argv[2]
        # 解析参数
        width = None
        height = None
        scale = None
        for i, arg in enumerate(sys.argv):
            if arg == '--width' and i+1 < len(sys.argv):
                width = int(sys.argv[i+1])
            elif arg == '--height' and i+1 < len(sys.argv):
                height = int(sys.argv[i+1])
            elif arg == '--scale' and i+1 < len(sys.argv):
                scale = float(sys.argv[i+1])
        
        result = ImageProcessor.resize_image(input_path, width=width, height=height, scale=scale)
        print(f"✅ 图片已调整大小: {result}")
    
    elif cmd == 'watermark':
        input_path = sys.argv[2]
        text = sys.argv[3] if len(sys.argv) > 3 else "Marvin AI"
        result = ImageProcessor.add_watermark(input_path, text)
        print(f"✅ 水印已添加: {result}")
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
