#!/usr/bin/env python3
"""
智能工作流引擎 - 增强版
整合四层架构：飞书、RDS、ECS、GitHub
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import subprocess

sys.path.insert(0, str(Path(__file__).parent))

# 导入各层工具
from feishu_rds import FeishuMessageRDS
from rds_github_sync import RDSGitHubSync


class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.rds = FeishuMessageRDS()
        self.github_sync = RDSGitHubSync()
        self.workflows = self._load_workflows()
    
    def _load_workflows(self):
        """加载预定义工作流"""
        return {
            'morning_routine': {
                'name': '晨间例行',
                'schedule': '0 8 * * 1-5',
                'steps': [
                    {'action': 'market_briefing', 'target': 'feishu'},
                    {'action': 'check_emails', 'target': 'feishu+rds'},
                    {'action': 'sync_github', 'target': 'github'},
                ]
            },
            'system_health_check': {
                'name': '系统健康检查',
                'schedule': '0 * * * *',
                'steps': [
                    {'action': 'system_monitor', 'target': 'rds'},
                    {'action': 'check_alerts', 'target': 'feishu'},
                    {'action': 'update_github_status', 'target': 'github'},
                ]
            },
            'data_sync': {
                'name': '数据同步',
                'schedule': '0 */6 * * *',
                'steps': [
                    {'action': 'export_metrics', 'target': 'github'},
                    {'action': 'export_tasks', 'target': 'github'},
                    {'action': 'sync_feishu_to_github', 'target': 'github'},
                ]
            },
            'daily_cleanup': {
                'name': '每日清理',
                'schedule': '0 2 * * *',
                'steps': [
                    {'action': 'archive_old_emails', 'target': 'rds'},
                    {'action': 'cleanup_logs', 'target': 'ecs'},
                    {'action': 'backup_to_github', 'target': 'github'},
                ]
            }
        }
    
    def execute_step(self, step: Dict[str, str]) -> bool:
        """执行单个步骤"""
        action = step['action']
        target = step['target']
        
        print(f"  → 执行: {action} → {target}")
        
        try:
            if action == 'market_briefing':
                return self._run_market_briefing(target)
            elif action == 'check_emails':
                return self._check_emails(target)
            elif action == 'system_monitor':
                return self._system_monitor(target)
            elif action == 'sync_github':
                return self._sync_to_github()
            elif action == 'export_metrics':
                return self.github_sync.export_system_metrics(days=7)
            elif action == 'export_tasks':
                return self.github_sync.export_tasks()
            elif action == 'sync_feishu_to_github':
                return self._sync_feishu_to_github()
            else:
                print(f"    ⚠️ 未知动作: {action}")
                return False
        except Exception as e:
            print(f"    ❌ 执行失败: {e}")
            return False
    
    def _run_market_briefing(self, target):
        """运行盘前简报"""
        result = subprocess.run(
            ['python3', 'tools/market_briefing.py'],
            capture_output=True,
            text=True,
            cwd='/root/.openclaw/workspace'
        )
        
        if result.returncode == 0:
            print(f"    ✅ 盘前简报生成成功")
            # TODO: 发送到飞书
            return True
        return False
    
    def _check_emails(self, target):
        """检查邮件"""
        result = subprocess.run(
            ['python3', 'tools/email_check.py'],
            capture_output=True,
            text=True,
            cwd='/root/.openclaw/workspace'
        )
        
        success = result.returncode == 0
        if success and 'feishu' in target:
            # 保存到 RDS
            pass
        return success
    
    def _system_monitor(self, target):
        """系统监控"""
        result = subprocess.run(
            ['python3', 'tools/system_monitor.py'],
            capture_output=True,
            text=True,
            cwd='/root/.openclaw/workspace'
        )
        return result.returncode == 0
    
    def _sync_to_github(self):
        """同步到 GitHub"""
        result = subprocess.run(
            ['python3', 'tools/github_core.py', 'backup'],
            capture_output=True,
            text=True,
            cwd='/root/.openclaw/workspace'
        )
        return result.returncode == 0
    
    def _sync_feishu_to_github(self):
        """同步飞书消息到 GitHub"""
        from feishu_to_github import FeishuToGitHub
        converter = FeishuToGitHub()
        count = converter.scan_and_convert(limit=5)
        return count >= 0
    
    def run_workflow(self, workflow_name: str) -> bool:
        """运行指定工作流"""
        if workflow_name not in self.workflows:
            print(f"❌ 未知工作流: {workflow_name}")
            return False
        
        workflow = self.workflows[workflow_name]
        print(f"\n🔄 运行工作流: {workflow['name']}")
        print("=" * 50)
        
        results = []
        for i, step in enumerate(workflow['steps'], 1):
            print(f"\n步骤 {i}/{len(workflow['steps'])}")
            results.append(self.execute_step(step))
        
        success = all(results)
        print("\n" + "=" * 50)
        print(f"{'✅' if success else '⚠️'} 工作流完成: {sum(results)}/{len(results)} 步骤成功")
        
        return success
    
    def run_all(self):
        """运行所有工作流"""
        print("🚀 运行所有工作流")
        print("=" * 50)
        
        results = {}
        for name in self.workflows:
            results[name] = self.run_workflow(name)
        
        print("\n" + "=" * 50)
        print("📊 工作流执行总结")
        for name, success in results.items():
            status = "✅" if success else "❌"
            print(f"  {status} {self.workflows[name]['name']}")
        
        return all(results.values())
    
    def list_workflows(self):
        """列出所有工作流"""
        print("📋 可用工作流")
        print("=" * 50)
        
        for name, workflow in self.workflows.items():
            print(f"\n{workflow['name']} ({name})")
            print(f"  定时: {workflow['schedule']}")
            print(f"  步骤: {len(workflow['steps'])}")
            for i, step in enumerate(workflow['steps'], 1):
                print(f"    {i}. {step['action']} → {step['target']}")


# 预定义工作流模板
WORKFLOW_TEMPLATES = {
    'task_from_feishu': {
        'name': '飞书任务自动处理',
        'trigger': 'feishu_message',
        'condition': 'content contains ["任务", "todo", "记得"]',
        'actions': [
            {'action': 'save_to_rds', 'table': 'tasks'},
            {'action': 'create_github_issue', 'label': 'task'},
            {'action': 'notify_user', 'message': '任务已创建'}
        ]
    },
    'alert_handler': {
        'name': '系统警报处理',
        'trigger': 'system_alert',
        'condition': 'severity in ["high", "critical"]',
        'actions': [
            {'action': 'notify_feishu', 'urgent': True},
            {'action': 'create_github_issue', 'label': 'alert'},
            {'action': 'log_to_rds', 'table': 'alerts'}
        ]
    },
    'daily_summary': {
        'name': '每日摘要生成',
        'trigger': 'cron(0 21 * * *)',
        'actions': [
            {'action': 'generate_summary', 'sources': ['tasks', 'emails', 'metrics']},
            {'action': 'save_to_rds', 'table': 'daily_reports'},
            {'action': 'send_to_feishu'}
        ]
    }
}


def main():
    """命令行工具"""
    import sys
    
    engine = WorkflowEngine()
    
    if len(sys.argv) < 2:
        print("🤖 智能工作流引擎")
        print("\n用法:")
        print("  python3 workflow_engine.py list           # 列出工作流")
        print("  python3 workflow_engine.py run <name>     # 运行指定工作流")
        print("  python3 workflow_engine.py run-all        # 运行所有工作流")
        print("\n示例:")
        print("  python3 workflow_engine.py run morning_routine")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'list':
        engine.list_workflows()
    
    elif cmd == 'run':
        if len(sys.argv) < 3:
            print("❌ 请指定工作流名称")
            sys.exit(1)
        workflow_name = sys.argv[2]
        engine.run_workflow(workflow_name)
    
    elif cmd == 'run-all':
        engine.run_all()
    
    else:
        print(f"❌ 未知命令: {cmd}")


if __name__ == '__main__':
    main()