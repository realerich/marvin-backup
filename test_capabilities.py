#!/usr/bin/env python3
"""
本地服务器能力测试脚本
验证所有扩展功能正常工作
"""

import sys
import subprocess

def test_tool(name, command):
    """测试工具是否安装"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print(f"✅ {name}: 正常")
            return True
        else:
            print(f"❌ {name}: 异常")
            return False
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False

def main():
    print("="*60)
    print("本地服务器能力验证测试")
    print("="*60)
    
    tests = []
    
    # 1. Python代码质量工具
    print("\n📦 Python代码质量工具:")
    tests.append(test_tool("black", "black --version"))
    tests.append(test_tool("isort", "isort --version"))
    tests.append(test_tool("flake8", "flake8 --version"))
    tests.append(test_tool("mypy", "mypy --version"))
    tests.append(test_tool("pytest", "pytest --version"))
    
    # 2. 数据处理库
    print("\n📊 数据处理库:")
    try:
        import pandas
        import numpy
        print(f"✅ pandas: {pandas.__version__}")
        print(f"✅ numpy: {numpy.__version__}")
        tests.append(True)
        tests.append(True)
    except ImportError as e:
        print(f"❌ 数据处理库: {e}")
        tests.append(False)
    
    # 3. Web框架
    print("\n🌐 Web/API框架:")
    try:
        import fastapi
        import uvicorn
        print(f"✅ FastAPI: {fastapi.__version__}")
        print(f"✅ Uvicorn: {uvicorn.__version__}")
        tests.append(True)
        tests.append(True)
    except ImportError as e:
        print(f"❌ Web框架: {e}")
        tests.append(False)
    
    # 4. 浏览器自动化
    print("\n🎭 浏览器自动化:")
    try:
        import playwright
        print(f"✅ Playwright: 已安装")
        tests.append(True)
    except ImportError:
        print("❌ Playwright: 未安装")
        tests.append(False)
    
    # 5. Docker
    print("\n🐳 Docker容器化:")
    tests.append(test_tool("Docker", "docker --version"))
    
    # 6. Redis
    print("\n📮 Redis消息队列:")
    tests.append(test_tool("Redis", "redis-cli ping"))
    
    # 总结
    print("\n" + "="*60)
    passed = sum(tests)
    total = len(tests)
    print(f"测试结果: {passed}/{total} 通过 ({passed/total*100:.0f}%)")
    print("="*60)
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
