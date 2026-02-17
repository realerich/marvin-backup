#!/usr/bin/env python3
"""
RDS数据库管理工具 (PostgreSQL)
支持阿里云RDS PostgreSQL
"""

import json
import os
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

CONFIG_FILE = Path("/root/.openclaw/workspace/config/rds_config.json")

# 默认配置
DEFAULT_CONFIG = {
    'host': 'pgm-j6c0rrysy447d8tc.pg.rds.aliyuncs.com',
    'port': 5432,
    'database': 'marvin_db',
    'user': 'marvin',
    'password': 'Crimson@13',
    'type': 'postgresql'
}

class RDSManager:
    """RDS管理器 (PostgreSQL)"""
    
    def __init__(self):
        self.config = self._load_config()
    
    def _load_config(self):
        """加载配置"""
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return DEFAULT_CONFIG.copy()
    
    def save_config(self, host=None, port=None, database=None, user=None, password=None):
        """保存配置"""
        CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        config = {
            'host': host or DEFAULT_CONFIG['host'],
            'port': port or DEFAULT_CONFIG['port'],
            'database': database or DEFAULT_CONFIG['database'],
            'user': user or DEFAULT_CONFIG['user'],
            'password': password or DEFAULT_CONFIG['password'],
            'type': 'postgresql',
            'created_at': datetime.now().isoformat()
        }
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)
        self.config = config
        return config
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接"""
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(
            host=self.config['host'],
            port=self.config['port'],
            user=self.config['user'],
            password=self.config['password'],
            database=self.config['database'],
            sslmode='disable'
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
            self._create_feishu_messages_table(),
        ]
        
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                for sql in tables:
                    try:
                        cursor.execute(sql)
                        conn.commit()
                    except Exception as e:
                        print(f"⚠️ 表可能已存在: {e}")
                        conn.rollback()
        
        return "✅ 数据库初始化完成"
    
    def _create_restaurants_table(self):
        return """
        CREATE TABLE IF NOT EXISTS restaurants (
            id SERIAL PRIMARY KEY,
            name VARCHAR(256) NOT NULL,
            address VARCHAR(512),
            city VARCHAR(50),
            district VARCHAR(50),
            lat NUMERIC(10, 8),
            lng NUMERIC(11, 8),
            rating NUMERIC(3, 2),
            category VARCHAR(100),
            tags JSONB,
            phone VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_restaurants_city ON restaurants(city);
        CREATE INDEX IF NOT EXISTS idx_restaurants_rating ON restaurants(rating);
        """
    
    def _create_system_metrics_table(self):
        return """
        CREATE TABLE IF NOT EXISTS system_metrics (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            hostname VARCHAR(100),
            cpu_percent NUMERIC(5, 2),
            cpu_count INTEGER,
            memory_total_gb NUMERIC(10, 2),
            memory_used_gb NUMERIC(10, 2),
            memory_percent NUMERIC(5, 2),
            disk_total_gb NUMERIC(10, 2),
            disk_used_gb NUMERIC(10, 2),
            disk_percent NUMERIC(5, 2),
            network_in_mb BIGINT,
            network_out_mb BIGINT,
            openclaw_status VARCHAR(20)
        );
        CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON system_metrics(timestamp);
        CREATE INDEX IF NOT EXISTS idx_metrics_hostname ON system_metrics(hostname);
        """
    
    def _create_emails_table(self):
        return """
        CREATE TABLE IF NOT EXISTS emails (
            id SERIAL PRIMARY KEY,
            message_id VARCHAR(128) UNIQUE,
            subject VARCHAR(512),
            sender VARCHAR(256),
            sender_name VARCHAR(256),
            received_at TIMESTAMP,
            category VARCHAR(20) DEFAULT 'normal',
            is_read BOOLEAN DEFAULT FALSE,
            is_archived BOOLEAN DEFAULT FALSE,
            body_summary TEXT,
            full_content TEXT,
            labels JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_emails_received ON emails(received_at);
        CREATE INDEX IF NOT EXISTS idx_emails_category ON emails(category);
        CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender);
        """
    
    def _create_memories_table(self):
        return """
        CREATE TABLE IF NOT EXISTS memories (
            id SERIAL PRIMARY KEY,
            session_key VARCHAR(64),
            memory_type VARCHAR(20) DEFAULT 'short_term',
            category VARCHAR(50),
            content TEXT,
            keywords JSONB,
            importance_score NUMERIC(3, 2) DEFAULT 0.5,
            source VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_accessed TIMESTAMP,
            access_count INTEGER DEFAULT 0
        );
        CREATE INDEX IF NOT EXISTS idx_memories_session ON memories(session_key);
        CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(memory_type);
        CREATE INDEX IF NOT EXISTS idx_memories_category ON memories(category);
        """
    
    def _create_webhook_logs_table(self):
        return """
        CREATE TABLE IF NOT EXISTS webhook_logs (
            id SERIAL PRIMARY KEY,
            webhook_id VARCHAR(64),
            webhook_name VARCHAR(256),
            action VARCHAR(100),
            payload JSONB,
            source_ip VARCHAR(50),
            executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(20) DEFAULT 'pending',
            execution_time_ms INTEGER,
            error_message TEXT,
            response_data JSONB
        );
        CREATE INDEX IF NOT EXISTS idx_webhook_logs_id ON webhook_logs(webhook_id);
        CREATE INDEX IF NOT EXISTS idx_webhook_logs_time ON webhook_logs(executed_at);
        CREATE INDEX IF NOT EXISTS idx_webhook_logs_status ON webhook_logs(status);
        """
    
    def _create_tasks_table(self):
        return """
        CREATE TABLE IF NOT EXISTS tasks (
            id SERIAL PRIMARY KEY,
            task_key VARCHAR(64) UNIQUE,
            title VARCHAR(256),
            description TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            priority VARCHAR(20) DEFAULT 'medium',
            due_date TIMESTAMP,
            assigned_to VARCHAR(100),
            tags JSONB,
            metadata JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);
        CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
        """
    
    def _create_feishu_messages_table(self):
        return """
        CREATE TABLE IF NOT EXISTS feishu_messages (
            id SERIAL PRIMARY KEY,
            message_id VARCHAR(100) UNIQUE,
            sender_id VARCHAR(100),
            sender_name VARCHAR(100),
            chat_type VARCHAR(20),
            chat_id VARCHAR(100),
            content TEXT,
            content_type VARCHAR(20) DEFAULT 'text',
            is_processed BOOLEAN DEFAULT FALSE,
            processed_action VARCHAR(50),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_feishu_sender ON feishu_messages(sender_id);
        CREATE INDEX IF NOT EXISTS idx_feishu_chat ON feishu_messages(chat_id);
        CREATE INDEX IF NOT EXISTS idx_feishu_created ON feishu_messages(created_at);
        CREATE INDEX IF NOT EXISTS idx_feishu_processed ON feishu_messages(is_processed);
        """


def main():
    import sys
    
    manager = RDSManager()
    
    if len(sys.argv) < 2:
        print("🗄️ RDS数据库管理工具 (PostgreSQL)")
        print("\n用法:")
        print("  python3 rds_manager.py setup [host] [port] [database] [user] [password]")
        print("  python3 rds_manager.py init          # 初始化数据库")
        print("  python3 rds_manager.py test          # 测试连接")
        print("  python3 rds_manager.py status        # 查看状态")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'setup':
        host = sys.argv[2] if len(sys.argv) > 2 else None
        port = int(sys.argv[3]) if len(sys.argv) > 3 else None
        database = sys.argv[4] if len(sys.argv) > 4 else None
        user = sys.argv[5] if len(sys.argv) > 5 else None
        password = sys.argv[6] if len(sys.argv) > 6 else None
        
        config = manager.save_config(host, port, database, user, password)
        print("✅ RDS配置已保存")
        print(f"   主机: {config['host']}:{config['port']}")
        print(f"   数据库: {config['database']}")
        print(f"   用户: {config['user']}")
    
    elif cmd == 'init':
        result = manager.init_database()
        print(result)
    
    elif cmd == 'test':
        try:
            with manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT version()")
                    result = cursor.fetchone()
                    print(f"✅ 连接成功!")
                    print(f"   PostgreSQL版本: {result[0]}")
        except Exception as e:
            print(f"❌ 连接失败: {e}")
    
    elif cmd == 'status':
        print("📊 RDS配置状态")
        print("=" * 40)
        print(f"主机: {manager.config.get('host')}")
        print(f"端口: {manager.config.get('port')}")
        print(f"数据库: {manager.config.get('database')}")
        print(f"用户: {manager.config.get('user')}")
        print(f"类型: {manager.config.get('type', 'postgresql')}")
        print(f"配置时间: {manager.config.get('created_at', 'N/A')}")
        
        # 测试连接
        try:
            with manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'")
                    tables = cursor.fetchall()
                    print(f"\n✅ 连接正常")
                    print(f"表数量: {len(tables)}")
                    if tables:
                        print("\n已创建的表:")
                        for t in tables:
                            print(f"  - {t[0]}")
        except Exception as e:
            print(f"\n❌ 连接异常: {e}")
    
    else:
        print(f"未知命令: {cmd}")

if __name__ == '__main__':
    main()
