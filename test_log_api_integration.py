#!/usr/bin/env python3
"""
测试日志API集成功能
"""

import json
import requests
from datetime import datetime, timedelta

# API基础URL（假设Django服务运行在localhost:8000）
BASE_URL = "http://localhost:8000"

def test_log_api():
    """测试日志API功能"""
    
    print("=== 日志API集成测试 ===")
    
    # 测试数据
    test_session = requests.Session()
    
    # 1. 测试日志列表API
    print("\n1. 测试日志列表API...")
    
    try:
        response = test_session.get(f"{BASE_URL}/logs/api/logs/")
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 获取日志列表成功")
            print(f"  总数: {data.get('count', 0)}")
            print(f"  结果数: {len(data.get('results', []))}")
        else:
            print(f"✗ 获取日志列表失败: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ 连接失败，请确保Django服务正在运行")
        return False
    except Exception as e:
        print(f"✗ 请求失败: {e}")
        return False
    
    # 2. 测试日志查询参数
    print("\n2. 测试日志查询参数...")
    
    query_params = {
        'level': 'ERROR',
        'log_type': 'SYSTEM',
        'page_size': 10
    }
    
    try:
        response = test_session.get(f"{BASE_URL}/logs/api/logs/", params=query_params)
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 带参数查询成功")
            print(f"  ERROR级别日志数: {len(data.get('results', []))}")
        else:
            print(f"✗ 带参数查询失败: {response.text}")
    except Exception as e:
        print(f"✗ 查询失败: {e}")
    
    # 3. 测试日志统计API
    print("\n3. 测试日志统计API...")
    
    try:
        response = test_session.get(f"{BASE_URL}/logs/api/logs/statistics/")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 获取统计信息成功")
            print(f"  总日志数: {data.get('total_logs', 0)}")
            print(f"  级别统计: {data.get('level_statistics', {})}")
        else:
            print(f"✗ 获取统计信息失败: {response.text}")
    except Exception as e:
        print(f"✗ 统计查询失败: {e}")
    
    # 4. 测试实时日志API
    print("\n4. 测试实时日志API...")
    
    try:
        response = test_session.get(f"{BASE_URL}/logs/api/logs/realtime/")
        if response.status_code == 200:
            data = response.json()
            print(f"✓ 获取实时日志成功")
            print(f"  实时日志数: {len(data.get('logs', []))}")
            print(f"  最后ID: {data.get('last_id', 0)}")
        else:
            print(f"✗ 获取实时日志失败: {response.text}")
    except Exception as e:
        print(f"✗ 实时日志查询失败: {e}")
    
    # 5. 测试日志导出API
    print("\n5. 测试日志导出API...")
    
    export_params = {
        'format': 'json',
        'level': 'INFO'
    }
    
    try:
        response = test_session.get(f"{BASE_URL}/logs/api/logs/export/", params=export_params)
        if response.status_code == 200:
            print(f"✓ 日志导出成功")
            print(f"  Content-Type: {response.headers.get('Content-Type')}")
            print(f"  Content-Length: {len(response.content)} bytes")
        else:
            print(f"✗ 日志导出失败: {response.text}")
    except Exception as e:
        print(f"✗ 导出失败: {e}")
    
    print(f"\n=== API测试完成 ===")
    return True

def test_web_interface():
    """测试Web界面"""
    
    print("\n=== Web界面测试 ===")
    
    test_session = requests.Session()
    
    # 测试日志查询页面
    try:
        response = test_session.get(f"{BASE_URL}/logs/")
        if response.status_code == 200:
            print("✓ 日志查询页面访问成功")
        else:
            print(f"✗ 日志查询页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 页面访问失败: {e}")
    
    # 测试实时监控页面
    try:
        response = test_session.get(f"{BASE_URL}/logs/monitor/")
        if response.status_code == 200:
            print("✓ 实时监控页面访问成功")
        else:
            print(f"✗ 实时监控页面访问失败: {response.status_code}")
    except Exception as e:
        print(f"✗ 监控页面访问失败: {e}")

if __name__ == "__main__":
    print("日志系统集成测试")
    print("注意: 此测试需要Django服务运行在 http://localhost:8000")
    print("请先启动Django服务: python manage.py runserver")
    
    input("\n按Enter键开始测试...")
    
    # 运行API测试
    api_success = test_log_api()
    
    if api_success:
        # 运行Web界面测试
        test_web_interface()
    
    print("\n测试完成！")