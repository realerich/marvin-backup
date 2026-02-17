#!/usr/bin/env python3
"""
Marvin 工具包恢复工具
从备份包恢复所有工具、配置和数据
"""

import json
import os
import shutil
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path

WORKSPACE = Path("/root/.openclaw/workspace")
BACKUP_DIR = WORKSPACE / "backups" / "packages"

class RestoreManager:
    """恢复管理器"""
    
    def __init__(self):
        pass
    
    def find_packages(self):
        """查找所有备份包"""
        if not BACKUP_DIR.exists():
            return []
        return list(BACKUP_DIR.glob('*.tar.gz'))
    
    def select_package(self):
        """交互式选择备份包"""
        packages = self.find_packages()
        
        if not packages:
            print("❌ 没有找到备份包")
            print(f"请确保备份包在: {BACKUP_DIR}")
            return None
        
        print("📦 可用的备份包:")
        print("=" * 60)
        
        for i, pkg in enumerate(sorted(packages, key=lambda x: x.stat().st_mtime, reverse=True), 1):
            size = pkg.stat().st_size / 1024 / 1024
            mtime = datetime.fromtimestamp(pkg.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            print(f"  {i}. {pkg.name:<35} {size:>6.2f} MB  {mtime}")
        
        print("\n  0. 退出")
        
        while True:
            try:
                choice = input("\n选择备份包 (编号): ").strip()
                if choice == '0':
                    return None
                idx = int(choice) - 1
                if 0 <= idx < len(packages):
                    return sorted(packages, key=lambda x: x.stat().st_mtime, reverse=True)[idx]
                print("无效选择")
            except ValueError:
                print("请输入数字")
    
    def restore(self, package_path=None, target_dir=None):
        """执行恢复"""
        if not package_path:
            package_path = self.select_package()
            if not package_path:
                return False
        
        if not target_dir:
            target_dir = WORKSPACE
        
        target_dir = Path(target_dir)
        
        print(f"\n🔧 开始恢复")
        print("=" * 50)
        print(f"备份包: {package_path}")
        print(f"目标目录: {target_dir}")
        print("")
        
        # 创建临时目录
        temp_dir = Path(f"/tmp/marvin-restore-{datetime.now().strftime('%Y%m%d%H%M%S')}")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 解压
            print("📦 解压备份包...")
            with tarfile.open(package_path, 'r:gz') as tar:
                tar.extractall(temp_dir)
            
            # 找到解压后的目录
            extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
            if not extracted_dirs:
                print("❌ 备份包结构异常")
                return False
            
            source_dir = extracted_dirs[0]
            
            # 创建目标目录结构
            print("📁 创建目录结构...")
            for subdir in ['tools', 'config', 'memory', 'logs', 
                          'output/charts', 'output/documents', 
                          'output/audio', 'output/monitoring']:
                (target_dir / subdir).mkdir(parents=True, exist_ok=True)
            
            # 恢复工具
            print("\n📁 恢复工具脚本...")
            tools_src = source_dir / 'tools'
            tools_dst = target_dir / 'tools'
            if tools_src.exists():
                for f in tools_src.glob('*.py'):
                    shutil.copy2(f, tools_dst / f.name)
                    print(f"  ✓ {f.name}")
                for f in tools_src.glob('*.sh'):
                    shutil.copy2(f, tools_dst / f.name)
                    print(f"  ✓ {f.name}")
            
            # 恢复配置
            print("\n⚙️ 恢复配置文件...")
            config_src = source_dir / 'config'
            config_dst = target_dir / 'config'
            if config_src.exists():
                for f in config_src.glob('*.json'):
                    # 询问是否覆盖现有配置
                    dst_file = config_dst / f.name
                    if dst_file.exists():
                        response = input(f"  配置 {f.name} 已存在，是否覆盖? (y/N): ").strip().lower()
                        if response != 'y':
                            print(f"  ⏭️ 跳过 {f.name}")
                            continue
                    shutil.copy2(f, dst_file)
                    print(f"  ✓ {f.name}")
            
            # 恢复记忆
            print("\n🧠 恢复记忆文件...")
            memory_src = source_dir / 'memory'
            memory_dst = target_dir / 'memory'
            if memory_src.exists():
                for f in memory_src.glob('*.md'):
                    shutil.copy2(f, memory_dst / f.name)
                    print(f"  ✓ {f.name}")
            
            # 恢复根目录配置
            print("\n📄 恢复根目录配置...")
            for cfg_file in ['HEARTBEAT.md', 'SOUL.md', 'USER.md', 'IDENTITY.md', 
                            'AGENTS.md', 'MEMORY.md', 'TOOLS.md']:
                src = source_dir / cfg_file
                if src.exists():
                    dst = target_dir / cfg_file
                    if dst.exists():
                        response = input(f"  {cfg_file} 已存在，是否覆盖? (y/N): ").strip().lower()
                        if response != 'y':
                            print(f"  ⏭️ 跳过 {cfg_file}")
                            continue
                    shutil.copy2(src, dst)
                    print(f"  ✓ {cfg_file}")
            
            # 恢复数据
            print("\n💾 恢复数据文件...")
            data_src = source_dir / 'data'
            if data_src.exists():
                for f in data_src.glob('*'):
                    shutil.copy2(f, target_dir / f.name)
                    print(f"  ✓ {f.name}")
            
            print("\n" + "=" * 50)
            print("✅ 恢复完成!")
            print("")
            print("下一步:")
            print("1. 检查配置文件: edit config/email_config.json")
            print("2. 安装依赖: python3 tools/backup_tools.py install-deps")
            print("3. 测试工具: python3 tools/system_monitor.py")
            
            return True
            
        finally:
            # 清理临时目录
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
    
    def install_dependencies(self):
        """安装依赖"""
        print("📦 安装系统依赖...")
        print("=" * 50)
        
        # 安装系统依赖
        deps = ['fonts-wqy-zenhei', 'poppler-utils']
        for dep in deps:
            print(f"\n检查 {dep}...")
            result = subprocess.run(['dpkg', '-l', dep], capture_output=True)
            if result.returncode != 0:
                print(f"  安装 {dep}...")
                subprocess.run(['apt-get', 'update'], capture_output=True)
                subprocess.run(['apt-get', 'install', '-y', dep], check=True)
            else:
                print(f"  ✓ {dep} 已安装")
        
        print("\n🐍 安装Python依赖...")
        print("=" * 50)
        
        python_deps = [
            'psutil', 'google-auth', 'google-auth-oauthlib',
            'google-auth-httplib2', 'google-api-python-client',
            'pyttsx3', 'speechrecognition', 'sentence-transformers',
            'pandas', 'numpy', 'matplotlib', 'plotly', 'pillow',
            'PyPDF2', 'reportlab', 'pdf2image', 'python-docx',
            'openpyxl', 'requests',
        ]
        
        for dep in python_deps:
            print(f"  安装 {dep}...")
            subprocess.run(
                ['pip3', 'install', dep, '--break-system-packages', '-q'],
                capture_output=True
            )
        
        print("\n✅ 依赖安装完成!")
    
    def verify_installation(self):
        """验证安装"""
        print("\n🔍 验证安装...")
        print("=" * 50)
        
        tools_dir = WORKSPACE / 'tools'
        expected_tools = [
            'gaode_map.py', 'email_smart.py', 'memory_local.py',
            'viz_tool.py', 'system_monitor.py', 'calendar_tool.py',
        ]
        
        missing = []
        for tool in expected_tools:
            if not (tools_dir / tool).exists():
                missing.append(tool)
        
        if missing:
            print("❌ 缺失的工具:")
            for t in missing:
                print(f"  - {t}")
        else:
            print("✓ 所有核心工具已就位")
        
        # 检查Python依赖
        print("\n检查Python依赖...")
        try:
            import psutil
            print("  ✓ psutil")
        except:
            print("  ✗ psutil 缺失")
        
        try:
            import pandas
            print("  ✓ pandas")
        except:
            print("  ✗ pandas 缺失")
        
        try:
            import matplotlib
            print("  ✓ matplotlib")
        except:
            print("  ✗ matplotlib 缺失")
        
        try:
            import sentence_transformers
            print("  ✓ sentence-transformers")
        except:
            print("  ✗ sentence-transformers 缺失")


def main():
    import sys
    
    manager = RestoreManager()
    
    if len(sys.argv) < 2:
        print("🔧 Marvin 工具包恢复工具")
        print("\n用法:")
        print("  python3 restore_tools.py restore [备份包] [目标目录]")
        print("  python3 restore_tools.py deps           # 安装依赖")
        print("  python3 restore_tools.py verify         # 验证安装")
        print("\n交互式恢复:")
        print("  python3 restore_tools.py restore")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'restore':
        package = sys.argv[2] if len(sys.argv) > 2 else None
        target = sys.argv[3] if len(sys.argv) > 3 else None
        manager.restore(package, target)
    
    elif cmd == 'deps' or cmd == 'install-deps':
        manager.install_dependencies()
    
    elif cmd == 'verify':
        manager.verify_installation()
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
