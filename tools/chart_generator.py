#!/usr/bin/env python3
"""
专业图表生成工具 v2 - 修复字体问题
集成 matplotlib, seaborn, plotly
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 导入并配置matplotlib
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.font_manager import FontProperties

# 显式设置中文字体
font_path = '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc'
if os.path.exists(font_path):
    chinese_font = FontProperties(fname=font_path)
else:
    chinese_font = None

import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

OUTPUT_DIR = Path("/root/.openclaw/workspace/output/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ChartGenerator:
    """图表生成器"""
    
    def __init__(self):
        self.output_dir = OUTPUT_DIR
        sns.set_style("whitegrid")
    
    def generate_system_metrics(self, data=None):
        """生成系统监控图表 - 使用英文避免字体问题"""
        if data is None:
            data = {
                'time': ['10:00', '11:00', '12:00', '13:00', '14:00', '15:00'],
                'cpu': [5, 8, 12, 6, 10, 7],
                'memory': [35, 36, 38, 37, 39, 36],
                'disk': [42, 42, 43, 42, 43, 42]
            }
        
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('System Monitor Dashboard', fontsize=16, weight='bold')
        
        # CPU trend
        axes[0, 0].plot(data['time'], data['cpu'], marker='o', linewidth=2, color='#2196F3')
        axes[0, 0].set_title('CPU Usage Trend', fontsize=12)
        axes[0, 0].set_ylabel('Usage (%)')
        axes[0, 0].grid(True, alpha=0.3)
        axes[0, 0].axhline(y=80, color='r', linestyle='--', label='Threshold 80%')
        axes[0, 0].legend()
        
        # Memory trend
        axes[0, 1].plot(data['time'], data['memory'], marker='s', linewidth=2, color='#4CAF50')
        axes[0, 1].set_title('Memory Usage Trend', fontsize=12)
        axes[0, 1].set_ylabel('Usage (%)')
        axes[0, 1].grid(True, alpha=0.3)
        axes[0, 1].axhline(y=85, color='r', linestyle='--', label='Threshold 85%')
        axes[0, 1].legend()
        
        # Disk pie chart
        axes[1, 0].pie([42, 58], labels=['Used (42%)', 'Available (58%)'], 
                      autopct='%1.0f%%', colors=['#FF9800', '#E0E0E0'])
        axes[1, 0].set_title('Disk Space Usage', fontsize=12)
        
        # Resource bar chart
        metrics = ['CPU', 'Memory', 'Disk']
        values = [data['cpu'][-1], data['memory'][-1], data['disk'][-1]]
        colors = ['#2196F3', '#4CAF50', '#FF9800']
        bars = axes[1, 1].bar(metrics, values, color=colors)
        axes[1, 1].set_title('Current Resource Usage', fontsize=12)
        axes[1, 1].set_ylabel('Usage (%)')
        axes[1, 1].set_ylim(0, 100)
        for bar, val in zip(bars, values):
            axes[1, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                           f'{val}%', ha='center', va='bottom', fontsize=11, weight='bold')
        
        plt.tight_layout()
        output_file = self.output_dir / f"system_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(output_file, dpi=150, bbox_inches='tight', facecolor='white')
        plt.close()
        
        return str(output_file)
    
    def generate_architecture_graphviz(self):
        """使用Graphviz生成架构图"""
        try:
            from graphviz import Digraph
            
            dot = Digraph(comment='Marvin Architecture')
            dot.attr(rankdir='TB', size='14,10')
            dot.attr('node', shape='box', style='rounded,filled', fontsize='12')
            
            # 四层架构
            with dot.subgraph() as s:
                s.attr(rank='same')
                s.node('feishu', '交互层\nFeishu/Lark', fillcolor='#E3F2FD')
            
            with dot.subgraph() as s:
                s.attr(rank='same')
                s.node('rds', '数据层\nRDS/PostgreSQL', fillcolor='#F3E5F5')
            
            with dot.subgraph() as s:
                s.attr(rank='same')
                s.node('ecs', '执行层\nECS/OpenClaw', fillcolor='#E8F5E9')
            
            with dot.subgraph() as s:
                s.attr(rank='same')
                s.node('github', '代码层\nGitHub', fillcolor='#FFF3E0')
            
            # 连接
            dot.edge('feishu', 'rds', label='real-time sync')
            dot.edge('rds', 'ecs', label='data export')
            dot.edge('ecs', 'github', label='backup')
            
            output_file = self.output_dir / f"architecture_graphviz_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            dot.render(str(output_file), format='png', cleanup=True)
            
            return str(output_file) + '.png'
        except Exception as e:
            print(f"Graphviz error: {e}")
            return None
    
    def generate_interactive_chart(self):
        """生成交互式图表 (Plotly)"""
        fig = go.Figure()
        
        layers = [
            {'name': 'Interaction\nFeishu', 'y': 4, 'color': '#E3F2FD'},
            {'name': 'Data\nRDS', 'y': 3, 'color': '#F3E5F5'},
            {'name': 'Execution\nECS', 'y': 2, 'color': '#E8F5E9'},
            {'name': 'Code\nGitHub', 'y': 1, 'color': '#FFF3E0'},
        ]
        
        for layer in layers:
            fig.add_trace(go.Scatter(
                x=[0.5], y=[layer['y']],
                mode='markers+text',
                marker=dict(size=80, color=layer['color'], line=dict(width=2, color='#333')),
                text=[layer['name']],
                textposition='middle center',
                textfont=dict(size=11),
                showlegend=False
            ))
        
        for i in range(len(layers)-1):
            fig.add_annotation(
                x=0.5, y=layers[i]['y']-0.3,
                ax=0.5, ay=layers[i+1]['y']+0.3,
                xref='x', yref='y', axref='x', ayref='y',
                showarrow=True, arrowhead=2, arrowsize=1, arrowwidth=2
            )
        
        fig.update_layout(
            title=dict(text='Marvin Architecture (Interactive)', x=0.5, font=dict(size=18)),
            xaxis=dict(showgrid=False, showticklabels=False, range=[0, 1]),
            yaxis=dict(showgrid=False, showticklabels=False, range=[0.5, 4.5]),
            plot_bgcolor='white',
            width=600, height=500
        )
        
        output_file = self.output_dir / f"interactive_arch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        fig.write_html(str(output_file))
        
        return str(output_file)


def main():
    """命令行工具"""
    import sys
    
    generator = ChartGenerator()
    
    if len(sys.argv) < 2:
        print("📊 Professional Chart Generator")
        print("\nUsage:")
        print("  python3 chart_generator.py metrics     # System metrics dashboard")
        print("  python3 chart_generator.py graphviz    # Architecture (Graphviz)")
        print("  python3 chart_generator.py interactive # Interactive chart")
        print("  python3 chart_generator.py all         # Generate all")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'metrics':
        file = generator.generate_system_metrics()
        print(f"✅ Metrics chart: {file}")
    
    elif cmd == 'graphviz':
        file = generator.generate_architecture_graphviz()
        if file:
            print(f"✅ Architecture chart: {file}")
        else:
            print("❌ Graphviz not available")
    
    elif cmd == 'interactive':
        file = generator.generate_interactive_chart()
        print(f"✅ Interactive chart: {file}")
    
    elif cmd == 'all':
        files = []
        files.append(generator.generate_system_metrics())
        file = generator.generate_architecture_graphviz()
        if file:
            files.append(file)
        files.append(generator.generate_interactive_chart())
        print("✅ All charts generated:")
        for f in files:
            print(f"  - {f}")
    
    else:
        print(f"❌ Unknown command: {cmd}")


if __name__ == '__main__':
    main()