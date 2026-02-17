#!/usr/bin/env python3
"""
飞书消息自动保存钩子
集成到 OpenClaw 消息处理流程中

使用方法:
1. 将此脚本设置为 OpenClaw 的 webhook 处理器
2. 或使用 cron 定期同步
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加工具路径
sys.path.insert(0, str(Path(__file__).parent))


class FeishuMessageSync:
    """飞书消息同步器"""
    
    def __init__(self):
        self.enabled = True
        self.fallback_file = Path("/root/.openclaw/workspace/data/feishu_messages_queue.json")
        self._init_fallback()
    
    def _init_fallback(self):
        """初始化本地队列文件"""
        self.fallback_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.fallback_file.exists():
            with open(self.fallback_file, 'w') as f:
                json.dump([], f)
    
    def _save_to_fallback(self, message_data):
        """保存到本地队列（RDS失败时备用）"""
        try:
            with open(self.fallback_file, 'r+') as f:
                queue = json.load(f)
                queue.append({
                    **message_data,
                    'queued_at': datetime.now().isoformat()
                })
                f.seek(0)
                json.dump(queue, f, indent=2, default=str)
                f.truncate()
            return True
        except Exception as e:
            print(f"❌ 本地队列保存失败: {e}")
            return False
    
    def _sync_fallback_to_rds(self):
        """将本地队列同步到RDS"""
        try:
            from feishu_rds import FeishuMessageRDS
            
            with open(self.fallback_file, 'r') as f:
                queue = json.load(f)
            
            if not queue:
                return 0
            
            tool = FeishuMessageRDS()
            synced = 0
            failed = []
            
            for msg in queue:
                success = tool.save_message(
                    message_id=msg.get('message_id'),
                    sender_id=msg.get('sender_id'),
                    sender_name=msg.get('sender_name'),
                    chat_type=msg.get('chat_type'),
                    chat_id=msg.get('chat_id'),
                    content=msg.get('content'),
                    content_type=msg.get('content_type', 'text')
                )
                if success:
                    synced += 1
                else:
                    failed.append(msg)
            
            # 更新队列（只保留失败的）
            with open(self.fallback_file, 'w') as f:
                json.dump(failed, f, indent=2, default=str)
            
            return synced
            
        except Exception as e:
            print(f"❌ 同步队列失败: {e}")
            return 0
    
    def save_message(self, message_data: dict) -> bool:
        """保存消息 - 优先RDS，失败则本地队列"""
        try:
            from feishu_rds import FeishuMessageRDS
            
            tool = FeishuMessageRDS()
            success = tool.save_message(
                message_id=message_data.get('message_id'),
                sender_id=message_data.get('sender_id'),
                sender_name=message_data.get('sender_name'),
                chat_type=message_data.get('chat_type'),
                chat_id=message_data.get('chat_id'),
                content=message_data.get('content'),
                content_type=message_data.get('content_type', 'text')
            )
            
            if success:
                # 检查是否有待同步的本地队列
                self._sync_fallback_to_rds()
                return True
            else:
                # RDS失败，保存到本地队列
                print("⚠️ RDS保存失败，写入本地队列")
                return self._save_to_fallback(message_data)
                
        except Exception as e:
            print(f"❌ 保存异常: {e}")
            return self._save_to_fallback(message_data)
    
    def process_inbound_message(self, inbound_data: dict) -> bool:
        """处理 OpenClaw 入站消息格式
        
        inbound_data 格式:
        {
            'schema': 'openclaw.inbound_meta.v1',
            'channel': 'feishu',
            'provider': 'feishu',
            'chat_type': 'direct',
            'flags': {...},
            'message': {
                'id': '...',
                'content': '...',
                'sender': {
                    'id': 'ou_...',
                    'name': '...'
                }
            }
        }
        """
        try:
            # 提取消息数据
            message_data = {
                'message_id': inbound_data.get('message', {}).get('id') or f"msg_{datetime.now().timestamp()}",
                'sender_id': inbound_data.get('message', {}).get('sender', {}).get('id', 'unknown'),
                'sender_name': inbound_data.get('message', {}).get('sender', {}).get('name', 'unknown'),
                'chat_type': inbound_data.get('chat_type', 'unknown'),
                'chat_id': inbound_data.get('conversation_label', 'unknown'),
                'content': inbound_data.get('message', {}).get('content', ''),
                'content_type': 'text'
            }
            
            return self.save_message(message_data)
            
        except Exception as e:
            print(f"❌ 处理入站消息失败: {e}")
            return False
    
    def sync_queue(self) -> dict:
        """手动触发队列同步"""
        synced = self._sync_fallback_to_rds()
        
        with open(self.fallback_file, 'r') as f:
            remaining = len(json.load(f))
        
        return {
            'synced': synced,
            'remaining': remaining,
            'timestamp': datetime.now().isoformat()
        }


def main():
    """命令行工具"""
    import sys
    
    sync = FeishuMessageSync()
    
    if len(sys.argv) < 2:
        print("🔄 飞书消息同步工具")
        print("\n用法:")
        print("  python3 feishu_sync.py sync          # 同步本地队列到RDS")
        print("  python3 feishu_sync.py test          # 测试保存功能")
        print("  python3 feishu_sync.py status        # 查看队列状态")
        print("\n环境变量:")
        print("  FEISHU_MSG_JSON - JSON格式的消息数据")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'sync':
        result = sync.sync_queue()
        print(f"✅ 已同步 {result['synced']} 条消息")
        print(f"📋 队列剩余: {result['remaining']} 条")
    
    elif cmd == 'test':
        test_msg = {
            'message_id': f'test_{int(datetime.now().timestamp())}',
            'sender_id': 'test_user',
            'sender_name': '测试用户',
            'chat_type': 'direct',
            'chat_id': 'test_chat',
            'content': '这是一条测试消息',
            'content_type': 'text'
        }
        success = sync.save_message(test_msg)
        print(f"{'✅' if success else '❌'} 测试保存: {'成功' if success else '失败'}")
    
    elif cmd == 'status':
        with open(sync.fallback_file, 'r') as f:
            queue = json.load(f)
        print(f"📋 本地队列: {len(queue)} 条消息待同步")
        if queue:
            print("\n最近3条:")
            for msg in queue[-3:]:
                print(f"  - {msg.get('sender_name')}: {msg.get('content', '')[:30]}...")
    
    elif cmd == 'process':
        # 从环境变量读取JSON
        json_str = os.environ.get('FEISHU_MSG_JSON')
        if not json_str:
            print("❌ 未设置 FEISHU_MSG_JSON")
            sys.exit(1)
        
        try:
            data = json.loads(json_str)
            success = sync.process_inbound_message(data)
            sys.exit(0 if success else 1)
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            sys.exit(1)
    
    else:
        print(f"❌ 未知命令: {cmd}")


if __name__ == '__main__':
    main()