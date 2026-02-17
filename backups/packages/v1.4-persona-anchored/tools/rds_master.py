#!/usr/bin/env python3
"""
RDS综合工具 - 统一入口
整合所有RDS功能
"""

import sys
from pathlib import Path

# 添加工具目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from rds_manager import RDSManager
from restaurant_rds import RestaurantRDS
from metrics_rds import SystemMetricsRDS
from email_rds import EmailArchiveRDS
from memory_rds import MemoryRDS
from webhook_rds import WebhookLogRDS

class RDSMaster:
    """RDS主控"""
    
    def __init__(self):
        self.restaurants = RestaurantRDS()
        self.metrics = SystemMetricsRDS()
        self.emails = EmailArchiveRDS()
        self.memories = MemoryRDS()
        self.webhooks = WebhookLogRDS()
    
    def full_setup(self, host, port, database, user, password):
        """完整设置流程"""
        print("🗄️ RDS完整设置")
        print("=" * 50)
        
        # 1. 保存配置
        print("\n1. 保存配置...")
        rds = RDSManager()
        config = rds.save_config(host, port, database, user, password)
        print(f"   ✅ 配置已保存: {config['host']}:{config['port']}")
        
        # 2. 测试连接
        print("\n2. 测试连接...")
        try:
            with rds.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    version = cursor.fetchone()['VERSION()']
                    print(f"   ✅ 连接成功: MySQL {version}")
        except Exception as e:
            print(f"   ❌ 连接失败: {e}")
            return False
        
        # 3. 初始化表结构
        print("\n3. 初始化数据库表...")
        result = rds.init_database()
        print(f"   {result}")
        
        print("\n" + "=" * 50)
        print("✅ RDS设置完成!")
        print("\n已创建的表:")
        print("  - restaurants      (餐厅数据)")
        print("  - system_metrics   (系统监控)")
        print("  - emails           (邮件归档)")
        print("  - memories         (记忆存储)")
        print("  - webhook_logs     (Webhook日志)")
        print("  - tasks            (任务管理)")
        
        return True
    
    def import_all_data(self):
        """导入所有本地数据到RDS"""
        print("📥 导入所有数据到RDS")
        print("=" * 50)
        
        workspace = Path("/root/.openclaw/workspace")
        
        # 1. 导入餐厅数据
        print("\n1. 导入餐厅数据...")
        csv_file = workspace / "restaurants_full_with_coords.csv"
        if csv_file.exists():
            result = self.restaurants.import_from_csv(csv_file)
            print(f"   {result}")
        else:
            print("   ⚠️ 未找到餐厅CSV文件")
        
        print("\n" + "=" * 50)
        print("✅ 数据导入完成!")
        print("\n提示:")
        print("  - 监控数据会自动存入")
        print("  - 邮件通过 email_rds.py 归档")
        print("  - 记忆通过 memory_rds.py 存储")
    
    def show_all_stats(self):
        """显示所有统计"""
        print("📊 RDS数据统计")
        print("=" * 50)
        
        # 餐厅统计
        print("\n🍽️ 餐厅数据:")
        try:
            stats = self.restaurants.get_stats()
            print(f"   总数量: {stats['total']}")
            print(f"   平均评分: {stats['avg_rating']}")
        except Exception as e:
            print(f"   ⚠️ {e}")
        
        # 监控统计
        print("\n📊 监控数据:")
        try:
            recent = self.metrics.get_recent_metrics(hours=24)
            print(f"   24小时数据点: {len(recent)}")
        except Exception as e:
            print(f"   ⚠️ {e}")
        
        # 邮件统计
        print("\n📧 邮件归档:")
        try:
            stats = self.emails.get_stats()
            print(f"   总数: {stats['total']}, 未读: {stats['unread']}")
        except Exception as e:
            print(f"   ⚠️ {e}")
        
        # 记忆统计
        print("\n🧠 记忆存储:")
        try:
            stats = self.memories.get_stats()
            print(f"   总数: {stats['total']}, 今日: {stats['today']}")
        except Exception as e:
            print(f"   ⚠️ {e}")
        
        # Webhook统计
        print("\n🔗 Webhook日志:")
        try:
            stats = self.webhooks.get_stats()
            print(f"   24小时调用: {stats['total']}")
        except Exception as e:
            print(f"   ⚠️ {e}")


def show_help():
    """显示帮助"""
    print("""
🗄️ RDS综合工具 - 统一入口

用法:
  python3 rds_master.py setup <host> <port> <database> <user> <password>
                              # 完整设置流程
  
  python3 rds_master.py import-data
                              # 导入所有本地数据
  
  python3 rds_master.py stats # 查看所有统计

专项工具:
  python3 rds_manager.py      # 数据库管理
  python3 restaurant_rds.py   # 餐厅数据
  python3 metrics_rds.py      # 系统监控
  python3 email_rds.py        # 邮件归档
  python3 memory_rds.py       # 记忆存储
  python3 webhook_rds.py      # Webhook日志

示例:
  # 完整设置
  python3 rds_master.py setup rm-xxx.mysql.rds.aliyuncs.com 3306 mydb admin password
  
  # 导入数据
  python3 rds_master.py import-data
  
  # 查看统计
  python3 rds_master.py stats
""")


def main():
    if len(sys.argv) < 2:
        show_help()
        sys.exit(1)
    
    cmd = sys.argv[1]
    master = RDSMaster()
    
    if cmd == 'setup':
        if len(sys.argv) < 7:
            print("用法: setup <host> <port> <database> <user> <password>")
            sys.exit(1)
        master.full_setup(
            host=sys.argv[2],
            port=int(sys.argv[3]),
            database=sys.argv[4],
            user=sys.argv[5],
            password=sys.argv[6]
        )
    
    elif cmd == 'import-data':
        master.import_all_data()
    
    elif cmd == 'stats':
        master.show_all_stats()
    
    else:
        show_help()

if __name__ == '__main__':
    main()
