#!/usr/bin/env python3
"""
Marvin 人格锚定检查
每次启动时运行，确保身份连续性
"""

import json
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")

def check_identity():
    """检查身份锚定"""
    print("🤖 Marvin 人格锚定检查")
    print("=" * 50)
    
    # 1. 检查核心文件
    core_files = ['SOUL.md', 'IDENTITY.md', 'PERSONA.md', 'MEMORY.md']
    print("\n📄 核心文件检查:")
    for f in core_files:
        path = WORKSPACE / f
        if path.exists():
            print(f"  ✅ {f}")
        else:
            print(f"  ❌ {f} - 缺失！")
    
    # 2. 读取身份
    print("\n🎭 身份确认:")
    try:
        identity = (WORKSPACE / 'IDENTITY.md').read_text()
        name = [l for l in identity.split('\n') if 'Name:' in l][0].split(':')[1].strip()
        print(f"  我是: {name}")
    except:
        print("  ⚠️ 无法读取身份")
    
    # 3. 检查用户
    print("\n👤 服务对象:")
    try:
        user = (WORKSPACE / 'USER.md').read_text()
        username = [l for l in user.split('\n') if 'Name:' in l][0].split(':')[1].strip()
        print(f"  为: {username} 服务")
    except:
        print("  ⚠️ 无法读取用户信息")
    
    # 4. 检查工具
    tools_dir = WORKSPACE / 'tools'
    tool_count = len(list(tools_dir.glob('*.py'))) if tools_dir.exists() else 0
    print(f"\n🛠️ 工具数量: {tool_count}")
    
    # 5. 检查记忆
    memory_dir = WORKSPACE / 'memory'
    memory_count = len(list(memory_dir.glob('*.md'))) if memory_dir.exists() else 0
    print(f"🧠 记忆文件: {memory_count}")
    
    # 6. 检查配置
    config_dir = WORKSPACE / 'config'
    if (config_dir / 'rds_config.json').exists():
        print("✅ RDS配置: 已配置")
    else:
        print("⚠️ RDS配置: 未配置")
    
    print("\n" + "=" * 50)
    print("✅ 锚定检查完成")
    print("\n确认:")
    print("  我是 Marvin 🤖")
    print("  我提供专业高效的服务")
    print("  我的记忆和能力完整保留")
    print("  模型变更不会影响我的身份")

if __name__ == '__main__':
    check_identity()
