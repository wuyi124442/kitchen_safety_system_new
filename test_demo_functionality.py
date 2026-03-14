#!/usr/bin/env python3
"""
演示功能测试脚本

测试演示模式和可视化功能的基本功能。
"""

import cv2
import numpy as np
import time
from pathlib import Path

from kitchen_safety_system.demo import DemoMode, DetectionVisualizer, AlertVisualizer, ComprehensiveVisualizer
from kitchen_safety_system.demo.visualization import VisualizationTheme
from kitchen_safety_system.core.interfaces import DetectionResult, DetectionType, BoundingBox
from kitchen_safety_system.utils.logger import get_logger

logger = get_logger(__name__)


def test_demo_mode():
    """测试演示模式功能"""
    print("\n=== 测试演示模式 ===")
    
    # 创建演示模式实例
    demo_mode = DemoMode("demo_videos")
    
    # 测试获取可用视频
    available_videos = demo_mode.get_available_videos()
    print(f"可用演示视频数量: {len(available_videos)}")
    
    for video in available_videos:
        print(f"  - {video.name}: {video.description}")
    
    # 测试演示数据重置
    print("\n测试演示数据重置...")
    demo_mode.reset_demo_data()
    
    # 测试添加演示数据
    print("测试添加演示数据...")
    
    # 创建模拟检测结果
    detection = DetectionResult(
        detection_type=DetectionType.PERSON,
        bbox=BoundingBox(x=100, y=100, width=80, height=160, confidence=0.85),
        timestamp=time.time(),
        frame_id=1
    )
    
    demo_mode.add_demo_detection(detection)
    demo_mode.add_demo_alert("fall_detected", "测试跌倒报警", level="high")
    
    # 获取统计信息
    stats = demo_mode.get_demo_statistics()
    print(f"演示统计信息: {stats}")
    
    # 清理
    demo_mode.cleanup()
    print("演示模式测试完成")


def test_detection_visualizer():
    """测试检测结果可视化器"""
    print("\n=== 测试检测结果可视化器 ===")
    
    # 创建可视化器
    visualizer = DetectionVisualizer(VisualizationTheme.DEFAULT)
    
    # 创建测试图像
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 添加背景
    cv2.rectangle(frame, (50, 50), (590, 430), (50, 50, 50), -1)
    cv2.putText(frame, "Kitchen Safety Detection Test", (150, 250), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # 创建测试检测结果
    detections = [
        DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=100, y=100, width=80, height=160, confidence=0.95),
            timestamp=time.time(),
            frame_id=1
        ),
        DetectionResult(
            detection_type=DetectionType.STOVE,
            bbox=BoundingBox(x=300, y=200, width=100, height=60, confidence=0.85),
            timestamp=time.time(),
            frame_id=1
        ),
        DetectionResult(
            detection_type=DetectionType.FLAME,
            bbox=BoundingBox(x=320, y=180, width=30, height=40, confidence=0.75),
            timestamp=time.time(),
            frame_id=1
        )
    ]
    
    # 可视化检测结果
    additional_info = {
        "Test Mode": "Active",
        "Frame Count": 100,
        "Processing Time": 0.05
    }
    
    vis_frame = visualizer.visualize_detections(frame, detections, additional_info)
    
    # 保存结果
    output_path = "test_detection_visualization.jpg"
    cv2.imwrite(output_path, vis_frame)
    print(f"检测可视化结果已保存到: {output_path}")
    
    print("检测结果可视化器测试完成")


def test_alert_visualizer():
    """测试报警可视化器"""
    print("\n=== 测试报警可视化器 ===")
    
    # 创建报警可视化器
    alert_visualizer = AlertVisualizer(VisualizationTheme.DEFAULT)
    
    # 创建测试图像
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 添加测试报警
    alert_visualizer.add_alert(
        "fall_detected", 
        "检测到人员跌倒！", 
        location=(200, 150),
        level="high"
    )
    
    alert_visualizer.add_alert(
        "unattended_stove",
        "灶台无人看管！",
        location=(400, 300),
        level="medium"
    )
    
    # 可视化报警
    vis_frame = alert_visualizer.visualize_alerts(frame)
    
    # 保存结果
    output_path = "test_alert_visualization.jpg"
    cv2.imwrite(output_path, vis_frame)
    print(f"报警可视化结果已保存到: {output_path}")
    
    print(f"当前报警数量: {alert_visualizer.get_alert_count()}")
    
    # 清除报警
    alert_visualizer.clear_alerts()
    print(f"清除后报警数量: {alert_visualizer.get_alert_count()}")
    
    print("报警可视化器测试完成")


