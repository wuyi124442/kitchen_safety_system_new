#!/usr/bin/env python3
"""
厨房安全检测系统健康检查脚本
用于Docker健康检查和系统监控
"""

import sys
import time
import requests
import psycopg2
import redis
import os
from typing import Dict, Any, List


class HealthChecker:
    """系统健康检查器"""
    
    def __init__(self):
        self.checks = []
        self.results = {}
        
    def add_check(self, name: str, check_func, critical: bool = True):
        """添加检查项"""
        self.checks.append({
            'name': name,
            'func': check_func,
            'critical': critical
        })
    
    def run_checks(self) -> Dict[str, Any]:
        """运行所有检查"""
        results = {
            'healthy': True,
            'checks': {},
            'summary': {
                'total': len(self.checks),
                'passed': 0,
                'failed': 0,
                'warnings': 0
            }
        }
        
        for check in self.checks:
            try:
                result = check['func']()
                status = 'passed' if result['success'] else 'failed'
                
                results['checks'][check['name']] = {
                    'status': status,
                    'message': result.get('message', ''),
                    'details': result.get('details', {}),
                    'critical': check['critical']
                }
                
                if result['success']:
                    results['summary']['passed'] += 1
                else:
                    if check['critical']:
                        results['summary']['failed'] += 1
                        results['healthy'] = False
                    else:
                        results['summary']['warnings'] += 1
                        
            except Exception as e:
                results['checks'][check['name']] = {
                    'status': 'error',
                    'message': f'检查执行失败: {str(e)}',
                    'critical': check['critical']
                }
                
                if check['critical']:
                    results['summary']['failed'] += 1
                    results['healthy'] = False
                else:
                    results['summary']['warnings'] += 1
        
        return results


def check_web_service():
    """检查Web服务"""
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            return {
                'success': True,
                'message': 'Web服务正常',
                'details': {
                    'status_code': response.status_code,
                    'response_time': response.elapsed.total_seconds()
                }
            }
        else:
            return {
                'success': False,
                'message': f'Web服务返回错误状态码: {response.status_code}'
            }
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'message': f'Web服务连接失败: {str(e)}'
        }


def check_database():
    """检查数据库连接"""
    try:
        conn = psycopg2.connect(
            host=os.environ.get('DATABASE_HOST', 'localhost'),
            port=os.environ.get('DATABASE_PORT', '5432'),
            database=os.environ.get('DATABASE_NAME', 'kitchen_safety'),
            user=os.environ.get('DATABASE_USER', 'kitchen_user'),
            password=os.environ.get('DATABASE_PASSWORD', 'kitchen_pass'),
            connect_timeout=5
        )
        
        cursor = conn.cursor()
        cursor.execute('SELECT 1')
        cursor.fetchone()
        cursor.close()
        conn.close()
        
        return {
            'success': True,
            'message': '数据库连接正常'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'数据库连接失败: {str(e)}'
        }


def check_redis():
    """检查Redis连接"""
    try:
        r = redis.Redis(
            host=os.environ.get('REDIS_HOST', 'localhost'),
            port=int(os.environ.get('REDIS_PORT', '6379')),
            socket_timeout=5,
            decode_responses=True
        )
        
        # 测试连接
        r.ping()
        
        # 测试读写
        test_key = 'health_check_test'
        r.set(test_key, 'test_value', ex=10)
        value = r.get(test_key)
        r.delete(test_key)
        
        return {
            'success': True,
            'message': 'Redis连接正常',
            'details': {
                'test_read_write': value == 'test_value'
            }
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'Redis连接失败: {str(e)}'
        }


def check_disk_space():
    """检查磁盘空间"""
    try:
        import shutil
        
        # 检查当前目录磁盘空间
        total, used, free = shutil.disk_usage('.')
        
        # 计算使用率
        usage_percent = (used / total) * 100
        
        # 阈值检查
        if usage_percent > 90:
            return {
                'success': False,
                'message': f'磁盘空间不足: {usage_percent:.1f}%',
                'details': {
                    'total_gb': total / (1024**3),
                    'used_gb': used / (1024**3),
                    'free_gb': free / (1024**3),
                    'usage_percent': usage_percent
                }
            }
        elif usage_percent > 80:
            return {
                'success': True,
                'message': f'磁盘空间警告: {usage_percent:.1f}%',
                'details': {
                    'total_gb': total / (1024**3),
                    'used_gb': used / (1024**3),
                    'free_gb': free / (1024**3),
                    'usage_percent': usage_percent
                }
            }
        else:
            return {
                'success': True,
                'message': f'磁盘空间正常: {usage_percent:.1f}%',
                'details': {
                    'total_gb': total / (1024**3),
                    'used_gb': used / (1024**3),
                    'free_gb': free / (1024**3),
                    'usage_percent': usage_percent
                }
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'磁盘空间检查失败: {str(e)}'
        }


