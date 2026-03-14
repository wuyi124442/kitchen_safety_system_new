#!/usr/bin/env python3
"""
系统集成演示脚本

演示主检测系统控制器和配置管理器的集成功能。
"""

import time
import json
import tempfile
from pathlib import Path

from kitchen_safety_system.detection.detection_system import DetectionSystem
from kitchen_safety_system.core.configuration_manager import ConfigurationManager
from kitchen_safety_system.core.models import SystemConfig
from kitchen_safety_system.utils.logger import get_logger

logger = get_logger(__name__)


def demo_configuration_manager():
    """演示配置管理器功能"""
    print("=" * 60)
    print("配置管理器演示")
    print("=" * 60)
    
    # 创建临时配置目录
    temp_dir = tempfile.mkdtemp()
    config_manager = ConfigurationManager(config_dir=temp_dir, enable_hot_reload=False)
    
    print(f"配置目录: {temp_dir}")
    
    # 1. 设置基本配置
    print("\n1. 设置基本配置...")
    config_manager.set_config('system.name', 'Kitchen Safety Detection System')
    config_manager.set_config('system.version', '1.0.0')
    config_manager.set_config('detection.confidence_threshold', 0.7)
    config_manager.set_config('detection.fps', 20)
    
    # 2. 获取配置
    print("\n2. 获取配置...")
    print(f"系统名称: {config_manager.get_config('system.name')}")
    print(f"系统版本: {config_manager.get_config('system.version')}")
    print(f"检测置信度: {config_manager.get_config('detection.confidence_threshold')}")
    print(f"检测帧率: {config_manager.get_config('detection.fps')}")
    
    # 3. 保存配置到文件
    print("\n3. 保存配置到文件...")
    config_manager.save_config_to_file('system', 'system_config.json')
    
    # 4. 从文件加载配置
    print("\n4. 从文件加载配置...")
    config_file = Path(temp_dir) / 'test_config.json'
    test_config = {
        'video': {
            'source': 'camera',
            'resolution': [1920, 1080],
            'fps': 30
        },
        'alerts': {
            'email_enabled': True,
            'sms_enabled': False
        }
    }
    
    with open(config_file, 'w') as f:
        json.dump(test_config, f, indent=2)
    
    config_manager.add_config_file('test', 'test_config.json')
    
    print(f"视频源: {config_manager.get_config('test.video.source')}")
    print(f"视频分辨率: {config_manager.get_config('test.video.resolution')}")
    print(f"邮件报警: {config_manager.get_config('test.alerts.email_enabled')}")
    
    # 5. 配置变更回调演示
    print("\n5. 配置变更回调演示...")
    
    def config_change_callback(key, old_value, new_value):
        print(f"配置变更: {key} 从 {old_value} 变为 {new_value}")
    
    config_manager.add_change_callback(config_change_callback)
    config_manager.set_config('detection.confidence_threshold', 0.8)
    config_manager.set_config('detection.fps', 25)
    
    print("配置管理器演示完成!")
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir)
    
    return config_manager


def demo_detection_system():
    """演示检测系统功能"""
    print("\n" + "=" * 60)
    print("检测系统演示")
    print("=" * 60)
    
    # 1. 创建系统配置
    print("\n1. 创建系统配置...")
    config = SystemConfig(
        video_input_source="0",  # 使用摄像头
        detection_fps=15,
        confidence_threshold=0.6,
        fall_confidence_threshold=0.7,
        stove_distance_threshold=150.0,
        unattended_time_threshold=60.0,
        enable_sound_alert=True,
        enable_email_alert=False
    )
    
    print(f"视频源: {config.video_input_source}")
    print(f"检测帧率: {config.detection_fps}")
    print(f"检测置信度: {config.confidence_threshold}")
    print(f"跌倒检测置信度: {config.fall_confidence_threshold}")
    
    # 2. 创建检测系统
    print("\n2. 创建检测系统...")
    detection_system = DetectionSystem(config)
    
    # 3. 获取系统状态
    print("\n3. 获取系统状态...")
    status = detection_system.get_system_status()
    print(f"系统已初始化: {status['is_initialized']}")
    print(f"系统运行中: {status['is_running']}")
    print(f"处理帧数: {status['frame_count']}")
    print(f"错误计数: {status['error_count']}")
    print(f"当前FPS: {status['current_fps']}")
    
    # 4. 模拟系统初始化（不实际启动摄像头）
    print("\n4. 模拟系统初始化...")
    try:
        # 这里会失败因为没有实际的摄像头和模型文件，但可以展示错误处理
        result = detection_system.initialize()
        if result:
            print("系统初始化成功!")
        else:
            print("系统初始化失败（预期的，因为缺少摄像头和模型文件）")
    except Exception as e:
        print(f"系统初始化异常: {e}")
    
    # 5. 展示配置转换
    print("\n5. 系统配置转换...")
    config_dict = config.to_dict()
    print("配置字典:")
    for key, value in config_dict.items():
        print(f"  {key}: {value}")
    
    print("检测系统演示完成!")
    
    return detection_system