def test_comprehensive_visualizer():
    """测试综合可视化器"""
    print("\n=== 测试综合可视化器 ===")
    
    # 创建综合可视化器
    visualizer = ComprehensiveVisualizer(VisualizationTheme.DARK)
    
    # 创建测试图像
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (0, 0), (640, 480), (30, 30, 30), -1)
    
    # 创建检测结果
    detections = [
        DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=150, y=120, width=90, height=180, confidence=0.92),
            timestamp=time.time(),
            frame_id=1
        ),
        DetectionResult(
            detection_type=DetectionType.STOVE,
            bbox=BoundingBox(x=350, y=250, width=120, height=80, confidence=0.88),
            timestamp=time.time(),
            frame_id=1
        )
    ]
    
    # 创建报警信息
    alerts = [
        {
            'alert_type': 'fall_detected',
            'message': '检测到人员跌倒！',
            'location': (195, 210),
            'level': 'high'
        }
    ]
    
    # 附加信息
    additional_info = {
        "Theme": "Dark",
        "Total Detections": 2,
        "Alert Count": 1,
        "System Status": "Active"
    }
    
    # 综合可视化
    vis_frame = visualizer.visualize_frame(frame, detections, alerts, additional_info)
    
    # 保存结果
    output_path = "test_comprehensive_visualization.jpg"
    cv2.imwrite(output_path, vis_frame)
    print(f"综合可视化结果已保存到: {output_path}")
    
    # 测试主题切换
    print("测试主题切换...")
    visualizer.set_theme(VisualizationTheme.HIGH_CONTRAST)
    
    vis_frame_hc = visualizer.visualize_frame(frame, detections, [], additional_info)
    output_path_hc = "test_comprehensive_visualization_hc.jpg"
    cv2.imwrite(output_path_hc, vis_frame_hc)
    print(f"高对比度主题结果已保存到: {output_path_hc}")
    
    print("综合可视化器测试完成")


def test_visualization_themes():
    """测试不同的可视化主题"""
    print("\n=== 测试可视化主题 ===")
    
    # 创建测试图像和数据
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    cv2.rectangle(frame, (20, 20), (620, 460), (40, 40, 40), -1)
    
    detection = DetectionResult(
        detection_type=DetectionType.PERSON,
        bbox=BoundingBox(x=200, y=150, width=100, height=200, confidence=0.90),
        timestamp=time.time(),
        frame_id=1
    )
    
    themes = [
        VisualizationTheme.DEFAULT,
        VisualizationTheme.DARK,
        VisualizationTheme.HIGH_CONTRAST
    ]
    
    for theme in themes:
        print(f"测试主题: {theme.value}")
        
        visualizer = DetectionVisualizer(theme)
        vis_frame = visualizer.visualize_detections(
            frame.copy(), 
            [detection],
            {"Theme": theme.value}
        )
        
        output_path = f"test_theme_{theme.value}.jpg"
        cv2.imwrite(output_path, vis_frame)
        print(f"  主题 {theme.value} 结果已保存到: {output_path}")
    
    print("可视化主题测试完成")


def create_demo_video_placeholder():
    """创建演示视频占位符"""
    print("\n=== 创建演示视频占位符 ===")
    
    demo_videos_dir = Path("demo_videos")
    demo_videos_dir.mkdir(exist_ok=True)
    
    # 创建简单的演示视频（如果OpenCV支持视频写入）
    try:
        # 视频参数
        width, height = 640, 480
        fps = 15
        duration = 10  # 10秒
        total_frames = fps * duration
        
        # 创建视频写入器
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_path = demo_videos_dir / "test_demo_video.mp4"
        
        out = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))
        
        if out.isOpened():
            print(f"创建测试视频: {video_path}")
            
            for frame_num in range(total_frames):
                # 创建测试帧
                frame = np.zeros((height, width, 3), dtype=np.uint8)
                
                # 添加背景
                cv2.rectangle(frame, (50, 50), (width-50, height-50), (50, 50, 50), -1)
                
                # 添加标题
                cv2.putText(frame, "Kitchen Safety Demo", (150, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
                
                # 添加帧计数
                cv2.putText(frame, f"Frame: {frame_num+1}/{total_frames}", (50, height-50),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
                
                # 添加移动的"人员"
                person_x = 100 + int((frame_num / total_frames) * 400)
                cv2.rectangle(frame, (person_x, 200), (person_x+60, 350), (0, 255, 0), 2)
                cv2.putText(frame, "Person", (person_x, 190), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                
                # 添加"灶台"
                cv2.rectangle(frame, (450, 300), (550, 380), (255, 165, 0), 2)
                cv2.putText(frame, "Stove", (455, 290), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 165, 0), 1)
                
                out.write(frame)
            
            out.release()
            print(f"测试视频创建完成: {video_path}")
        else:
            print("无法创建视频文件")
            
    except Exception as e:
        print(f"创建演示视频失败: {e}")
        print("请手动添加演示视频文件到 demo_videos/ 目录")


def main():
    """主测试函数"""
    print("厨房安全检测系统 - 演示功能测试")
    print("=" * 60)
    
    try:
        # 测试各个组件
        test_demo_mode()
        test_detection_visualizer()
        test_alert_visualizer()
        test_comprehensive_visualizer()
        test_visualization_themes()
        
        # 创建演示视频占位符
        create_demo_video_placeholder()
        
        print("\n" + "=" * 60)
        print("所有演示功能测试完成！")
        print("\n生成的文件:")
        print("- test_detection_visualization.jpg")
        print("- test_alert_visualization.jpg")
        print("- test_comprehensive_visualization.jpg")
        print("- test_comprehensive_visualization_hc.jpg")
        print("- test_theme_*.jpg")
        print("- demo_videos/test_demo_video.mp4 (如果支持)")
        
        print("\n下一步:")
        print("1. 添加真实的演示视频文件到 demo_videos/ 目录")
        print("2. 运行 python -m kitchen_safety_system.main demo 启动完整演示")
        print("3. 集成到Django Web界面中")
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()