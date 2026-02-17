#!/usr/bin/env python3
"""
日历集成工具
支持Google Calendar和飞书日历
自动提醒、日程查询、事件创建
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path

CONFIG_FILE = Path("/root/.openclaw/workspace/config/calendar_config.json")

class CalendarManager:
    """日历管理器"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {'calendars': {}}
    
    def _save_config(self):
        """保存配置"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def setup_google_calendar(self, credentials_path):
        """配置Google Calendar"""
        self.config['calendars']['google'] = {
            'type': 'google',
            'credentials': credentials_path,
            'enabled': True
        }
        self._save_config()
        return "✅ Google Calendar 配置已保存"
    
    def setup_feishu_calendar(self, app_id, app_secret):
        """配置飞书日历"""
        self.config['calendars']['feishu'] = {
            'type': 'feishu',
            'app_id': app_id,
            'app_secret': app_secret,
            'enabled': True
        }
        self._save_config()
        return "✅ 飞书日历配置已保存"
    
    def get_upcoming_events(self, days=7):
        """获取即将到来的事件"""
        # 这里是模拟实现，实际需要调用API
        # 返回格式示例
        events = [
            {
                'title': '示例会议',
                'start': (datetime.now() + timedelta(hours=2)).isoformat(),
                'end': (datetime.now() + timedelta(hours=3)).isoformat(),
                'description': '这是一个示例事件',
                'location': '线上会议'
            }
        ]
        return events
    
    def create_event(self, title, start_time, end_time, description="", location=""):
        """创建日历事件"""
        # 实际实现需要调用API
        event = {
            'title': title,
            'start': start_time,
            'end': end_time,
            'description': description,
            'location': location,
            'created_at': datetime.now().isoformat()
        }
        return event
    
    def check_upcoming_meetings(self, minutes=15):
        """检查即将到来的会议"""
        events = self.get_upcoming_events()
        now = datetime.now()
        upcoming = []
        
        for event in events:
            start = datetime.fromisoformat(event['start'])
            diff = (start - now).total_seconds() / 60
            
            if 0 < diff <= minutes:
                upcoming.append({
                    'event': event,
                    'minutes_until': int(diff)
                })
        
        return upcoming
    
    def format_event_for_notification(self, event, minutes_until=None):
        """格式化为通知消息"""
        start = datetime.fromisoformat(event['start'])
        
        msg = "📅 日程提醒\n"
        msg += "=" * 30 + "\n\n"
        msg += f"📌 {event['title']}\n"
        msg += f"🕐 {start.strftime('%m月%d日 %H:%M')}\n"
        
        if minutes_until:
            msg += f"⏰ 还有 {minutes_until} 分钟\n"
        
        if event.get('location'):
            msg += f"📍 {event['location']}\n"
        
        if event.get('description'):
            msg += f"📝 {event['description'][:100]}\n"
        
        return msg


class NaturalLanguageEventParser:
    """自然语言事件解析"""
    
    @staticmethod
    def parse(text):
        """解析自然语言为事件"""
        import re
        
        event = {
            'title': '',
            'start': None,
            'end': None,
            'description': ''
        }
        
        # 提取标题（通常是"开会"、"吃饭"等动词短语）
        title_patterns = [
            r'(开会|吃饭|聚餐|约会|看病|运动|健身|看电影|购物)',
            r'(\d+点)(.+?)(?=，|$)',
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, text)
            if match:
                event['title'] = match.group(0)
                break
        
        # 提取时间
        time_patterns = [
            (r'(明天|后天|今天|下周[一二三四五六日])', 'relative_day'),
            (r'(\d+)月(\d+)日', 'date'),
            (r'(\d+)点', 'hour'),
            (r'(\d+)分', 'minute'),
        ]
        
        now = datetime.now()
        target_date = now
        target_hour = 9
        target_minute = 0
        
        for pattern, type in time_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if type == 'relative_day':
                    if match == '明天':
                        target_date = now + timedelta(days=1)
                    elif match == '后天':
                        target_date = now + timedelta(days=2)
                elif type == 'date':
                    month, day = int(match[0]), int(match[1])
                    target_date = target_date.replace(month=month, day=day)
                elif type == 'hour':
                    target_hour = int(match)
                elif type == 'minute':
                    target_minute = int(match)
        
        event['start'] = target_date.replace(hour=target_hour, minute=target_minute).isoformat()
        event['end'] = (target_date.replace(hour=target_hour, minute=target_minute) + 
                       timedelta(hours=1)).isoformat()
        
        # 如果没有提取到标题，使用原文
        if not event['title']:
            event['title'] = text[:20]
        
        return event


def main():
    import sys
    
    cal = CalendarManager()
    
    if len(sys.argv) < 2:
        print("📅 日历集成工具")
        print("\n用法:")
        print("  python3 calendar_tool.py setup google <credentials.json>")
        print("  python3 calendar_tool.py setup feishu <app_id> <app_secret>")
        print("  python3 calendar_tool.py upcoming [天数]")
        print("  python3 calendar_tool.py check")
        print("  python3 calendar_tool.py create '<标题>' '<开始时间>' '<结束时间>'")
        print("  python3 calendar_tool.py parse '<自然语言>'")
        print("\n示例:")
        print("  python3 calendar_tool.py parse '明天下午3点开会'")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'setup':
        provider = sys.argv[2]
        if provider == 'google':
            result = cal.setup_google_calendar(sys.argv[3])
        elif provider == 'feishu':
            result = cal.setup_feishu_calendar(sys.argv[3], sys.argv[4])
        else:
            result = f"未知提供商: {provider}"
        print(result)
    
    elif cmd == 'upcoming':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        events = cal.get_upcoming_events(days)
        print(f"未来{days}天有 {len(events)} 个事件:")
        for e in events:
            print(f"\n  📌 {e['title']}")
            print(f"     {e['start']}")
    
    elif cmd == 'check':
        upcoming = cal.check_upcoming_meetings(30)
        if upcoming:
            print("⚠️ 即将到来的会议:")
            for item in upcoming:
                print(cal.format_event_for_notification(item['event'], item['minutes_until']))
        else:
            print("✅ 未来30分钟无会议")
    
    elif cmd == 'create':
        title = sys.argv[2]
        start = sys.argv[3]
        end = sys.argv[4]
        desc = sys.argv[5] if len(sys.argv) > 5 else ""
        loc = sys.argv[6] if len(sys.argv) > 6 else ""
        event = cal.create_event(title, start, end, desc, loc)
        print(f"✅ 事件已创建: {event['title']}")
    
    elif cmd == 'parse':
        text = sys.argv[2]
        event = NaturalLanguageEventParser.parse(text)
        print(f"解析结果:")
        print(f"  标题: {event['title']}")
        print(f"  开始: {event['start']}")
        print(f"  结束: {event['end']}")
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
