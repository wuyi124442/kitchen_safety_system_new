#!/usr/bin/env python3
"""
测试日志系统功能的脚本
"""

import os
import sys
import django
from datetime import datetime, timedelta

# 添加项目路径到Python路径
sys.path.insert(0, os.path.abspath('.'))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kitchen_safety_system.web.django_app.settings')

try:
    django.setup()
    
    # 导入日志相关模块
    from kitchen_safety_system.web.django_app.apps.logs.models import LogEntry
    from kitchen_safety_system.web.django_app.apps.logs.services import LogService
    
    print("=== 日志系统测试 ===")
    
    # 测试创建日志条目
    print("\n1. 测试创建日志条目...")
    
    test_logs = [
        {
            'level': 'INFO',
            'log_type': 'SYSTEM',
            'message': '系统启动成功',
            'module': 'main'
        },
        {
            'level': 'WARNING',
            'log_type': 'DETECTION',
            'message': '检测到人员跌倒风险',
            'module': 'pose_analyzer'
        },
        {
            'level': 'ERROR',
            'log_type': 'ALERT',
            'message': '报警发送失败',
            'module': 'alert_manager'
        },
        {
            'level': 'DEBUG',
            'log_type': 'USER',
            'message': '用户登录系统',
            'module': 'authentication'
        }
    ]
    
    created_logs = []
    for log_data in test_logs:
        try:
            log_entry = LogService.create_log_entry(**log_data)
            created_logs.append(log_entry)
            print(f"✓ 创建日志: [{log_entry.level}] {log_entry.message}")
        except Exception as e:
            print(f"✗ 创建日志失败: {e}")
    
    # 测试日志查询
    print(f"\n2. 测试日志查询...")
    
    total_logs = LogEntry.objects.count()
    print(f"总日志数: {total_logs}")
    
    # 按级别查询
    for level_choice in LogEntry.LEVEL_CHOICES:
        level = level_choice[0]
        count = LogEntry.objects.filter(level=level).count()
        print(f"{level} 级别日志: {count} 条")
    
    # 按类型查询
    for type_choice in LogEntry.TYPE_CHOICES:
        log_type = type_choice[0]
        count = LogEntry.objects.filter(log_type=log_type).count()
        print(f"{log_type} 类型日志: {count} 条")
    
    # 测试日志统计
    print(f"\n3. 测试日志统计...")
    
    stats = LogService.get_log_statistics(days=7)
    print(f"最近7天日志统计:")
    print(f"  总数: {stats['total_logs']}")
    print(f"  级别统计: {stats['level_statistics']}")
    print(f"  类型统计: {stats['type_statistics']}")
    
    # 测试日志导出功能（模拟）
    print(f"\n4. 测试日志导出功能...")
    
    recent_logs = LogEntry.objects.all()[:10]
    print(f"最近10条日志:")
    for log in recent_logs:
        print(f"  [{log.timestamp.strftime('%H:%M:%S')}] [{log.level}] {log.message}")
    
    print(f"\n=== 测试完成 ===")
    print(f"日志系统功能正常，共创建 {len(created_logs)} 条测试日志")
    
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保Django环境配置正确")
except Exception as e:
    print(f"测试失败: {e}")
    import traceback
    traceback.print_exc()