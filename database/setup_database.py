#!/usr/bin/env python3
"""
数据库设置脚本

用于初始化PostgreSQL数据库和Redis缓存系统。
"""

import os
import sys
import subprocess
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from kitchen_safety_system.utils.logger import get_logger

logger = get_logger(__name__)


class DatabaseSetup:
    """数据库设置类"""
    
    def __init__(self):
        """初始化数据库设置"""
        self.pg_config = {
            'host': os.getenv('DATABASE_HOST', 'localhost'),
            'port': int(os.getenv('DATABASE_PORT', 5432)),
            'user': os.getenv('DATABASE_USER', 'kitchen_user'),
            'password': os.getenv('DATABASE_PASSWORD', 'kitchen_pass')
        }
        
        self.db_name = os.getenv('DATABASE_NAME', 'kitchen_safety')
        
        self.redis_config = {
            'host': os.getenv('REDIS_HOST', 'localhost'),
            'port': int(os.getenv('REDIS_PORT', 6379)),
            'db': int(os.getenv('REDIS_DB', 0))
        }
        
        if os.getenv('REDIS_PASSWORD'):
            self.redis_config['password'] = os.getenv('REDIS_PASSWORD')
    
    def wait_for_postgres(self, max_retries: int = 30, retry_interval: int = 2) -> bool:
        """
        等待PostgreSQL服务启动
        
        Args:
            max_retries: 最大重试次数
            retry_interval: 重试间隔（秒）
            
        Returns:
            是否连接成功
        """
        if not PSYCOPG2_AVAILABLE:
            logger.error("psycopg2未安装，无法连接PostgreSQL")
            return False
        
        for attempt in range(max_retries):
            try:
                # 尝试连接到默认的postgres数据库
                conn = psycopg2.connect(
                    host=self.pg_config['host'],
                    port=self.pg_config['port'],
                    user=self.pg_config['user'],
                    password=self.pg_config['password'],
                    database='postgres'
                )
                conn.close()
                logger.info("PostgreSQL连接成功")
                return True
            except Exception as e:
                logger.warning(f"PostgreSQL连接失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
        
        logger.error("PostgreSQL连接超时")
        return False
    
    def wait_for_redis(self, max_retries: int = 30, retry_interval: int = 2) -> bool:
        """
        等待Redis服务启动
        
        Args:
            max_retries: 最大重试次数
            retry_interval: 重试间隔（秒）
            
        Returns:
            是否连接成功
        """
        if not REDIS_AVAILABLE:
            logger.error("redis未安装，无法连接Redis")
            return False
        
        for attempt in range(max_retries):
            try:
                r = redis.Redis(**self.redis_config)
                r.ping()
                logger.info("Redis连接成功")
                return True
            except Exception as e:
                logger.warning(f"Redis连接失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_interval)
        
        logger.error("Redis连接超时")
        return False
    
    def create_database(self) -> bool:
        """
        创建数据库
        
        Returns:
            是否创建成功
        """
        if not PSYCOPG2_AVAILABLE:
            logger.error("psycopg2未安装，无法创建数据库")
            return False
        
        try:
            # 连接到默认的postgres数据库
            conn = psycopg2.connect(
                host=self.pg_config['host'],
                port=self.pg_config['port'],
                user=self.pg_config['user'],
                password=self.pg_config['password'],
                database='postgres'
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # 检查数据库是否存在
            cursor.execute(
                "SELECT 1 FROM pg_database WHERE datname = %s",
                (self.db_name,)
            )
            
            if cursor.fetchone():
                logger.info(f"数据库 {self.db_name} 已存在")
            else:
                # 创建数据库
                cursor.execute(f'CREATE DATABASE "{self.db_name}"')
                logger.info(f"数据库 {self.db_name} 创建成功")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            return False
    
    def initialize_schema(self) -> bool:
        """
        初始化数据库模式
        
        Returns:
            是否初始化成功
        """
        if not PSYCOPG2_AVAILABLE:
            logger.error("psycopg2未安装，无法初始化数据库模式")
            return False
        
        try:
            # 连接到目标数据库
            conn = psycopg2.connect(
                host=self.pg_config['host'],
                port=self.pg_config['port'],
                user=self.pg_config['user'],
                password=self.pg_config['password'],
                database=self.db_name
            )
            
            cursor = conn.cursor()
            
            # 读取并执行初始化SQL脚本
            init_sql_path = Path(__file__).parent / 'init.sql'
            if init_sql_path.exists():
                with open(init_sql_path, 'r', encoding='utf-8') as f:
                    sql_content = f.read()
                
                # 移除连接数据库的命令，因为我们已经连接了
                sql_content = sql_content.replace('\\c kitchen_safety;', '')
                
                cursor.execute(sql_content)
                conn.commit()
                logger.info("数据库模式初始化成功")
            else:
                logger.error(f"初始化SQL文件不存在: {init_sql_path}")
                return False
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"初始化数据库模式失败: {e}")
            return False
    
    def test_redis_connection(self) -> bool:
        """
        测试Redis连接
        
        Returns:
            是否连接成功
        """
        if not REDIS_AVAILABLE:
            logger.error("redis未安装，无法测试Redis连接")
            return False
        
        try:
            r = redis.Redis(**self.redis_config)
            
            # 测试基本操作
            test_key = 'kitchen_safety:test'
            test_value = 'connection_test'
            
            r.set(test_key, test_value, ex=10)  # 10秒过期
            retrieved_value = r.get(test_key)
            
            if retrieved_value and retrieved_value.decode('utf-8') == test_value:
                logger.info("Redis连接测试成功")
                r.delete(test_key)  # 清理测试数据
                return True
            else:
                logger.error("Redis连接测试失败：数据不匹配")
                return False
                
        except Exception as e:
            logger.error(f"Redis连接测试失败: {e}")
            return False
    
    def setup_all(self) -> bool:
        """
        设置所有数据库和缓存系统
        
        Returns:
            是否设置成功
        """
        logger.info("开始设置数据库和缓存系统...")
        
        # 等待PostgreSQL启动
        if not self.wait_for_postgres():
            return False
        
        # 创建数据库
        if not self.create_database():
            return False
        
        # 初始化数据库模式
        if not self.initialize_schema():
            return False
        
        # 等待Redis启动
        if not self.wait_for_redis():
            return False
        
        # 测试Redis连接
        if not self.test_redis_connection():
            return False
        
        logger.info("数据库和缓存系统设置完成")
        return True


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='厨房安全检测系统数据库设置')
    parser.add_argument('--wait-only', action='store_true', help='仅等待服务启动')
    parser.add_argument('--create-db-only', action='store_true', help='仅创建数据库')
    parser.add_argument('--init-schema-only', action='store_true', help='仅初始化数据库模式')
    parser.add_argument('--test-redis-only', action='store_true', help='仅测试Redis连接')
    
    args = parser.parse_args()
    
    setup = DatabaseSetup()
    
    try:
        if args.wait_only:
            success = setup.wait_for_postgres() and setup.wait_for_redis()
        elif args.create_db_only:
            success = setup.create_database()
        elif args.init_schema_only:
            success = setup.initialize_schema()
        elif args.test_redis_only:
            success = setup.test_redis_connection()
        else:
            success = setup.setup_all()
        
        if success:
            logger.info("数据库设置成功")
            sys.exit(0)
        else:
            logger.error("数据库设置失败")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        sys.exit(1)
    except Exception as e:
        logger.error(f"设置过程中发生错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()