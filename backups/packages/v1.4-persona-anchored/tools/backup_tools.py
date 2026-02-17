#!/usr/bin/env python3
"""
Marvin 工具包备份工具
打包所有工具、配置和依赖，用于灾难恢复
"""

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
BACKUP_DIR = WORKSPACE / "backups"
PACKAGES_DIR = BACKUP_DIR / "packages"

# 需要备份的文件和目录
BACKUP_ITEMS = {
    'tools': {
        'path': WORKSPACE / 'tools',
        'description': '工具脚本目录',
        'files': [
            'gaode_map.py',
            'gaode_map.sh',
            'restaurant_finder.py',
            'extract_restaurants.py',
            'extract_restaurants_full.py',
            'email_tool.py',
            'email_smart.py',
            'email_checker.py',
            'cloudflare_email.py',
            'memory_local.py',
            'memory_simple.py',
            'viz_tool.py',
            'doc_tool.py',
            'webhook_tool.py',
            'system_monitor.py',
            'calendar_tool.py',
            'voice_tool.py',
            'workflow_engine.py',
            'browser_auto.py',
            'backup_tools.py',
            'restore_tools.py',
            'email_cleaner.py',
            'rds_manager.py',
            'rds_master.py',
            'restaurant_rds.py',
            'metrics_rds.py',
            'email_rds.py',
            'memory_rds.py',
            'webhook_rds.py',
            'RDS-README.md',
        ]
    },
    'config': {
        'path': WORKSPACE / 'config',
        'description': '配置文件目录',
        'files': [
            'email_config.json',
            'webhooks.json',
            'monitor_config.json',
        ]
    },
    'memory': {
        'path': WORKSPACE / 'memory',
        'description': '记忆文件',
        'files': [
            '2026-02-16.md',
        ]
    },
    'root_configs': {
        'path': WORKSPACE,
        'description': '根目录配置',
        'files': [
            'HEARTBEAT.md',
            'SOUL.md',
            'USER.md',
            'IDENTITY.md',
            'AGENTS.md',
            'MEMORY.md',
            'TOOLS.md',
            'INFRASTRUCTURE.md',
            'PERSONA.md',
        ]
    },
    'data': {
        'path': WORKSPACE,
        'description': '数据文件',
        'files': [
            'restaurants_full.csv',
            'restaurants_full.json',
            'restaurants_full_with_coords.csv',
        ]
    }
}

# Python依赖
PYTHON_DEPS = [
    'psutil',
    'google-auth',
    'google-auth-oauthlib',
    'google-auth-httplib2',
    'google-api-python-client',
    'pyttsx3',
    'speechrecognition',
    'sentence-transformers',
    'pandas',
    'numpy',
    'matplotlib',
    'plotly',
    'pillow',
    'PyPDF2',
    'reportlab',
    'pdf2image',
    'python-docx',
    'openpyxl',
    'requests',
]

# 系统依赖
SYSTEM_DEPS = [
    'fonts-wqy-zenhei',  # 中文字体
    'poppler-utils',     # PDF处理
]

