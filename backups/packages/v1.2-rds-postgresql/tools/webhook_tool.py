#!/usr/bin/env python3
"""
Webhook触发器与自动化任务
支持外部HTTP请求触发本地动作
"""

import json
import os
import hashlib
import hmac
from datetime import datetime
from pathlib import Path

WEBHOOK_CONFIG = Path("/root/.openclaw/workspace/config/webhooks.json")
WEBHOOK_LOG = Path("/root/.openclaw/workspace/logs/webhook.log")

class WebhookManager:
    """Webhook管理器"""
    
    def __init__(self):
        self.config = self._load_config()
        WEBHOOK_LOG.parent.mkdir(parents=True, exist_ok=True)
    
    def _load_config(self):
        """加载配置"""
        if WEBHOOK_CONFIG.exists():
            with open(WEBHOOK_CONFIG, 'r') as f:
                return json.load(f)
        return {'webhooks': {}}
    
    def _save_config(self):
        """保存配置"""
        WEBHOOK_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        with open(WEBHOOK_CONFIG, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def create_webhook(self, name, action, secret=None):
        """创建新的webhook"""
        # 生成唯一ID
        webhook_id = hashlib.sha256(f"{name}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
        
        self.config['webhooks'][webhook_id] = {
            'name': name,
            'action': action,
            'secret': secret,
            'created_at': datetime.now().isoformat(),
            'trigger_count': 0
        }
        
        self._save_config()
        
        return {
            'webhook_id': webhook_id,
            'url': f'/webhook/{webhook_id}',
            'full_url': f'http://your-server:18789/webhook/{webhook_id}'
        }
    
    def list_webhooks(self):
        """列出所有webhook"""
        return self.config['webhooks']
    
    def delete_webhook(self, webhook_id):
        """删除webhook"""
        if webhook_id in self.config['webhooks']:
            del self.config['webhooks'][webhook_id]
            self._save_config()
            return True
        return False
    
    def trigger_webhook(self, webhook_id, data=None, signature=None):
        """触发webhook动作"""
        if webhook_id not in self.config['webhooks']:
            return {'error': 'Webhook not found'}
        
        hook = self.config['webhooks'][webhook_id]
        
        # 验证签名（如果有密钥）
        if hook.get('secret') and signature:
            expected = hmac.new(hook['secret'].encode(), json.dumps(data).encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(expected, signature):
                return {'error': 'Invalid signature'}
        
        # 执行动作
        action = hook['action']
        result = self._execute_action(action, data)
        
        # 更新计数
        hook['trigger_count'] += 1
        hook['last_triggered'] = datetime.now().isoformat()
        self._save_config()
        
        # 记录日志
        self._log_trigger(webhook_id, action, data, result)
        
        return {'success': True, 'action': action, 'result': result}
    
    def _execute_action(self, action, data):
        """执行具体动作"""
        import subprocess
        
        actions = {
            'backup': '/root/marvin-backup-github/marvin_daily_backup.sh',
            'email_check': 'cd /root/.openclaw/workspace && python3 tools/email_smart.py',
            'memory_stats': 'cd /root/.openclaw/workspace && python3 tools/memory_local.py stats',
            'restaurant_chart': 'cd /root/.openclaw/workspace && python3 tools/viz_tool.py restaurants',
        }
        
        if action in actions:
            try:
                result = subprocess.run(actions[action], shell=True, capture_output=True, text=True, timeout=60)
                return {
                    'stdout': result.stdout[:500],
                    'stderr': result.stderr[:500],
                    'returncode': result.returncode
                }
            except Exception as e:
                return {'error': str(e)}
        
        return {'message': f'Unknown action: {action}'}
    
    def _log_trigger(self, webhook_id, action, data, result):
        """记录触发日志"""
        with open(WEBHOOK_LOG, 'a') as f:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'webhook_id': webhook_id,
                'action': action,
                'data': data,
                'result': result
            }
            f.write(json.dumps(log_entry) + '\n')


def main():
    import sys
    
    manager = WebhookManager()
    
    if len(sys.argv) < 2:
        print("🔗 Webhook管理工具")
        print("\n用法:")
        print("  python3 webhook_tool.py create <名称> <动作> [密钥]")
        print("  python3 webhook_tool.py list")
        print("  python3 webhook_tool.py delete <webhook_id>")
        print("  python3 webhook_tool.py trigger <webhook_id> [JSON数据]")
        print("\n可用动作:")
        print("  - backup: 执行备份")
        print("  - email_check: 检查邮件")
        print("  - memory_stats: 内存统计")
        print("  - restaurant_chart: 生成餐厅图表")
        print("\n示例:")
        print("  python3 webhook_tool.py create '每日备份' backup")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'create':
        name = sys.argv[2]
        action = sys.argv[3]
        secret = sys.argv[4] if len(sys.argv) > 4 else None
        result = manager.create_webhook(name, action, secret)
        print(f"✅ Webhook 创建成功!")
        print(f"   ID: {result['webhook_id']}")
        print(f"   URL: {result['full_url']}")
    
    elif cmd == 'list':
        hooks = manager.list_webhooks()
        print(f"📋 共有 {len(hooks)} 个 Webhook:")
        for wid, info in hooks.items():
            print(f"\n  {wid[:8]}... - {info['name']}")
            print(f"    动作: {info['action']}")
            print(f"    触发次数: {info.get('trigger_count', 0)}")
            if 'last_triggered' in info:
                print(f"    最后触发: {info['last_triggered']}")
    
    elif cmd == 'delete':
        wid = sys.argv[2]
        if manager.delete_webhook(wid):
            print(f"✅ Webhook {wid[:8]} 已删除")
        else:
            print(f"❌ Webhook 不存在")
    
    elif cmd == 'trigger':
        wid = sys.argv[2]
        data = json.loads(sys.argv[3]) if len(sys.argv) > 3 else None
        result = manager.trigger_webhook(wid, data)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
