#!/usr/bin/env python3
"""
Graphviz 架构图生成器
生成专业系统架构流程图
"""

from graphviz import Digraph
from pathlib import Path
from datetime import datetime

OUTPUT_DIR = Path("/root/.openclaw/workspace/output/charts")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def generate_marvin_architecture():
    """生成Marvin四层架构图"""
    
    dot = Digraph(comment='Marvin 4-Layer Architecture')
    dot.attr(rankdir='TB', size='16,12', dpi='150')
    dot.attr('node', shape='box', style='rounded,filled', fontsize='11', fontname='Helvetica')
    dot.attr('edge', fontsize='9', fontname='Helvetica')
    
    # 标题
    dot.attr(label='Marvin System Architecture\n4-Layer Design', 
             labelloc='t', fontsize='18', fontname='Helvetica-Bold')
    
    # 颜色定义
    colors = {
        'feishu': '#E3F2FD',      # 浅蓝
        'rds': '#F3E5F5',         # 浅紫
        'ecs': '#E8F5E9',         # 浅绿
        'github': '#FFF3E0',      # 浅橙
        'tool': '#E0E0E0',        # 灰
    }
    
    # ========== 第1层：交互层 ==========
    with dot.subgraph(name='cluster_feishu') as c:
        c.attr(label='交互层 - Feishu/Lark', style='rounded', bgcolor=colors['feishu'], 
               fontname='Helvetica-Bold', fontsize='13')
        c.node('feishu_msg', '消息收发\nfeishu_msg.py', fillcolor='white')
        c.node('feishu_sync', 'RDS同步\nfeishu_sync.py', fillcolor='white')
        c.node('feishu_doc', '文档管理\nfeishu_doc.py', fillcolor='white')
    
    # ========== 第2层：数据层 ==========
    with dot.subgraph(name='cluster_rds') as c:
        c.attr(label='数据层 - RDS/PostgreSQL', style='rounded', bgcolor=colors['rds'],
               fontname='Helvetica-Bold', fontsize='13')
        c.node('rds_master', '主连接\nrds_master.py', fillcolor='white')
        c.node('rds_pool', '连接池\nrds_pool.py', fillcolor='white')
        c.node('feishu_db', '消息表\nfeishu_messages', fillcolor='white')
    
    # ========== 第3层：执行层 ==========
    with dot.subgraph(name='cluster_ecs') as c:
        c.attr(label='执行层 - ECS/OpenClaw', style='rounded', bgcolor=colors['ecs'],
               fontname='Helvetica-Bold', fontsize='13')
        # 工具模块
        with c.subgraph(name='cluster_tools') as t:
            t.attr(label='工具集 (28+)', style='dashed', bgcolor='#C8E6C9')
            t.node('email', '智能邮件\nemail_smart.py', fillcolor='white')
            t.node('monitor', '系统监控\nsystem_monitor.py', fillcolor='white')
            t.node('chart', '图表生成\nchart_generator.py', fillcolor='white')
            t.node('voice', '语音工具\nvoice_tool.py', fillcolor='white')
            t.node('browser', '浏览器\nbrowser_auto.py', fillcolor='white')
        c.node('workflow', '工作流引擎\nworkflow_engine.py', fillcolor='white')
    
    # ========== 第4层：代码层 ==========
    with dot.subgraph(name='cluster_github') as c:
        c.attr(label='代码层 - GitHub', style='rounded', bgcolor=colors['github'],
               fontname='Helvetica-Bold', fontsize='13')
        c.node('github_core', '核心备份\ngithub_core.py', fillcolor='white')
        c.node('feishu_gh', '飞书同步\nfeishu_to_github.py', fillcolor='white')
        c.node('github_io', '状态页面\nGitHub Pages', fillcolor='white')
    
    # ========== 跨层连接 ==========
    # 1->2
    dot.edge('feishu_msg', 'feishu_db', label='消息写入', style='solid')
    dot.edge('feishu_sync', 'rds_master', label='同步查询', style='solid')
    
    # 2->3
    dot.edge('rds_pool', 'email', label='邮件数据', style='solid')
    dot.edge('rds_pool', 'monitor', label='监控指标', style='solid')
    
    # 3->4
    dot.edge('workflow', 'github_core', label='自动备份', style='solid')
    dot.edge('chart', 'feishu_gh', label='图表推送', style='solid')
    
    # 4->1 (反馈循环)
    dot.edge('github_io', 'feishu_msg', label='状态通知', style='dashed', color='gray')
    
    # 保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = OUTPUT_DIR / f"marvin_architecture_graphviz_{timestamp}"
    dot.render(str(output_file), format='png', cleanup=True)
    
    return str(output_file) + '.png'


def generate_data_flow():
    """生成数据流图"""
    
    dot = Digraph(comment='Data Flow')
    dot.attr(rankdir='LR', size='14,8', dpi='150')
    dot.attr('node', shape='ellipse', style='filled', fontsize='10')
    
    # 输入
    dot.node('input', 'User Input\n(Feishu)', fillcolor='#E3F2FD')
    
    # 处理节点
    dot.node('parse', 'Parse\nCommand', fillcolor='#FFF9C4')
    dot.node('route', 'Route\nDecision', fillcolor='#FFF9C4')
    
    # 输出
    dot.node('tool', 'Tool\nExecution', fillcolor='#E8F5E9')
    dot.node('db', 'Data\nStorage', fillcolor='#F3E5F5')
    dot.node('response', 'Response\nOutput', fillcolor='#E3F2FD')
    
    # 边
    dot.edge('input', 'parse')
    dot.edge('parse', 'route')
    dot.edge('route', 'tool', label='tool call')
    dot.edge('route', 'db', label='data op')
    dot.edge('tool', 'db', style='dashed')
    dot.edge('tool', 'response')
    dot.edge('db', 'response', style='dashed')
    
    output_file = OUTPUT_DIR / f"data_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    dot.render(str(output_file), format='png', cleanup=True)
    
    return str(output_file) + '.png'


def main():
    import sys
    
    if len(sys.argv) < 2 or sys.argv[1] == 'all':
        print("🎨 Generating Graphviz diagrams...")
        
        arch_file = generate_marvin_architecture()
        print(f"✅ Architecture diagram: {arch_file}")
        
        flow_file = generate_data_flow()
        print(f"✅ Data flow diagram: {flow_file}")
        
    elif sys.argv[1] == 'arch':
        arch_file = generate_marvin_architecture()
        print(f"✅ Architecture diagram: {arch_file}")
        
    elif sys.argv[1] == 'flow':
        flow_file = generate_data_flow()
        print(f"✅ Data flow diagram: {flow_file}")
        
    else:
        print("Usage: python3 graphviz_charts.py [all|arch|flow]")


if __name__ == '__main__':
    main()