class BackupManager:
    """备份管理器"""
    
    def __init__(self):
        PACKAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    def create_package(self, name=None):
        """创建完整备份包"""
        if not name:
            name = f"marvin-tools-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        package_dir = PACKAGES_DIR / name
        package_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📦 创建备份包: {name}")
        print("=" * 50)
        
        # 1. 复制工具脚本
        print("\n📁 备份工具脚本...")
        tools_dir = package_dir / 'tools'
        tools_dir.mkdir(exist_ok=True)
        for tool_file in BACKUP_ITEMS['tools']['files']:
            src = BACKUP_ITEMS['tools']['path'] / tool_file
            if src.exists():
                shutil.copy2(src, tools_dir / tool_file)
                print(f"  ✓ {tool_file}")
        
        # 2. 复制配置文件
        print("\n⚙️ 备份配置文件...")
        config_dir = package_dir / 'config'
        config_dir.mkdir(exist_ok=True)
        for config_file in BACKUP_ITEMS['config']['files']:
            src = BACKUP_ITEMS['config']['path'] / config_file
            if src.exists():
                shutil.copy2(src, config_dir / config_file)
                print(f"  ✓ {config_file}")
        
        # 3. 复制记忆文件
        print("\n🧠 备份记忆文件...")
        memory_dir = package_dir / 'memory'
        memory_dir.mkdir(exist_ok=True)
        for mem_file in BACKUP_ITEMS['memory']['files']:
            src = BACKUP_ITEMS['memory']['path'] / mem_file
            if src.exists():
                shutil.copy2(src, memory_dir / mem_file)
                print(f"  ✓ {mem_file}")
        
        # 4. 复制根目录配置
        print("\n📄 备份根目录配置...")
        for root_file in BACKUP_ITEMS['root_configs']['files']:
            src = BACKUP_ITEMS['root_configs']['path'] / root_file
            if src.exists():
                shutil.copy2(src, package_dir / root_file)
                print(f"  ✓ {root_file}")
        
        # 5. 复制数据文件
        print("\n💾 备份数据文件...")
        data_dir = package_dir / 'data'
        data_dir.mkdir(exist_ok=True)
        for data_file in BACKUP_ITEMS['data']['files']:
            src = BACKUP_ITEMS['data']['path'] / data_file
            if src.exists():
                shutil.copy2(src, data_dir / data_file)
                print(f"  ✓ {data_file}")
        
        # 6. 生成依赖清单
        print("\n📝 生成依赖清单...")
        deps_info = {
            'python_deps': PYTHON_DEPS,
            'system_deps': SYSTEM_DEPS,
            'backup_time': datetime.now().isoformat(),
            'backup_version': '1.0',
        }
        with open(package_dir / 'dependencies.json', 'w') as f:
            json.dump(deps_info, f, indent=2)
        
        # 7. 生成恢复脚本
        print("\n🔧 生成恢复脚本...")
        self._create_restore_script(package_dir)
        self._create_install_script(package_dir)
        self._create_readme(package_dir)
        
        # 8. 打包为tar.gz
        print("\n📦 压缩备份包...")
        tar_path = PACKAGES_DIR / f"{name}.tar.gz"
        subprocess.run(
            ['tar', '-czf', str(tar_path), '-C', str(PACKAGES_DIR), name],
            check=True
        )
        
        print("\n" + "=" * 50)
        print(f"✅ 备份完成!")
        print(f"📂 备份目录: {package_dir}")
        print(f"📦 压缩包: {tar_path}")
        print(f"📊 大小: {tar_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        return tar_path
    
    def _create_restore_script(self, package_dir):
        """创建恢复脚本"""
        script = '''#!/bin/bash
# Marvin 工具包恢复脚本
# 用法: ./restore.sh [目标目录]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_DIR="${1:-/root/.openclaw/workspace}"

echo "🔧 Marvin 工具包恢复"
echo "===================="
echo "源目录: $SCRIPT_DIR"
echo "目标目录: $TARGET_DIR"
echo ""

# 创建目录
mkdir -p "$TARGET_DIR"/{tools,config,memory,output/{charts,documents,audio,monitoring},logs}

# 恢复工具
echo "📁 恢复工具脚本..."
cp -v "$SCRIPT_DIR"/tools/*.py "$TARGET_DIR/tools/" 2>/dev/null || true
cp -v "$SCRIPT_DIR"/tools/*.sh "$TARGET_DIR/tools/" 2>/dev/null || true

# 恢复配置
echo ""
echo "⚙️ 恢复配置文件..."
if [ -d "$SCRIPT_DIR/config" ]; then
    cp -v "$SCRIPT_DIR"/config/*.json "$TARGET_DIR/config/" 2>/dev/null || true
fi

# 恢复记忆
echo ""
echo "🧠 恢复记忆文件..."
if [ -d "$SCRIPT_DIR/memory" ]; then
    cp -v "$SCRIPT_DIR"/memory/*.md "$TARGET_DIR/memory/" 2>/dev/null || true
fi

# 恢复根目录配置
echo ""
echo "📄 恢复根目录配置..."
for file in HEARTBEAT.md SOUL.md USER.md IDENTITY.md AGENTS.md MEMORY.md TOOLS.md; do
    if [ -f "$SCRIPT_DIR/$file" ]; then
        cp -v "$SCRIPT_DIR/$file" "$TARGET_DIR/"
    fi
done

# 恢复数据
echo ""
echo "💾 恢复数据文件..."
if [ -d "$SCRIPT_DIR/data" ]; then
    cp -v "$SCRIPT_DIR"/data/*.csv "$TARGET_DIR/" 2>/dev/null || true
    cp -v "$SCRIPT_DIR"/data/*.json "$TARGET_DIR/" 2>/dev/null || true
fi

echo ""
echo "✅ 文件恢复完成!"
echo ""
echo "下一步:"
echo "1. 运行 ./install-deps.sh 安装依赖"
echo "2. 配置API密钥 (email_config.json)"
echo "3. 恢复cron任务"
'''
        
        restore_script = package_dir / 'restore.sh'
        with open(restore_script, 'w') as f:
            f.write(script)
        restore_script.chmod(0o755)
    
    def _create_install_script(self, package_dir):
        """创建依赖安装脚本"""
        script = '''#!/bin/bash
# Marvin 工具包依赖安装脚本

set -e

echo "📦 安装系统依赖..."
echo "===================="

# 安装中文字体
if ! dpkg -l | grep -q fonts-wqy-zenhei; then
    echo "安装中文字体..."
    apt-get update && apt-get install -y fonts-wqy-zenhei poppler-utils
else
    echo "✓ 中文字体已安装"
fi

echo ""
echo "🐍 安装Python依赖..."
echo "===================="

# Python依赖
pip3 install \
    psutil \
    google-auth \
    google-auth-oauthlib \
    google-auth-httplib2 \
    google-api-python-client \
    pyttsx3 \
    speechrecognition \
    sentence-transformers \
    pandas \
    numpy \
    matplotlib \
    plotly \
    pillow \
    PyPDF2 \
    reportlab \
    pdf2image \
    python-docx \
    openpyxl \
    requests \
    --break-system-packages -q

echo ""
echo "✅ 依赖安装完成!"
'''
        
        install_script = package_dir / 'install-deps.sh'
        with open(install_script, 'w') as f:
            f.write(script)
        install_script.chmod(0o755)
    
    def _create_readme(self, package_dir):
        """创建README"""
        readme = '''# Marvin 工具包

完整备份包含18个工具脚本和配置。

## 快速恢复

```bash
# 1. 解压
tar -xzf marvin-tools-*.tar.gz
cd marvin-tools-*

# 2. 恢复文件
./restore.sh

# 3. 安装依赖
./install-deps.sh

# 4. 配置API密钥
# 编辑 /root/.openclaw/workspace/config/email_config.json

# 5. 恢复cron任务（手动）
```

## 工具清单

| 工具 | 功能 |
|:---|:---|
| gaode_map.py | 高德地图API |
| restaurant_finder.py | 餐厅推荐 |
| email_tool.py | 邮件收发 |
| email_smart.py | 智能邮件分类 |
| memory_local.py | 向量语义搜索 |
| viz_tool.py | 数据可视化 |
| doc_tool.py | 文档处理 |
| webhook_tool.py | Webhook触发器 |
| system_monitor.py | 系统监控 |
| calendar_tool.py | 日历集成 |
| voice_tool.py | 语音能力 |
| workflow_engine.py | 工作流引擎 |
| browser_auto.py | 浏览器自动化 |

## 备份信息

- 备份时间: {time}
- 版本: 1.0
- 工具数量: 18
'''.format(time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        with open(package_dir / 'README.md', 'w') as f:
            f.write(readme)
    
    def list_packages(self):
        """列出所有备份包"""
        packages = list(PACKAGES_DIR.glob('*.tar.gz'))
        if not packages:
            print("📭 没有备份包")
            return []
        
        print(f"📦 找到 {len(packages)} 个备份包:")
        print("=" * 60)
        for pkg in sorted(packages, key=lambda x: x.stat().st_mtime, reverse=True):
            size = pkg.stat().st_size / 1024 / 1024
            mtime = datetime.fromtimestamp(pkg.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            print(f"  {pkg.name:<40} {size:>6.2f} MB  {mtime}")
        
        return packages


def main():
    import sys
    
    manager = BackupManager()
    
    if len(sys.argv) < 2:
        print("📦 Marvin 工具包备份工具")
        print("\n用法:")
        print("  python3 backup_tools.py create [名称]  # 创建备份")
        print("  python3 backup_tools.py list           # 列出备份")
        print("\n示例:")
        print("  python3 backup_tools.py create")
        print("  python3 backup_tools.py create v1.0")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'create':
        name = sys.argv[2] if len(sys.argv) > 2 else None
        manager.create_package(name)
    
    elif cmd == 'list':
        manager.list_packages()
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
