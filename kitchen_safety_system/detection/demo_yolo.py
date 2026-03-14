"""
YOLO检测器演示脚本

演示YOLO检测器的功能，包括实时检测和性能测试。
"""

import cv2
import numpy as np
import time
import argparse
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from kitchen_safety_system.detection.yolo_detector import YOLODetector
from kitchen_safety_system.core.interfaces import DetectionType


def create_demo_frame(width: int = 640, height: int = 480) -> np.ndarray:
    """
    创建演示用的测试帧
    
    Args:
        width: 图像宽度
        height: 图像高度
        
    Returns:
        np.ndarray: 测试图像帧
    """
    # 创建厨房场景背景
    frame = np.ones((height, width, 3), dtype=np.uint8) * 50
    
    # 添加厨房元素
    # 绘制灶台（矩形）
    cv2.rectangle(frame, (400, 300), (600, 450), (100, 100, 150), -1)
    cv2.rectangle(frame, (400, 300), (600, 450), (200, 200, 200), 2)
    
    # 绘制火焰效果（橙红色圆形）
    cv2.circle(frame, (500, 320), 20, (0, 100, 255), -1)
    cv2.circle(frame, (480, 325), 15, (0, 150, 255), -1)
    cv2.circle(frame, (520, 325), 15, (0, 150, 255), -1)
    
    # 绘制人员轮廓（简化的人形）
    # 头部
    cv2.circle(frame, (150, 120), 30, (200, 180, 160), -1)
    # 身体
    cv2.rectangle(frame, (120, 150), (180, 300), (200, 180, 160), -1)
    # 手臂
    cv2.rectangle(frame, (90, 170), (120, 250), (200, 180, 160), -1)
    cv2.rectangle(frame, (180, 170), (210, 250), (200, 180, 160), -1)
    # 腿部
    cv2.rectangle(frame, (130, 300), (150, 420), (200, 180, 160), -1)
    cv2.rectangle(frame, (160, 300), (180, 420), (200, 180, 160), -1)
    
    # 添加一些噪声使图像更真实
    noise = np.random.randint(-20, 20, frame.shape, dtype=np.int16)
    frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return frame


def demo_basic_detection():
    """基础检测演示"""
    print("=== YOLO检测器基础功能演示 ===")
    
    # 初始化检测器
    print("正在初始化YOLO检测器...")
    detector = YOLODetector(confidence_threshold=0.3)
    
    if not detector.is_loaded:
        print("❌ 检测器初始化失败")
        return
    
    print("✅ 检测器初始化成功")
    print(f"模型路径: {detector.model_path}")
    print(f"置信度阈值: {detector.confidence_threshold}")
    
    # 创建测试图像
    print("\n正在创建测试图像...")
    test_frame = create_demo_frame()
    
    # 执行检测
    print("正在执行目标检测...")
    start_time = time.time()
    detections = detector.detect(test_frame)
    inference_time = time.time() - start_time
    
    print(f"检测完成，耗时: {inference_time:.3f}秒")
    print(f"检测到 {len(detections)} 个目标:")
    
    # 显示检测结果
    for i, detection in enumerate(detections):
        print(f"  {i+1}. {detection.detection_type.value}")
        print(f"     位置: ({detection.bbox.x}, {detection.bbox.y})")
        print(f"     尺寸: {detection.bbox.width}x{detection.bbox.height}")
        print(f"     置信度: {detection.bbox.confidence:.3f}")
    
    # 可视化结果
    result_frame = detector.visualize_detections(test_frame, detections)
    
    # 保存结果图像
    output_path = "yolo_detection_result.jpg"
    cv2.imwrite(output_path, result_frame)
    print(f"\n检测结果已保存到: {output_path}")
    
    # 显示性能统计
    stats = detector.get_performance_stats()
    print(f"\n性能统计:")
    print(f"  平均推理时间: {stats['average_inference_time']:.3f}秒")
    print(f"  平均FPS: {stats['average_fps']:.1f}")