def check_memory():
    """检查内存使用"""
    try:
        import psutil
        
        memory = psutil.virtual_memory()
        usage_percent = memory.percent
        
        if usage_percent > 90:
            return {
                'success': False,
                'message': f'内存使用率过高: {usage_percent:.1f}%',
                'details': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'usage_percent': usage_percent
                }
            }
        elif usage_percent > 80:
            return {
                'success': True,
                'message': f'内存使用率警告: {usage_percent:.1f}%',
                'details': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'usage_percent': usage_percent
                }
            }
        else:
            return {
                'success': True,
                'message': f'内存使用率正常: {usage_percent:.1f}%',
                'details': {
                    'total_gb': memory.total / (1024**3),
                    'available_gb': memory.available / (1024**3),
                    'used_gb': memory.used / (1024**3),
                    'usage_percent': usage_percent
                }
            }
    except ImportError:
        return {
            'success': True,
            'message': '内存检查跳过 (psutil未安装)',
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'内存检查失败: {str(e)}'
        }


def check_log_files():
    """检查日志文件"""
    try:
        log_dir = 'logs'
        if not os.path.exists(log_dir):
            return {
                'success': True,
                'message': '日志目录不存在，跳过检查'
            }
        
        log_files = []
        total_size = 0
        
        for root, dirs, files in os.walk(log_dir):
            for file in files:
                if file.endswith('.log'):
                    file_path = os.path.join(root, file)
                    file_size = os.path.getsize(file_path)
                    total_size += file_size
                    log_files.append({
                        'path': file_path,
                        'size_mb': file_size / (1024**2)
                    })
        
        # 检查日志文件总大小 (阈值: 1GB)
        total_size_gb = total_size / (1024**3)
        
        if total_size_gb > 1.0:
            return {
                'success': False,
                'message': f'日志文件过大: {total_size_gb:.2f}GB',
                'details': {
                    'total_files': len(log_files),
                    'total_size_gb': total_size_gb,
                    'large_files': [f for f in log_files if f['size_mb'] > 100]
                }
            }
        else:
            return {
                'success': True,
                'message': f'日志文件正常: {total_size_gb:.2f}GB',
                'details': {
                    'total_files': len(log_files),
                    'total_size_gb': total_size_gb
                }
            }
    except Exception as e:
        return {
            'success': False,
            'message': f'日志文件检查失败: {str(e)}'
        }


def main():
    """主函数"""
    checker = HealthChecker()
    
    # 添加关键检查项
    checker.add_check('web_service', check_web_service, critical=True)
    checker.add_check('database', check_database, critical=True)
    checker.add_check('redis', check_redis, critical=True)
    
    # 添加非关键检查项
    checker.add_check('disk_space', check_disk_space, critical=False)
    checker.add_check('memory', check_memory, critical=False)
    checker.add_check('log_files', check_log_files, critical=False)
    
    # 运行检查
    results = checker.run_checks()
    
    # 输出结果
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        import json
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        print(f"健康检查结果: {'✓ 健康' if results['healthy'] else '✗ 异常'}")
        print(f"总计: {results['summary']['total']} 项")
        print(f"通过: {results['summary']['passed']} 项")
        print(f"失败: {results['summary']['failed']} 项")
        print(f"警告: {results['summary']['warnings']} 项")
        print()
        
        for name, check in results['checks'].items():
            status_icon = '✓' if check['status'] == 'passed' else '✗' if check['status'] == 'failed' else '!'
            critical_mark = ' [关键]' if check['critical'] else ''
            print(f"{status_icon} {name}{critical_mark}: {check['message']}")
    
    # 返回适当的退出码
    sys.exit(0 if results['healthy'] else 1)


if __name__ == '__main__':
    main()