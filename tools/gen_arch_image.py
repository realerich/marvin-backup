#!/usr/bin/env python3
"""
生成架构图图片
使用 matplotlib 或 pillow
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os

    # 创建图片
    width, height = 1200, 800
    img = Image.new('RGB', (width, height), color='#f8f9fa')
    draw = ImageDraw.Draw(img)

    # 尝试加载字体
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 32)
        font_header = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
    except:
        font_title = ImageFont.load_default()
        font_header = font_title
        font_text = font_title
        font_small = font_title

    # 颜色
    colors = {
        'title': '#333333',
        'layer1': '#2196f3',  # 蓝色 - 交互层
        'layer2': '#9c27b0',  # 紫色 - 数据层
        'layer3': '#4caf50',  # 绿色 - 执行层
        'layer4': '#ff9800',  # 橙色 - 代码层
        'white': '#ffffff',
        'gray': '#666666'
    }

    # 标题
    draw.text((width//2, 30), "🤖 Marvin 智能助手架构 v2.0", 
              fill=colors['title'], font=font_title, anchor="mm")

    # 定义层级框
    layers = [
        {
            'name': '📱 交互层 - 飞书',
            'y': 80,
            'height': 100,
            'color': colors['layer1'],
            'items': ['即时消息', '任务创建', '系统通知']
        },
        {
            'name': '🗄️ 数据层 - RDS',
            'y': 200,
            'height': 120,
            'color': colors['layer2'],
            'items': ['消息历史', '监控指标', '任务追踪', 'AI记忆']
        },
        {
            'name': '⚡ 执行层 - ECS',
            'y': 340,
            'height': 120,
            'color': colors['layer3'],
            'items': ['OpenClaw', '工作流引擎', '定时任务', '系统监控']
        },
        {
            'name': '📦 代码层 - GitHub',
            'y': 480,
            'height': 100,
            'color': colors['layer4'],
            'items': ['Issues追踪', 'Actions自动化', 'Pages状态页']
        }
    ]

    box_width = 1000
    start_x = 100

    # 绘制层级
    for layer in layers:
        # 外框
        draw.rectangle(
            [start_x, layer['y'], start_x + box_width, layer['y'] + layer['height']],
            outline=layer['color'],
            width=3,
            fill='#ffffff'
        )
        
        # 标题
        draw.text((start_x + 20, layer['y'] + 15), 
                  layer['name'], 
                  fill=layer['color'], 
                  font=font_header)
        
        # 项目
        item_x = start_x + 40
        item_y = layer['y'] + 50
        for item in layer['items']:
            draw.text((item_x, item_y), f"• {item}", 
                     fill=colors['gray'], 
                     font=font_text)
            item_x += 220

    # 绘制连接箭头
    arrow_color = '#666666'
    # 交互层 -> 数据层
    draw.line([(width//2, 180), (width//2, 200)], fill=arrow_color, width=2)
    draw.polygon([(width//2-5, 200), (width//2+5, 200), (width//2, 195)], fill=arrow_color)
    
    # 数据层 -> 代码层
    draw.line([(width//2, 320), (width//2, 340)], fill=arrow_color, width=2)
    draw.polygon([(width//2-5, 340), (width//2+5, 340), (width//2, 335)], fill=arrow_color)
    
    # 执行层 -> 代码层
    draw.line([(width//2, 460), (width//2, 480)], fill=arrow_color, width=2)
    draw.polygon([(width//2-5, 480), (width//2+5, 480), (width//2, 475)], fill=arrow_color)

    # 特性列表
    features_y = 610
    draw.text((start_x, features_y), "核心特性:", fill=colors['title'], font=font_header)
    
    features = [
        "✅ 飞书消息实时同步RDS (连接池+本地队列双重保障)",
        "✅ 任务自动转GitHub Issue (飞书一句话创建任务)",
        "✅ 系统全监控 (每小时健康检查 + 异常自动报警)",
        "✅ 云端备份 (GitHub Pages状态页 + Docker秒级恢复)"
    ]
    
    feat_y = features_y + 35
    for feat in features:
        draw.text((start_x + 20, feat_y), feat, fill=colors['gray'], font=font_small)
        feat_y += 22

    # 保存
    output_dir = '/root/.openclaw/workspace/output'
    os.makedirs(output_dir, exist_ok=True)
    img.save(f'{output_dir}/marvin_architecture.png')
    print(f"✅ 架构图已生成: {output_dir}/marvin_architecture.png")

except ImportError:
    print("⚠️ PIL 未安装，使用文本版本")
    print("安装: pip3 install pillow")