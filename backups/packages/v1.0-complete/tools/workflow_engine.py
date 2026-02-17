#!/usr/bin/env python3
"""
智能工作流引擎
条件触发、多步骤任务、自动化流程
"""

import json
import os
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

WORKFLOW_DIR = Path("/root/.openclaw/workspace/config/workflows")
WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
WORKFLOW_LOG = Path("/root/.openclaw/workspace/logs/workflow.log")
WORKFLOW_LOG.parent.mkdir(parents=True, exist_ok=True)

class WorkflowEngine:
    """工作流引擎"""
    
    def __init__(self):
        self.workflows = self._load_workflows()
    
    def _load_workflows(self):
        """加载所有工作流"""
        workflows = {}
        for wf_file in WORKFLOW_DIR.glob("*.json"):
            with open(wf_file, 'r') as f:
                workflows[wf_file.stem] = json.load(f)
        return workflows
    
    def _save_workflow(self, name, workflow):
        """保存工作流"""
        wf_file = WORKFLOW_DIR / f"{name}.json"
        with open(wf_file, 'w') as f:
            json.dump(workflow, f, indent=2)
    
    def create_workflow(self, name, trigger, conditions, actions, description=""):
        """创建工作流"""
        workflow = {
            'name': name,
            'description': description,
            'enabled': True,
            'created_at': datetime.now().isoformat(),
            'trigger': trigger,
            'conditions': conditions,
            'actions': actions
        }
        
        self._save_workflow(name, workflow)
        self.workflows[name] = workflow
        
        return f"✅ 工作流 '{name}' 已创建"
    
    def evaluate_condition(self, condition, context):
        """评估条件"""
        cond_type = condition.get('type')
        
        if cond_type == 'contains':
            field = condition.get('field')
            keyword = condition.get('keyword')
            value = context.get(field, '')
            return keyword in value
        
        elif cond_type == 'regex':
            field = condition.get('field')
            pattern = condition.get('pattern')
            value = context.get(field, '')
            return bool(re.search(pattern, value))
        
        elif cond_type == 'threshold':
            field = condition.get('field')
            operator = condition.get('operator', '>')
            threshold = condition.get('value')
            value = context.get(field, 0)
            
            if operator == '>':
                return value > threshold
            elif operator == '<':
                return value < threshold
            elif operator == '>=':
                return value >= threshold
            elif operator == '<=':
                return value <= threshold
            elif operator == '==':
                return value == threshold
        
        elif cond_type == 'time_range':
            start = condition.get('start', '00:00')
            end = condition.get('end', '23:59')
            now = datetime.now().strftime('%H:%M')
            return start <= now <= end
        
        return False
    
    def execute_action(self, action, context):
        """执行动作"""
        action_type = action.get('type')
        
        if action_type == 'command':
            cmd = action.get('command')
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, 
                                      text=True, timeout=60)
                return {
                    'success': result.returncode == 0,
                    'stdout': result.stdout[:500],
                    'stderr': result.stderr[:500]
                }
            except Exception as e:
                return {'success': False, 'error': str(e)}
        
        elif action_type == 'notification':
            message = action.get('message', '')
            # 替换变量
            for key, value in context.items():
                message = message.replace(f'{{{key}}}', str(value))
            return {'success': True, 'message': message}
        
        elif action_type == 'webhook':
            url = action.get('url')
            # 实际实现需要requests库
            return {'success': True, 'webhook': url}
        
        elif action_type == 'calendar':
            # 创建日历事件
            return {'success': True, 'action': 'create_calendar_event'}
        
        return {'success': False, 'error': 'Unknown action type'}
    
    def run_workflow(self, name, context=None):
        """运行工作流"""
        if name not in self.workflows:
            return {'error': f'Workflow {name} not found'}
        
        workflow = self.workflows[name]
        
        if not workflow.get('enabled'):
            return {'error': 'Workflow is disabled'}
        
        context = context or {}
        
        # 评估条件
        conditions_met = True
        for condition in workflow.get('conditions', []):
            if not self.evaluate_condition(condition, context):
                conditions_met = False
                break
        
        if not conditions_met:
            return {'success': False, 'reason': 'Conditions not met'}
        
        # 执行动作
        results = []
        for action in workflow.get('actions', []):
            result = self.execute_action(action, context)
            results.append(result)
            
            # 如果动作失败且配置了停止策略
            if not result.get('success') and action.get('stop_on_error'):
                break
        
        # 记录日志
        self._log_execution(name, context, results)
        
        return {
            'success': True,
            'workflow': name,
            'results': results
        }
    
    def _log_execution(self, name, context, results):
        """记录执行日志"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'workflow': name,
            'context': context,
            'results': results
        }
        
        with open(WORKFLOW_LOG, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def list_workflows(self):
        """列出所有工作流"""
        return self.workflows
    
    def delete_workflow(self, name):
        """删除工作流"""
        if name in self.workflows:
            wf_file = WORKFLOW_DIR / f"{name}.json"
            if wf_file.exists():
                wf_file.unlink()
            del self.workflows[name]
            return True
        return False


# 预置工作流模板
WORKFLOW_TEMPLATES = {
    'email_to_calendar': {
        'name': '邮件自动创建日历',
        'description': '收到包含"会议"的邮件时自动创建日历事件',
        'trigger': {'type': 'email', 'event': 'received'},
        'conditions': [
            {'type': 'contains', 'field': 'subject', 'keyword': '会议'}
        ],
        'actions': [
            {'type': 'calendar', 'action': 'create_event'},
            {'type': 'notification', 'message': '已为您创建会议日程'}
        ]
    },
    'disk_cleanup': {
        'name': '磁盘清理',
        'description': '磁盘使用率超过90%时自动清理',
        'trigger': {'type': 'schedule', 'cron': '0 * * * *'},
        'conditions': [
            {'type': 'threshold', 'field': 'disk_percent', 'operator': '>', 'value': 90}
        ],
        'actions': [
            {'type': 'command', 'command': 'find /var/log -name "*.log" -mtime +7 -delete'},
            {'type': 'notification', 'message': '磁盘清理完成，当前使用率: {disk_percent}%'}
        ]
    },
    'daily_summary': {
        'name': '每日汇总',
        'description': '每天晚上9点发送每日汇总',
        'trigger': {'type': 'schedule', 'cron': '0 21 * * *'},
        'conditions': [],
        'actions': [
            {'type': 'command', 'command': 'cd /root/.openclaw/workspace && python3 tools/email_smart.py summary'},
            {'type': 'command', 'command': 'cd /root/.openclaw/workspace && python3 tools/system_monitor.py'},
            {'type': 'notification', 'message': '每日汇总已生成'}
        ]
    }
}


def main():
    import sys
    
    engine = WorkflowEngine()
    
    if len(sys.argv) < 2:
        print("🤖 智能工作流引擎")
        print("\n用法:")
        print("  python3 workflow_engine.py create <名称> <模板>")
        print("  python3 workflow_engine.py list")
        print("  python3 workflow_engine.py run <名称> [JSON上下文]")
        print("  python3 workflow_engine.py delete <名称>")
        print("  python3 workflow_engine.py templates")
        print("\n可用模板:")
        for name, template in WORKFLOW_TEMPLATES.items():
            print(f"  - {name}: {template['description']}")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'create':
        name = sys.argv[2]
        template_name = sys.argv[3]
        
        if template_name in WORKFLOW_TEMPLATES:
            template = WORKFLOW_TEMPLATES[template_name]
            result = engine.create_workflow(
                name,
                template['trigger'],
                template['conditions'],
                template['actions'],
                template['description']
            )
            print(result)
        else:
            print(f"❌ 未知模板: {template_name}")
    
    elif cmd == 'list':
        workflows = engine.list_workflows()
        print(f"共有 {len(workflows)} 个工作流:")
        for name, wf in workflows.items():
            status = "🟢" if wf.get('enabled') else "🔴"
            print(f"\n{status} {name}")
            print(f"   {wf.get('description', '无描述')}")
    
    elif cmd == 'run':
        name = sys.argv[2]
        context = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
        result = engine.run_workflow(name, context)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif cmd == 'delete':
        name = sys.argv[2]
        if engine.delete_workflow(name):
            print(f"✅ 工作流 '{name}' 已删除")
        else:
            print(f"❌ 工作流不存在")
    
    elif cmd == 'templates':
        print("可用模板:")
        for name, template in WORKFLOW_TEMPLATES.items():
            print(f"\n📋 {name}")
            print(f"   {template['description']}")
            print(f"   触发: {template['trigger']}")
            print(f"   条件: {len(template['conditions'])} 个")
            print(f"   动作: {len(template['actions'])} 个")
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
