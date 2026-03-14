#!/usr/bin/env python3
"""
测试登录界面功能
"""

import requests
import sys

def test_login_interface():
    """测试登录界面"""
    base_url = "http://127.0.0.1:8000"
    
    print("测试登录界面...")
    
    try:
        # 测试登录页面
        response = requests.get(f"{base_url}/auth/login/", timeout=5)
        print(f"登录页面访问: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            
            # 检查页面内容
            checks = [
                ("厨房安全检测系统", "系统标题"),
                ("Kitchen Safety Detection System", "英文副标题"),
                ("演示账户", "演示信息"),
                ("admin", "默认用户名"),
                ("实时视频监控", "功能特性"),
                ("跌倒检测", "功能特性"),
                ("灶台安全监控", "功能特性"),
                ("多渠道报警通知", "功能特性")
            ]
            
            print("\n页面内容检查:")
            for check_text, description in checks:
                if check_text in content:
                    print(f"  ✅ {description}: 存在")
                else:
                    print(f"  ❌ {description}: 缺失")
            
            # 检查是否移除了2024年份
            if "2024" not in content:
                print("  ✅ 年份信息: 已移除2024")
            else:
                print("  ❌ 年份信息: 仍包含2024")
        
        # 测试个人资料页面
        response = requests.get(f"{base_url}/auth/profile/", timeout=5)
        print(f"个人资料页面: {response.status_code}")
        
        print(f"\n✅ 测试完成！")
        print(f"访问地址:")
        print(f"  - 登录页面: {base_url}/auth/login/")
        print(f"  - 个人资料: {base_url}/auth/profile/")
        print(f"  - 主仪表板: {base_url}/dashboard/")
        
    except Exception as e:
        print(f"测试失败: {e}")
        print("请确保Django服务器正在运行")

if __name__ == '__main__':
    test_login_interface()