def demo_integrated_system():
    """演示系统集成功能"""
    print("\n" + "=" * 60)
    print("系统集成演示")
    print("=" * 60)
    
    # 1. 创建配置管理器
    print("\n1. 创建配置管理器...")
    temp_dir = tempfile.mkdtemp()
    config_manager = ConfigurationManager(config_dir=temp_dir, enable_hot_reload=False)
    
    # 2. 设置系统配置
    print("\n2. 设置系统配置...")
    config_manager.set_config('detection.confidence_threshold', 0.75)
    config_manager.set_config('detection.fps', 18)
    config_manager.set_config('video.source', 'demo_video.mp4')
    config_manager.set_config('alerts.sound_enabled', True)
    config_manager.set_config('alerts.email_enabled', True)
    config_manager.set_config('stove.distance_threshold', 120.0)
    config_manager.set_config('stove.unattended_time', 45.0)
    
    # 3. 从配置管理器创建系统配置
    print("\n3. 从配置管理器创建系统配置...")
    system_config = SystemConfig(
        video_input_source=config_manager.get_config('video.source') or "0",
        detection_fps=config_manager.get_config('detection.fps') or 15,
        confidence_threshold=config_manager.get_config('detection.confidence_threshold') or 0.5,
        stove_distance_threshold=config_manager.get_config('stove.distance_threshold') or 100.0,
        unattended_time_threshold=config_manager.get_config('stove.unattended_time') or 30.0,
        enable_sound_alert=config_manager.get_config('alerts.sound_enabled') or True,
        enable_email_alert=config_manager.get_config('alerts.email_enabled') or False
    )
    
    print(f"集成配置 - 视频源: {system_config.video_input_source}")
    print(f"集成配置 - 检测FPS: {system_config.detection_fps}")
    print(f"集成配置 - 置信度: {system_config.confidence_threshold}")
    print(f"集成配置 - 灶台距离阈值: {system_config.stove_distance_threshold}")
    
    # 4. 创建检测系统
    print("\n4. 创建集成检测系统...")
    detection_system = DetectionSystem(system_config)
    
    # 5. 演示配置热更新
    print("\n5. 演示配置热更新...")
    
    def on_config_change(key, old_value, new_value):
        print(f"配置热更新: {key} = {new_value} (原值: {old_value})")
        # 在实际系统中，这里可以更新检测系统的配置
        if key == 'detection.confidence_threshold':
            print(f"  -> 更新检测系统置信度阈值")
        elif key == 'detection.fps':
            print(f"  -> 更新检测系统帧率")
    
    config_manager.add_change_callback(on_config_change)
    
    # 模拟运行时配置更新
    print("模拟运行时配置更新...")
    config_manager.set_config('detection.confidence_threshold', 0.85)
    config_manager.set_config('detection.fps', 22)
    config_manager.set_config('alerts.sound_enabled', False)
    
    # 6. 系统状态监控
    print("\n6. 系统状态监控...")
    status = detection_system.get_system_status()
    print("系统状态:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    print("\n系统集成演示完成!")
    
    # 清理
    import shutil
    shutil.rmtree(temp_dir)


def main():
    """主函数"""
    print("厨房安全检测系统 - 系统集成演示")
    print("=" * 80)
    
    try:
        # 1. 配置管理器演示
        demo_configuration_manager()
        
        # 2. 检测系统演示
        demo_detection_system()
        
        # 3. 系统集成演示
        demo_integrated_system()
        
        print("\n" + "=" * 80)
        print("所有演示完成!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()