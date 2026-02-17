#!/usr/bin/env python3
"""
系统监控工具 - 可配置报警阈值
监控服务器状态、OpenClaw服务健康、自动报警
"""

import psutil
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("/root/.openclaw/workspace/output/monitoring")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_FILE = Path("/root/.openclaw/workspace/config/monitor_config.json")

# 默认配置
DEFAULT_CONFIG = {
    'cpu_threshold': 80,      # CPU报警阈值 (%)
    'memory_threshold': 85,   # 内存报警阈值 (%)
    'disk_threshold': 90,     # 磁盘报警阈值 (%)
    'check_openclaw': True,   # 是否检查OpenClaw
    'alert_cooldown': 30,     # 报警冷却时间 (分钟)
    'notify_channels': ['feishu'],  # 通知渠道
    'last_alert': {}          # 上次报警时间
}

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                saved = json.load(f)
                # 合并默认配置
                config = DEFAULT_CONFIG.copy()
                config.update(saved)
                return config
        return DEFAULT_CONFIG.copy()
    
    def save_config(self):
        """保存配置"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def set_threshold(self, metric, value):
        """设置阈值"""
        key = f'{metric}_threshold'
        if key in self.config:
            self.config[key] = int(value)
            self.save_config()
            return f"✅ {metric}报警阈值已设置为 {value}%"
        return f"❌ 未知指标: {metric}"
    
    def get_threshold(self, metric):
        """获取阈值"""
        return self.config.get(f'{metric}_threshold', DEFAULT_CONFIG[f'{metric}_threshold'])
    
    @staticmethod
    def get_system_stats():
        """获取系统统计"""
        stats = {
            'timestamp': datetime.now().isoformat(),
            'cpu': {
                'percent': psutil.cpu_percent(interval=1),
                'count': psutil.cpu_count(),
                'freq': psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None
            },
            'memory': {
                'total': psutil.virtual_memory().total // (1024**3),  # GB
                'available': psutil.virtual_memory().available // (1024**3),
                'percent': psutil.virtual_memory().percent,
                'used': psutil.virtual_memory().used // (1024**3)
            },
            'disk': {
                'total': psutil.disk_usage('/').total // (1024**3),
                'used': psutil.disk_usage('/').used // (1024**3),
                'free': psutil.disk_usage('/').free // (1024**3),
                'percent': psutil.disk_usage('/').percent
            },
            'network': {
                'bytes_sent': psutil.net_io_counters().bytes_sent // (1024**2),  # MB
                'bytes_recv': psutil.net_io_counters().bytes_recv // (1024**2)
            },
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        return stats
    
    @staticmethod
    def check_openclaw_status():
        """检查OpenClaw服务状态"""
        try:
            result = subprocess.run(['openclaw', 'status'], 
                                  capture_output=True, text=True, timeout=10)
            return {
                'running': 'running' in result.stdout.lower(),
                'output': result.stdout[:500]
            }
        except Exception as e:
            return {'running': False, 'error': str(e)}
    
    def check_alerts(self, stats):
        """检查是否需要报警（带冷却）"""
        alerts = []
        now = datetime.now()
        
        # CPU报警
        cpu_threshold = self.get_threshold('cpu')
        if stats['cpu']['percent'] > cpu_threshold:
            alert_key = 'cpu'
            if self._can_alert(alert_key, now):
                alerts.append(f"🔴 CPU使用率过高: {stats['cpu']['percent']}% (阈值: {cpu_threshold}%)")
                self._record_alert(alert_key, now)
        
        # 内存报警
        mem_threshold = self.get_threshold('memory')
        if stats['memory']['percent'] > mem_threshold:
            alert_key = 'memory'
            if self._can_alert(alert_key, now):
                alerts.append(f"🔴 内存使用率过高: {stats['memory']['percent']}% (阈值: {mem_threshold}%)")
                self._record_alert(alert_key, now)
        
        # 磁盘报警
        disk_threshold = self.get_threshold('disk')
        if stats['disk']['percent'] > disk_threshold:
            alert_key = 'disk'
            if self._can_alert(alert_key, now):
                alerts.append(f"🔴 磁盘空间不足: {stats['disk']['percent']}% (阈值: {disk_threshold}%)")
                self._record_alert(alert_key, now)
        
        return alerts
    
    def _can_alert(self, alert_key, now):
        """检查是否可以报警（冷却时间）"""
        last_alert = self.config.get('last_alert', {})
        if alert_key in last_alert:
            last_time = datetime.fromisoformat(last_alert[alert_key])
            cooldown = timedelta(minutes=self.config['alert_cooldown'])
            if now - last_time < cooldown:
                return False
        return True
    
    def _record_alert(self, alert_key, now):
        """记录报警时间"""
        if 'last_alert' not in self.config:
            self.config['last_alert'] = {}
        self.config['last_alert'][alert_key] = now.isoformat()
        self.save_config()
    
    def generate_report(self):
        """生成系统报告"""
        stats = self.get_system_stats()
        openclaw = self.check_openclaw_status() if self.config['check_openclaw'] else {'running': True}
        alerts = self.check_alerts(stats)
        
        report = {
            'timestamp': stats['timestamp'],
            'system': stats,
            'openclaw': openclaw,
            'alerts': alerts,
            'thresholds': {
                'cpu': self.get_threshold('cpu'),
                'memory': self.get_threshold('memory'),
                'disk': self.get_threshold('disk')
            },
            'status': 'warning' if alerts else 'ok'
        }
        
        # 保存报告
        report_file = OUTPUT_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    @staticmethod
    def format_report_for_feishu(report):
        """格式化为飞书消息"""
        s = report['system']
        thresholds = report.get('thresholds', DEFAULT_CONFIG)
        
        msg = f"📊 系统监控报告 [{datetime.now().strftime('%H:%M')}]\n"
        msg += "=" * 40 + "\n\n"
        
        # 系统状态
        cpu_threshold = thresholds.get('cpu', 80)
        mem_threshold = thresholds.get('memory', 85)
        disk_threshold = thresholds.get('disk', 90)
        
        cpu_emoji = "🔴" if s['cpu']['percent'] > cpu_threshold else "🟡" if s['cpu']['percent'] > cpu_threshold * 0.7 else "🟢"
        mem_emoji = "🔴" if s['memory']['percent'] > mem_threshold else "🟡" if s['memory']['percent'] > mem_threshold * 0.7 else "🟢"
        disk_emoji = "🔴" if s['disk']['percent'] > disk_threshold else "🟡" if s['disk']['percent'] > disk_threshold * 0.7 else "🟢"
        
        msg += f"{cpu_emoji} CPU: {s['cpu']['percent']}% (阈值: {cpu_threshold}%)\n"
        msg += f"{mem_emoji} 内存: {s['memory']['used']}/{s['memory']['total']} GB ({s['memory']['percent']}%)\n"
        msg += f"{disk_emoji} 磁盘: {s['disk']['used']}/{s['disk']['total']} GB ({s['disk']['percent']}%)\n"
        msg += f"📡 网络: ↓{s['network']['bytes_recv']}MB ↑{s['network']['bytes_sent']}MB\n\n"
        
        # OpenClaw状态
        oc = report['openclaw']
        oc_emoji = "🟢" if oc.get('running') else "🔴"
        msg += f"{oc_emoji} OpenClaw: {'运行中' if oc.get('running') else '异常'}\n\n"
        
        # 报警
        if report['alerts']:
            msg += "⚠️ 报警:\n"
            for alert in report['alerts']:
                msg += f"  {alert}\n"
        else:
            msg += "✅ 系统状态正常\n"
        
        return msg
    
    def show_config(self):
        """显示当前配置"""
        msg = "📋 系统监控配置\n"
        msg += "=" * 40 + "\n\n"
        msg += f"CPU报警阈值: {self.get_threshold('cpu')}%\n"
        msg += f"内存报警阈值: {self.get_threshold('memory')}%\n"
        msg += f"磁盘报警阈值: {self.get_threshold('disk')}%\n"
        msg += f"报警冷却时间: {self.config['alert_cooldown']} 分钟\n"
        msg += f"检查OpenClaw: {'是' if self.config['check_openclaw'] else '否'}\n"
        msg += f"通知渠道: {', '.join(self.config['notify_channels'])}\n"
        return msg


def main():
    import sys
    
    monitor = SystemMonitor()
    
    if len(sys.argv) < 2:
        # 生成并显示报告
        report = monitor.generate_report()
        print(monitor.format_report_for_feishu(report))
        
        # 如果有报警，输出报警信息
        if report['alerts']:
            print("\n" + "=" * 40)
            print("ALERTS_FOUND")
            for alert in report['alerts']:
                print(alert)
        
        sys.exit(0)
    
    cmd = sys.argv[1]
    
    if cmd == 'stats':
        stats = SystemMonitor.get_system_stats()
        print(json.dumps(stats, indent=2))
    
    elif cmd == 'check':
        report = monitor.generate_report()
        print(monitor.format_report_for_feishu(report))
    
    elif cmd == 'alerts':
        report = monitor.generate_report()
        if report['alerts']:
            print("找到以下报警:")
            for alert in report['alerts']:
                print(f"  {alert}")
        else:
            print("✅ 无报警")
    
    elif cmd == 'config':
        print(monitor.show_config())
    
    elif cmd == 'set':
        if len(sys.argv) < 4:
            print("用法: set <metric> <value>")
            print("metric: cpu, memory, disk")
            sys.exit(1)
        metric = sys.argv[2]
        value = sys.argv[3]
        print(monitor.set_threshold(metric, value))
    
    elif cmd == 'cooldown':
        if len(sys.argv) < 3:
            print(f"当前冷却时间: {monitor.config['alert_cooldown']} 分钟")
            sys.exit(0)
        minutes = int(sys.argv[2])
        monitor.config['alert_cooldown'] = minutes
        monitor.save_config()
        print(f"✅ 报警冷却时间已设置为 {minutes} 分钟")
    
    else:
        print(f"未知命令: {cmd}")
        print("\n用法:")
        print("  system_monitor.py          # 生成报告")
        print("  system_monitor.py stats    # 查看统计")
        print("  system_monitor.py config   # 查看配置")
        print("  system_monitor.py set <metric> <value>  # 设置阈值")
        print("  system_monitor.py cooldown [分钟]        # 设置冷却时间")

if __name__ == '__main__':
    main()
