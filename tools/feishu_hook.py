#!/usr/bin/env python3
"""
飞书消息实时保存钩子
集成到 OpenClaw 消息处理流程

使用方法:
  在 OpenClaw 处理飞书消息时调用:
  python3 tools/feishu_hook.py save <json_file>
  
  或在 Python 中直接调用:
  from feishu_hook import save_inbound_message
  save_inbound_message(message_data)
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 添加工具路径
sys.path.insert(0, str(Path(__file__).parent))


def extract_message_data(inbound_json):
    """从 OpenClaw 入站格式提取消息数据
    
    支持的格式:
    1. OpenClaw 标准入站格式:
    {
        "schema": "openclaw.inbound_meta.v1",
        "channel": "feishu",
        "chat_type": "direct",
        "message": {
            "content": "..."
        }
    }
    
    2. 简化格式:
    {
        "content": "...",
        "sender_name": "..."
    }
    """
    try:
        # 尝试解析为 OpenClaw 标准格式
        if isinstance(inbound_json, str):
            data = json.loads(inbound_json)
        else:
            data = inbound_json
        
        # 提取消息ID
        message_id = None
        if 'message' in data and isinstance(data['message'], dict):
            message_id = data['message'].get('id')
        if not message_id:
            message_id = f"msg_{int(datetime.now().timestamp() * 1000)}"
        
        # 提取发送者信息
        sender_id = 'unknown'
        sender_name = 'unknown'
        if 'message' in data and 'sender' in data['message']:
            sender = data['message']['sender']
            sender_id = sender.get('id', 'unknown')
            sender_name = sender.get('name', 'unknown')
        
        # 提取聊天信息
        chat_type = data.get('chat_type', 'unknown')
        chat_id = data.get('conversation_label', 'unknown')
        
        # 提取内容
        content = ''
        if 'message' in data and isinstance(data['message'], dict):
            content = data['message'].get('content', '')
        if not content and 'content' in data:
            content = data['content']
        
        return {
            'message_id': message_id,
            'sender_id': sender_id,
            'sender_name': sender_name,
            'chat_type': chat_type,
            'chat_id': chat_id,
            'content': content,
            'content_type': 'text',
            'raw_data': data
        }
    except Exception as e:
        print(f"❌ 解析消息失败: {e}")
        return None


def save_inbound_message(message_data):
    """保存入站消息到RDS
    
    Args:
        message_data: dict 或 json字符串
    
    Returns:
        bool: 是否成功
    """
    try:
        from feishu_sync import FeishuMessageSync
        
        # 解析消息
        if isinstance(message_data, str):
            data = extract_message_data(message_data)
        else:
            data = extract_message_data(message_data)
        
        if not data:
            return False
        
        # 创建同步器并保存
        sync = FeishuMessageSync()
        success = sync.save_message(data)
        
        if success:
            print(f"✅ 消息已保存: {data['sender_name']}: {data['content'][:30]}...")
        else:
            print(f"⚠️ 消息已加入队列: {data['sender_name']}")
        
        return success
        
    except Exception as e:
        print(f"❌ 保存失败: {e}")
        return False


def main():
    """命令行入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("🔗 飞书消息实时保存钩子")
        print("\n用法:")
        print("  python3 feishu_hook.py save '<json>'     # 保存JSON消息")
        print("  python3 feishu_hook.py test              # 测试")
        print("\n环境变量:")
        print("  FEISHU_MESSAGE_JSON - 消息JSON")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'save':
        if len(sys.argv) < 3:
            # 尝试从环境变量读取
            json_str = os.environ.get('FEISHU_MESSAGE_JSON')
            if not json_str:
                print("❌ 请提供JSON消息或设置 FEISHU_MESSAGE_JSON")
                sys.exit(1)
        else:
            json_str = sys.argv[2]
        
        success = save_inbound_message(json_str)
        sys.exit(0 if success else 1)
    
    elif cmd == 'test':
        test_data = {
            "schema": "openclaw.inbound_meta.v1",
            "channel": "feishu",
            "chat_type": "direct",
            "conversation_label": "user:test",
            "message": {
                "id": f"test_{int(datetime.now().timestamp())}",
                "content": "这是一条测试消息，验证实时同步功能",
                "sender": {
                    "id": "ou_test",
                    "name": "测试用户"
                }
            }
        }
        success = save_inbound_message(test_data)
        sys.exit(0 if success else 1)
    
    else:
        print(f"❌ 未知命令: {cmd}")
        sys.exit(1)


if __name__ == '__main__':
    main()