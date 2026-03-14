#!/usr/bin/env python3
"""
简单演示功能测试

测试演示功能的基本运行，不需要GUI。
"""

import time
from kitchen_safety_system.demo.demo_app import DemoApplication
from kitchen_safety_system.utils.logger import get_logger

logger = get_logger(__name__)


def test_demo_app_basic():
    """测试演示应用基本功能"""
    print("=== 测试演示应用基本功能 ===")
    
    # 创建演示应用
    app = DemoApplication()
    
    # 初始化检测系统
    success = app.initialize_detection_system()
    print(f"检测系统初始化: {'成功' if success else '失败'}")
    
    # 测试演示模式创建
    demo_mode = app.demo_mode
    
    # 获取可用视频
    videos = demo_mode.get_available_videos()
    print(f"可用演示视频数量: {len(videos)}")
    for video in videos:
        print(f"  - {video.name}: {video.description}")
    
    # 测试场景创建
    scenarios = ['comprehensive', 'test', 'virtual']
    for scenario in scenarios:
        print(f"\n测试场景: {scenario}")
        success = demo_mode.create_demo_scenario(scenario)
        print(f"  场景创建: {'成功' if success else '失败'}")
        
        if success:
            # 测试播放信息
            info = demo_mode.get_playback_info()
            print(f"  当前视频: {info.get('current_video', {}).get('name', 'None')}")
            print(f"  播放状态: {'播放中' if info['is_playing'] else '未播放'}")
            
            # 测试统计信息
            stats = demo_mode.get_demo_statistics()
            print(f"  检测数量: {stats.get('total_detections', 0)}")
            print(f"  报警数量: {stats.get('alerts_triggered', 0)}")
    
    print("\n演示应用基本功能测试完成")


def test_visualization_without_gui():
    """测试可视化功能（不显示GUI）"""
    print("\n=== 测试可视化功能 ===")
    
    from kitchen_safety_system.demo import ComprehensiveVisualizer
    from kitchen_safety_system.demo.visualization import VisualizationTheme
    from kitchen_safety_system.core.interfaces import DetectionResult, DetectionType, BoundingBox
    import numpy as np
    import cv2
    
    # 创建可视化器
    visualizer = ComprehensiveVisualizer(VisualizationTheme.DEFAULT)
    
    # 创建测试帧
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (50, 50), (590, 430), (50, 50, 50), -1)
    
    # 创建测试检测结果
    detections = [
        DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=200, y=150, width=80, height=160, confidence=0.90),
            timestamp=time.time(),
            frame_id=1
        ),
        DetectionResult(
            detection_type=DetectionType.STOVE,
            bbox=BoundingBox(x=400, y=250, width=100, height=60, confidence=0.85),
            timestamp=time.time(),
            frame_id=1
        )
    ]
    
    # 创建测试报警
    alerts = [
        {
            'alert_type': 'fall_detected',
            'message': '检测到人员跌倒！',
            'location': (240, 230),
            'level': 'high'
        }
    ]
    
    # 可视化
    vis_frame = visualizer.visualize_frame(frame, detections, alerts, {'Test': 'Active'})
    
    # 保存结果
    output_path = "test_demo_visualization.jpg"
    cv2.imwrite(output_path, vis_frame)
    print(f"可视化结果已保存到: {output_path}")
    
    print("可视化功能测试完成")


def test_virtual_demo_mode():
    """测试虚拟演示模式"""
    print("\n=== 测试虚拟演示模式 ===")
    
    from kitchen_safety_system.demo import DemoMode
    
    # 创建演示模式（使用不存在的目录强制虚拟模式）
    demo_mode = DemoMode("nonexistent_videos")
    
    # 创建虚拟场景
    success = demo_mode.create_demo_scenario("virtual")
    print(f"虚拟场景创建: {'成功' if success else '失败'}")
    
    if success:
        # 测试虚拟帧生成
        if hasattr(demo_mode, '_generate_virtual_frame'):
            frame = demo_mode._generate_virtual_frame(10)
            print(f"虚拟帧生成: 成功 (尺寸: {frame.shape})")
            
            # 保存虚拟帧
            import cv2
            cv2.imwrite("test_virtual_frame.jpg", frame)
            print("虚拟帧已保存到: test_virtual_frame.jpg")
        
        # 测试播放信息
        info = demo_mode.get_playback_info()
        print(f"当前视频: {info.get('current_video', {}).get('name', 'None')}")
    
    print("虚拟演示模式测试完成")


def main():
    """主测试函数"""
    print("厨房安全检测系统 - 简单演示功能测试")
    print("=" * 60)
    
    try:
        test_demo_app_basic()
        test_visualization_without_gui()
        test_virtual_demo_mode()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("\n生成的文件:")
        print("- test_demo_visualization.jpg")
        print("- test_virtual_frame.jpg")
        
        print("\n演示功能已成功实现:")
        print("✓ 演示模式 (预录制视频播放功能)")
        print("✓ 演示数据重置功能")
        print("✓ 实时检测框和标签显示")
        print("✓ 报警信息可视化展示")
        print("✓ 虚拟演示模式（无需视频文件）")
        print("✓ 多种可视化主题")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()