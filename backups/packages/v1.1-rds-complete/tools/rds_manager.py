#!/usr/bin/env python3
"""
RDS数据库管理工具
支持MySQL/PostgreSQL，统一接口
"""

import json
import os
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

CONFIG_FILE = Path("/root/.openclaw/workspace/config/rds_config.json")

class RDSManager:
    """RDS管理器"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self, host, port, database, user, password, db_type='mysql'):
        """保存配置"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        config = {
            'host': host,
            'port': port,
            'database': database,
            'user': user,
            'password': password,
            'type': db_type,
            'created_at': datetime.now().isoformat()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)
        return config
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        import pymysql
        conn = pymysql.connect(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['database'],
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        try:
            yield conn
        finally:
            conn.close()
    
    def init_database(self):
        """初始化所有表结构"""
        tables = [
            self._create_restaurants_table(),
            self._create_system_metrics_table(),
            self._create_emails_table(),
            self._create_memories_table(),
            self._create_webhook_logs_table(),
            self._create_tasks_table(),
        ]
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                for sql in tables:
                    try:
                        cursor.execute(sql)
                        conn.commit()
                    except Exception as e:
                        print(f"⚠️ 表可能已存在: {e}")
        
        return "✅ 数据库初始化完成"
    
    def _create_restaurants_table(self):
        return """
        CREATE TABLE IF NOT EXISTS restaurants (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(256) NOT NULL,
            address VARCHAR(512),
            city VARCHAR(50),
            district VARCHAR(50),
            lat DECIMAL(10, 8),
            lng DECIMAL(11, 8),
            rating DECIMAL(3, 2),
            category VARCHAR(100),
            tags JSON,
            phone VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_city (city),
            INDEX idx_rating (rating),
            INDEX idx_location (lat, lng)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    
    def _create_system_metrics_table(self):
        return """
        CREATE TABLE IF NOT EXISTS system_metrics (
            id INT AUTO_INCREMENT PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hostname VARCHAR(100),
            cpu_percent FLOAT,
            cpu_count INT,
            memory_total_gb FLOAT,
            memory_used_gb FLOAT,
            memory_percent FLOAT,
            disk_total_gb FLOAT,
            disk_used_gb FLOAT,
            disk_percent FLOAT,
            network_in_mb BIGINT,
            network_out_mb BIGINT,
            openclaw_status VARCHAR(20),
            INDEX idx_timestamp (timestamp),
            INDEX idx_hostname (hostname)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    
    def _create_emails_table(self):
        return """
        CREATE TABLE IF NOT EXISTS emails (
            id INT AUTO_INCREMENT PRIMARY KEY,
            message_id VARCHAR(128) UNIQUE,
            subject VARCHAR(512),
            sender VARCHAR(256),
            sender_name VARCHAR(256),
            received_at TIMESTAMP,
            category ENUM('important', 'promo', 'normal') DEFAULT 'normal',
            is_read BOOLEAN DEFAULT FALSE,
            is_archived BOOLEAN DEFAULT FALSE,
            body_summary TEXT,
            full_content MEDIUMTEXT,
            labels JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_received_at (received_at),
            INDEX idx_category (category),
            INDEX idx_sender (sender),
            FULLTEXT INDEX idx_subject (subject)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    
    def _create_memories_table(self):
        return """
        CREATE TABLE IF NOT EXISTS memories (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_key VARCHAR(64),
            memory_type ENUM('short_term', 'long_term', 'user_pref') DEFAULT 'short_term',
            category VARCHAR(50),
            content TEXT,
            keywords JSON,
            importance_score FLOAT DEFAULT 0.5,
            source VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP,
            access_count INT DEFAULT 0,
            INDEX idx_session (session_key),
            INDEX idx_type (memory_type),
            INDEX idx_category (category),
            FULLTEXT INDEX idx_content (content)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    
    def _create_webhook_logs_table(self):
        return """
        CREATE TABLE IF NOT EXISTS webhook_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            webhook_id VARCHAR(64),
            webhook_name VARCHAR(256),
            action VARCHAR(100),
            payload JSON,
            source_ip VARCHAR(50),
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status ENUM('success', 'failed', 'pending') DEFAULT 'pending',
            execution_time_ms INT,
            error_message TEXT,
            response_data JSON,
            INDEX idx_webhook_id (webhook_id),
            INDEX idx_executed_at (executed_at),
            INDEX idx_status (status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
    
    def _create_tasks_table(self):
        return """
        CREATE TABLE IF NOT EXISTS tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task_key VARCHAR(64) UNIQUE,
            title VARCHAR(256),
            description TEXT,
            status ENUM('pending', 'in_progress', 'completed', 'cancelled') DEFAULT 'pending',
            priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
            due_date TIMESTAMP,
            assigned_to VARCHAR(100),
            tags JSON,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            INDEX idx_status (status),
            INDEX idx_due_date (due_date),
            INDEX idx_priority (priority)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("🗄️ RDS数据库管理工具")
        print("\n用法:")
        print("  python3 rds_manager.py setup <host> <port> <database> <user> <password>")
        print("  python3 rds_manager.py init          # 初始化数据库")
        print("  python3 rds_manager.py test          # 测试连接")
        print("  python3 rds_manager.py status        # 查看状态")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'setup':
        if len(sys.argv) < 7:
            print("用法: setup <host> <port> <database> <user> <password>")
            sys.exit(1)
        manager = RDSManager()
        config = manager.save_config(
            host=sys.argv[2],
            port=int(sys.argv[3]),
            database=sys.argv[4],
            user=sys.argv[5],
            password=sys.argv[6]
        )
        print("✅ RDS配置已保存")
        print(f"   主机: {config['host']}:{config['port']}")
        print(f"   数据库: {config['database']}")
        print(f"   用户: {config['user']}")
    
    elif cmd == 'init':
        manager = RDSManager()
        result = manager.init_database()
        print(result)
    
    elif cmd == 'test':
        manager = RDSManager()
        try:
            with manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT VERSION()")
                    result = cursor.fetchone()
                    print(f"✅ 连接成功!")
                    print(f"   MySQL版本: {result['VERSION()']}")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
    
    elif cmd == 'status':
        manager = RDSManager()
        if not manager.config:
            print("❌ 未配置RDS")
            sys.exit(1)
        
        print("📊 RDS配置状态")
        print("=" * 40)
        print(f"主机: {manager.config.get('host')}")
        print(f"端口: {manager.config.get('port')}")
        print(f"数据库: {manager.config.get('database')}")
        print(f"用户: {manager.config.get('user')}")
        print(f"配置时间: {manager.config.get('created_at', 'N/A')}")
        
        # 测试连接
        try:
            with manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SHOW TABLES")
                    tables = cursor.fetchall()
                    print(f"\n✅ 连接正常")
                    print(f"表数量: {len(tables)}")
                    if tables:
                        print("\n已创建的表:")
                        for t in tables:
                            print(f"  - {list(t.values())[0]}")
        except Exception as e:
            print(f"\n❌ 连接异常: {e}")
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
