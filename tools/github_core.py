#!/usr/bin/env python3
"""
GitHub 核心同步工具
将本地代码、配置、状态同步到 GitHub
作为代码层核心，防止本地服务器崩溃丢失数据
"""

import json
import os
import subprocess
import requests
from datetime import datetime
from pathlib import Path

# 配置
CONFIG_FILE = "/root/.openclaw/workspace/config/github_core.json"
WORKSPACE = "/root/.openclaw/workspace"

def load_config():
    """加载 GitHub 核心配置"""
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def sync_to_github(config, message=None):
    """同步本地更改到 GitHub"""
    
    os.chdir(WORKSPACE)
    
    # 检查 git 状态
    result = subprocess.run(
        ['git', 'status', '--porcelain'],
        capture_output=True,
        text=True
    )
    
    if not result.stdout.strip():
        print("✅ 没有需要同步的更改")
        return True
    
    # 添加所有更改
    subprocess.run(['git', 'add', '-A'], check=True)
    
    # 提交
    commit_msg = message or f"自动同步 - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
    
    # 先拉取远程更改（避免冲突）
    print("  📥 拉取远程更改...")
    subprocess.run(['git', 'pull', 'origin', 'main', '--rebase'], check=False)
    
    # 推送到 GitHub
    subprocess.run(['git', 'push', 'origin', 'main'], check=True)
    
    print(f"✅ 已同步到 GitHub: {commit_msg}")
    return True

def create_issue(config, title, body, labels=None):
    """在 GitHub 创建 Issue"""
    
    url = f"{config['api_base']}/repos/{config['owner']}/{config['repo']}/issues"
    headers = {
        "Authorization": f"token {config['token']}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "title": title,
        "body": body
    }
    
    if labels:
        data["labels"] = labels
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 201:
        issue = response.json()
        print(f"✅ Issue 创建成功: #{issue['number']} - {issue['title']}")
        return issue
    else:
        print(f"❌ 创建 Issue 失败: {response.status_code} - {response.text}")
        return None

def list_issues(config, state="open"):
    """列出 GitHub Issues"""
    
    url = f"{config['api_base']}/repos/{config['owner']}/{config['repo']}/issues"
    headers = {
        "Authorization": f"token {config['token']}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    params = {"state": state}
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        issues = response.json()
        print(f"📋 找到 {len(issues)} 个 Issues:")
        for issue in issues:
            labels = ', '.join([l['name'] for l in issue['labels']])
            print(f"  #{issue['number']}: {issue['title']} [{labels}]")
        return issues
    else:
        print(f"❌ 获取 Issues 失败: {response.status_code}")
        return []

def trigger_workflow(config, workflow_id="sync-status.yml"):
    """触发 GitHub Actions 工作流"""
    
    url = f"{config['api_base']}/repos/{config['owner']}/{config['repo']}/actions/workflows/{workflow_id}/dispatches"
    headers = {
        "Authorization": f"token {config['token']}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    data = {
        "ref": config['primary_branch']
    }
    
    response = requests.post(url, headers=headers, json=data)
    
    if response.status_code == 204:
        print(f"✅ 工作流 {workflow_id} 已触发")
        return True
    else:
        print(f"❌ 触发工作流失败: {response.status_code} - {response.text}")
        return False

def backup_critical_files(config):
    """备份关键文件到 GitHub"""
    
    critical_paths = [
        "config/",
        "tools/",
        "SOUL.md",
        "USER.md",
        "MEMORY.md",
        "AGENTS.md",
        "HEARTBEAT.md",
        "IDENTITY.md",
    ]
    
    print("🔄 开始备份关键文件...")
    
    for path in critical_paths:
        full_path = os.path.join(WORKSPACE, path)
        if os.path.exists(full_path):
            print(f"  📄 {path}")
    
    # 执行同步
    sync_to_github(config, f"关键文件备份 - {datetime.now().strftime('%Y-%m-%d %H:%M')}")

def main():
    """主函数"""
    import sys
    
    config = load_config()
    
    if len(sys.argv) < 2:
        print("""
GitHub 核心同步工具

用法:
  python3 github_core.py sync [message]     - 同步到 GitHub
  python3 github_core.py issue title body   - 创建 Issue
  python3 github_core.py issues [state]     - 列出 Issues
  python3 github_core.py workflow [id]      - 触发工作流
  python3 github_core.py backup             - 备份关键文件
        """)
        return
    
    cmd = sys.argv[1]
    
    if cmd == "sync":
        message = sys.argv[2] if len(sys.argv) > 2 else None
        sync_to_github(config, message)
    
    elif cmd == "issue":
        if len(sys.argv) < 4:
            print("❌ 需要标题和正文")
            return
        title = sys.argv[2]
        body = sys.argv[3]
        labels = sys.argv[4].split(',') if len(sys.argv) > 4 else None
        create_issue(config, title, body, labels)
    
    elif cmd == "issues":
        state = sys.argv[2] if len(sys.argv) > 2 else "open"
        list_issues(config, state)
    
    elif cmd == "workflow":
        workflow_id = sys.argv[2] if len(sys.argv) > 2 else "sync-status.yml"
        trigger_workflow(config, workflow_id)
    
    elif cmd == "backup":
        backup_critical_files(config)
    
    else:
        print(f"❌ 未知命令: {cmd}")

if __name__ == "__main__":
    main()