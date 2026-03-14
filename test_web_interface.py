#!/usr/bin/env python3
"""
Web界面测试脚本
"""

import requests
import sys
import os

def test_web_interface():
    """测试Web界面的各个页面"""
    base_url = "http://127.0.0.1:8000"
    
    print("测试Web界面...")
    
    # 测试主页
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"主页: {response.status_code}")
    except Exception as e:
        print(f"主页访问失败: {e}")
    
    # 测试登录页面
    try:
        response = requests.get(f"{base_url}/auth/login/", timeout=5)
        print(f"登录页面: {response.status_code}")
    except Exception as e:
        print(f"登录页面访问失败: {e}")
    
    # 测试仪表板页面
    try:
        response = requests.get(f"{base_url}/dashboard/", timeout=5)
        print(f"仪表板页面: {response.status_code}")
    except Exception as e:
        print(f"仪表板页面访问失败: {e}")

if __name__ == '__main__':
    test_web_interface()