def demo_video_detection(video_source: str = "0"):
    """视频检测演示"""
    print("=== YOLO视频检测演示 ===")
    
    # 初始化检测器
    detector = YOLODetector(confidence_threshold=0.5)
    if not detector.is_loaded:
        print("❌ 检测器初始化失败")
        return
    
    # 打开视频源
    if video_source.isdigit():
        cap = cv2.VideoCapture(int(video_source))
    else:
        cap = cv2.VideoCapture(video_source)
    
    if not cap.isOpened():
        print(f"❌ 无法打开视频源: {video_source}")
        return
    
    print("✅ 视频源已打开")
    print("按 'q' 退出，按 's' 保存当前帧")
    
    frame_count = 0
    total_time = 0
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("视频结束或读取失败")
                break
            
            # 执行检测
            start_time = time.time()
            detections = detector.detect(frame)
            inference_time = time.time() - start_time
            
            # 可视化结果
            result_frame = detector.visualize_detections(frame, detections)
            
            # 添加性能信息
            fps = 1.0 / inference_time if inference_time > 0 else 0
            cv2.putText(result_frame, f"FPS: {fps:.1f}", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(result_frame, f"Detections: {len(detections)}", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            
            # 显示结果
            cv2.imshow('YOLO Kitchen Safety Detection', result_frame)
            
            # 更新统计
            frame_count += 1
            total_time += inference_time
            
            # 处理按键
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                filename = f"detection_frame_{frame_count}.jpg"
                cv2.imwrite(filename, result_frame)
                print(f"帧已保存: {filename}")
    
    except KeyboardInterrupt:
        print("\n检测被用户中断")
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        
        # 显示最终统计
        if frame_count > 0:
            avg_time = total_time / frame_count
            avg_fps = 1.0 / avg_time if avg_time > 0 else 0
            print(f"\n最终统计:")
            print(f"  处理帧数: {frame_count}")
            print(f"  平均推理时间: {avg_time:.3f}秒")
            print(f"  平均FPS: {avg_fps:.1f}")


def demo_performance_test():
    """性能测试演示"""
    print("=== YOLO检测器性能测试 ===")
    
    # 初始化检测器
    detector = YOLODetector()
    if not detector.is_loaded:
        print("❌ 检测器初始化失败")
        return
    
    # 创建不同尺寸的测试图像
    test_sizes = [(320, 240), (640, 480), (1280, 720)]
    test_iterations = 50
    
    print(f"将对每个尺寸执行 {test_iterations} 次检测")
    
    for width, height in test_sizes:
        print(f"\n测试图像尺寸: {width}x{height}")
        
        # 创建测试图像
        test_frame = create_demo_frame(width, height)
        
        # 预热
        for _ in range(5):
            detector.detect(test_frame)
        
        # 重置统计
        detector.reset_stats()
        
        # 执行性能测试
        start_time = time.time()
        detection_counts = []
        
        for i in range(test_iterations):
            detections = detector.detect(test_frame)
            detection_counts.append(len(detections))
            
            if (i + 1) % 10 == 0:
                print(f"  进度: {i + 1}/{test_iterations}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 计算统计信息
        avg_detections = sum(detection_counts) / len(detection_counts)
        avg_time_per_frame = total_time / test_iterations
        fps = 1.0 / avg_time_per_frame
        
        print(f"  总耗时: {total_time:.2f}秒")
        print(f"  平均每帧: {avg_time_per_frame:.3f}秒")
        print(f"  平均FPS: {fps:.1f}")
        print(f"  平均检测数: {avg_detections:.1f}")
        
        # 检查是否满足性能要求
        if fps >= 15:
            print(f"  ✅ 性能合格 (≥15 FPS)")
        else:
            print(f"  ❌ 性能不足 (<15 FPS)")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="YOLO检测器演示")
    parser.add_argument('--mode', choices=['basic', 'video', 'performance'], 
                       default='basic', help='演示模式')
    parser.add_argument('--video', default='0', 
                       help='视频源 (摄像头编号或视频文件路径)')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'basic':
            demo_basic_detection()
        elif args.mode == 'video':
            demo_video_detection(args.video)
        elif args.mode == 'performance':
            demo_performance_test()
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()