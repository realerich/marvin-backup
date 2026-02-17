#!/usr/bin/env python3
"""
生成详细的架构图，包含技术栈
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    import os

    # 创建更大的图片以容纳更多内容
    width, height = 1400, 1000
    img = Image.new('RGB', (width, height), color='#fafbfc')
    draw = ImageDraw.Draw(img)

    # 加载中文字体
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 36)
        font_layer = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 22)
        font_tech = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 16)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 14)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", 12)
    except:
        font_title = ImageFont.load_default()
        font_layer = font_title
        font_tech = font_title
        font_text = font_title
        font_small = font_title

    # 颜色定义
    colors = {
        'title': '#1a1a1a',
        'layer1_bg': '#e3f2fd',
        'layer1_border': '#1976d2',
        'layer2_bg': '#f3e5f5',
        'layer2_border': '#7b1fa2',
        'layer3_bg': '#e8f5e9',
        'layer3_border': '#388e3c',
        'layer4_bg': '#fff3e0',
        'layer4_border': '#f57c00',
        'tech_bg': '#ffffff',
        'tech_border': '#e0e0e0',
        'text': '#333333',
        'tech_text': '#555555',
        'arrow': '#666666'
    }

    # 标题
    draw.text((width//2, 40), "Marvin 智能助手架构 v2.0", 
              fill=colors['title'], font=font_title, anchor="mm")
    draw.text((width//2, 75), "四层架构 + 技术栈全览", 
              fill='#666666', font=font_tech, anchor="mm")

    # 定义层级数据（包含技术栈）
    layers = [
        {
            'name': '交互层',
            'icon': '📱',
            'platform': '飞书 (Feishu/Lark)',
            'y': 120,
            'height': 140,
            'color_bg': colors['layer1_bg'],
            'color_border': colors['layer1_border'],
            'functions': ['即时消息', '任务创建', '系统通知'],
            'tech_stack': ['Feishu API', 'Webhook', 'Event订阅']
        },
        {
            'name': '数据层',
            'icon': '🗄️',
            'platform': '阿里云 RDS (PostgreSQL)',
            'y': 280,
            'height': 160,
            'color_bg': colors['layer2_bg'],
            'color_border': colors['layer2_border'],
            'functions': ['消息历史', '监控指标', '任务追踪', 'AI记忆'],
            'tech_stack': ['PostgreSQL 14', 'psycopg2', '连接池', 'JSONB']
        },
        {
            'name': '执行层',
            'icon': '⚡',
            'platform': '阿里云 ECS + OpenClaw',
            'y': 460,
            'height': 160,
            'color_bg': colors['layer3_bg'],
            'color_border': colors['layer3_border'],
            'functions': ['AI核心处理', '工作流引擎', '定时任务', '系统监控'],
            'tech_stack': ['Python 3.12', 'OpenClaw', 'Docker', 'Cron']
        },
        {
            'name': '代码层',
            'icon': '📦',
            'platform': 'GitHub',
            'y': 640,
            'height': 140,
            'color_bg': colors['layer4_bg'],
            'color_border': colors['layer4_border'],
            'functions': ['Issues追踪', 'Actions自动化', 'Pages状态页'],
            'tech_stack': ['Git', 'GitHub API', 'Jekyll', 'GitHub Pages']
        }
    ]

    box_width = 1200
    start_x = 100

    # 绘制每个层级
    for layer in layers:
        # 层级背景
        draw.rectangle(
            [start_x, layer['y'], start_x + box_width, layer['y'] + layer['height']],
            outline=layer['color_border'],
            width=3,
            fill=layer['color_bg']
        )
        
        # 层级标题
        title_text = f"{layer['icon']} {layer['name']} - {layer['platform']}"
        draw.text((start_x + 20, layer['y'] + 15), 
                  title_text, 
                  fill=layer['color_border'], 
                  font=font_layer)
        
        # 功能模块区域
        func_y = layer['y'] + 50
        box_width_func = 180
        box_height_func = 35
        func_x = start_x + 40
        
        for func in layer['functions']:
            # 功能框
            draw.rectangle(
                [func_x, func_y, func_x + box_width_func, func_y + box_height_func],
                outline=layer['color_border'],
                width=1,
                fill='white'
            )
            draw.text((func_x + box_width_func//2, func_y + box_height_func//2), 
                     func, 
                     fill=colors['text'], 
                     font=font_text,
                     anchor="mm")
            func_x += box_width_func + 20
        
        # 技术栈区域
        tech_y = layer['y'] + 95
        tech_label = "技术栈:"
        draw.text((start_x + 20, tech_y), tech_label, 
                 fill=colors['tech_text'], font=font_small)
        
        tech_x = start_x + 80
        for tech in layer['tech_stack']:
            # 技术标签
            tech_width = len(tech) * 10 + 20
            draw.rectangle(
                [tech_x, tech_y - 2, tech_x + tech_width, tech_y + 22],
                outline=colors['tech_border'],
                width=1,
                fill=colors['tech_bg']
            )
            draw.text((tech_x + 10, tech_y + 8), tech, 
                     fill=colors['tech_text'], font=font_small)
            tech_x += tech_width + 15

    # 绘制连接箭头
    arrow_color = colors['arrow']
    arrow_x = width // 2
    
    # 层间箭头
    for i in range(len(layers) - 1):
        y1 = layers[i]['y'] + layers[i]['height']
        y2 = layers[i + 1]['y']
        
        # 箭头线
        draw.line([(arrow_x, y1), (arrow_x, y2 - 5)], fill=arrow_color, width=2)
        # 箭头
        draw.polygon([(arrow_x-5, y2-5), (arrow_x+5, y2-5), (arrow_x, y2)], fill=arrow_color)

    # 底部信息区域
    info_y = 810
    draw.text((start_x, info_y), "核心特性:", fill=colors['title'], font=font_layer)
    
    features = [
        "✓ 飞书消息实时同步RDS (连接池 + 本地队列双重保障)",
        "✓ 任务自动转GitHub Issue (飞书一句话创建任务)",
        "✓ 系统全监控 (每小时健康检查 + 异常自动报警)",
        "✓ 云端备份 (GitHub Pages状态页 + Docker秒级恢复)"
    ]
    
    feat_y = info_y + 35
    for feat in features:
        draw.text((start_x + 20, feat_y), feat, fill=colors['text'], font=font_text)
        feat_y += 25

    # 数据流向说明
    flow_y = 920
    draw.text((start_x, flow_y), "数据流向: 飞书 → RDS (实时同步) → GitHub (每6小时导出)  |  恢复: GitHub → Docker → ECS (5分钟内)", 
             fill='#666666', font=font_small)

    # 保存
    output_dir = '/root/.openclaw/workspace/output'
    os.makedirs(output_dir, exist_ok=True)
    output_path = f'{output_dir}/marvin_architecture_v2.png'
    img.save(output_path)
    print(f"✅ 详细架构图已生成: {output_path}")
    print(f"   尺寸: {width}x{height}")
    print(f"   包含: 4层架构 + 技术栈 + 核心特性")

except ImportError as e:
    print(f"❌ 错误: {e}")
    print("请安装PIL: pip3 install pillow")