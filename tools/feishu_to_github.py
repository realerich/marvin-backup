#!/usr/bin/env python3
"""
飞书消息到 GitHub Issue 自动转换
识别飞书中的任务/问题，自动创建 GitHub Issue
"""

import json
import re
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

# GitHub 配置
GITHUB_CONFIG = {
    'owner': 'realerich',
    'repo': 'marvin-backup',
    'token': None  # 从配置文件读取
}


def load_github_token():
    """加载 GitHub Token"""
    config_file = Path("/root/.openclaw/workspace/config/github_config.json")
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = json.load(f)
            return config.get('token')
    return None


class FeishuToGitHub:
    """飞书消息转 GitHub Issue"""
    
    # 任务关键词
    TASK_KEYWORDS = [
        '任务', 'todo', '待办', '记得', '别忘了', '需要',
        '修复', '修复一下', '改一下', '修改', '更新',
        '添加', '创建', '删除', '检查', '测试',
        'task:', 'todo:', '[task]', '[todo]'
    ]
    
    # 问题关键词
    BUG_KEYWORDS = [
        'bug', '错误', '问题', '故障', '崩溃', '异常',
        '不工作', '失败', '报错', 'error', 'issue',
        '[bug]', '[issue]', 'fix:'
    ]
    
    # 功能请求关键词
    FEATURE_KEYWORDS = [
        '功能', 'feature', '新增', '增加', '支持', '实现',
        '能不能', '能不能加', '建议', '想要', '希望',
        '[feature]', 'feat:'
    ]
    
    def __init__(self):
        self.token = load_github_token()
    
    def classify_message(self, content):
        """分类消息类型"""
        content_lower = content.lower()
        
        # 检查 Bug 报告
        for kw in self.BUG_KEYWORDS:
            if kw in content_lower:
                return 'bug', 0.9
        
        # 检查功能请求
        for kw in self.FEATURE_KEYWORDS:
            if kw in content_lower:
                return 'feature', 0.8
        
        # 检查任务
        for kw in self.TASK_KEYWORDS:
            if kw in content_lower:
                return 'task', 0.7
        
        return None, 0
    
    def extract_title(self, content, msg_type):
        """提取 Issue 标题"""
        # 尝试提取第一行或前 50 个字符
        lines = content.strip().split('\n')
        first_line = lines[0].strip()
        
        # 移除常见的命令前缀
        prefixes = ['任务:', 'todo:', 'bug:', 'fix:', 'feature:', 'feat:']
        for prefix in prefixes:
            if first_line.lower().startswith(prefix):
                first_line = first_line[len(prefix):].strip()
        
        # 截取前 80 个字符作为标题
        title = first_line[:80]
        if len(first_line) > 80:
            title += '...'
        
        # 添加前缀
        prefix_map = {
            'bug': '[BUG]',
            'feature': '[FEATURE]',
            'task': '[TASK]'
        }
        if msg_type in prefix_map:
            title = f"{prefix_map[msg_type]} {title}"
        
        return title
    
    def create_github_issue(self, title, body, labels=None):
        """创建 GitHub Issue"""
        import requests
        
        if not self.token:
            print("❌ GitHub Token 未配置")
            return None
        
        url = f"https://api.github.com/repos/{GITHUB_CONFIG['owner']}/{GITHUB_CONFIG['repo']}/issues"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        data = {
            "title": title,
            "body": body
        }
        
        if labels:
            data["labels"] = labels
        
        try:
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                issue = response.json()
                print(f"✅ Issue 创建成功: #{issue['number']} - {issue['title']}")
                return issue
            else:
                print(f"❌ 创建 Issue 失败: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ 请求失败: {e}")
            return None
    
    def process_message(self, content, sender_name=None, created_at=None):
        """处理飞书消息"""
        # 分类
        msg_type, confidence = self.classify_message(content)
        
        if not msg_type or confidence < 0.7:
            return None  # 不需要创建 Issue
        
        # 提取标题
        title = self.extract_title(content, msg_type)
        
        # 构建正文
        body_lines = [
            f"**来源**: 飞书消息",
        ]
        if sender_name:
            body_lines.append(f"**发送者**: {sender_name}")
        if created_at:
            body_lines.append(f"**时间**: {created_at}")
        
        body_lines.extend([
            "",
            "**原始内容**:",
            "```",
            content,
            "```"
        ])
        
        body = "\n".join(body_lines)
        
        # 标签映射
        label_map = {
            'bug': ['bug'],
            'feature': ['enhancement'],
            'task': ['task']
        }
        labels = label_map.get(msg_type, [])
        
        # 创建 Issue
        issue = self.create_github_issue(title, body, labels)
        
        return issue
    
    def scan_and_convert(self, limit=10):
        """扫描未处理的飞书消息并转换"""
        try:
            from feishu_rds import FeishuMessageRDS
            
            feishu_db = FeishuMessageRDS()
            
            # 获取未处理的消息
            with feishu_db.manager.pool.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        SELECT * FROM feishu_messages
                        WHERE is_processed = FALSE
                        ORDER BY created_at DESC
                        LIMIT %s
                    """, (limit,))
                    
                    rows = cursor.fetchall()
                    
                    converted = 0
                    for row in rows:
                        msg_id = row[1]
                        sender_name = row[3]
                        content = row[6]
                        created_at = row[9]
                        
                        # 处理消息
                        issue = self.process_message(content, sender_name, created_at)
                        
                        if issue:
                            # 标记为已处理
                            feishu_db.mark_processed(msg_id, f"github_issue_{issue['number']}")
                            converted += 1
                    
                    print(f"✅ 转换 {converted}/{len(rows)} 条消息到 GitHub Issue")
                    return converted
                    
        except Exception as e:
            print(f"❌ 扫描失败: {e}")
            return 0


def main():
    """命令行工具"""
    import sys
    
    converter = FeishuToGitHub()
    
    if len(sys.argv) < 2:
        print("🔄 飞书消息转 GitHub Issue")
        print("\n用法:")
        print("  python3 feishu_to_github.py scan [limit]    # 扫描未处理消息")
        print("  python3 feishu_to_github.py convert <内容>   # 转换单条消息")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'scan':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        converter.scan_and_convert(limit)
    
    elif cmd == 'convert':
        if len(sys.argv) < 3:
            print("❌ 请提供消息内容")
            sys.exit(1)
        content = sys.argv[2]
        converter.process_message(content)
    
    else:
        print(f"❌ 未知命令: {cmd}")


if __name__ == '__main__':
    main()