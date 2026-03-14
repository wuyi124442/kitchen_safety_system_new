#!/usr/bin/env python3
"""
测试仪表板设置功能
"""

import requests
import json

def test_dashboard_access():
    """测试仪表板访问"""
    base_url = "http://127.0.0.1:8000"
    
    print("测试仪表板功能...")
    
    try:
        # 测试仪表板页面
        response = requests.get(f"{base_url}/dashboard/", timeout=5)
        print(f"仪表板页面: {response.status_code}")
        
        # 测试系统状态API
        response = requests.get(f"{base_url}/dashboard/api/system-status/", timeout=5)
        print(f"系统状态API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  - 成功: {data.get('success', False)}")
        
        # 测试配置页面
        response = requests.get(f"{base_url}/config/", timeout=5)
        print(f"配置页面: {response.status_code}")
        
        # 测试配置API
        response = requests.get(f"{base_url}/config/api/configs/", timeout=5)
        print(f"配置API: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"  - 成功: {data.get('success', False)}")
        
        print("\n✅ 所有测试完成！")
        print("现在可以访问:")
        print(f"  - 仪表板: {base_url}/dashboard/")
        print(f"  - 系统配置: {base_url}/config/")
        print(f"  - 报警历史: {base_url}/alerts/")
        
    except Exception as e:
        print(f"测试失败: {e}")
        print("请确保Django服务器正在运行: run_django_direct.bat")

if __name__ == '__main__':
    test_dashboard_access()