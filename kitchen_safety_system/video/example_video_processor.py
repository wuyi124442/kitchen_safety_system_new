"""
视频预处理器使用示例

演示VideoProcessor与VideoCapture的集成使用。
"""

import cv2
import numpy as np
import time
from typing import Optional

from .video_capture import VideoCapture
from .video_processor import VideoProcessor, VideoFormat, QualityLevel


def demo_video_processing():
    """
    演示视频处理功能
    
    展示VideoProcessor的各种功能:
    - 视频质量检测
    - 格式转换
    - 尺寸调整
    - 图像增强
    """
    print("=== 视频预处理器演示 ===")
    
    # 创建视频处理器
    processor = VideoProcessor(
        target_format=VideoFormat.BGR,
        target_size=(640, 480),
        quality_threshold=0.4,
        enable_enhancement=True
    )
    
    print(f"处理器配置:")
    print(f"- 目标格式: {processor.target_format.value}")
    print(f"- 目标尺寸: {processor.target_size}")
    print(f"- 质量阈值: {processor.quality_threshold}")
    print(f"- 图像增强: {processor.enable_enhancement}")
    print()
    
    # 创建测试帧
    test_frames = create_test_frames()
    
    print("处理测试帧...")
    for i, (frame_name, frame) in enumerate(test_frames.items()):
        print(f"\n--- 处理帧 {i+1}: {frame_name} ---")
        
        # 分析原始帧属性
        original_props = processor.analyze_frame_properties(frame)
        print(f"原始帧: {original_props['width']}x{original_props['height']}, "
              f"质量得分: {original_props['quality_score']:.3f} "
              f"({original_props['quality_level']})")
        
        # 处理帧
        start_time = time.time()
        processed_frame = processor.process_frame(frame)
        processing_time = time.time() - start_time
        
        # 分析处理后帧属性
        processed_props = processor.analyze_frame_properties(processed_frame)
        print(f"处理后: {processed_props['width']}x{processed_props['height']}, "
              f"质量得分: {processed_props['quality_score']:.3f} "
              f"({processed_props['quality_level']})")
        print(f"处理耗时: {processing_time*1000:.2f}ms")
    
    # 显示统计信息
    stats = processor.get_processing_stats()
    print(f"\n=== 处理统计 ===")
    print(f"处理帧数: {stats['processed_frames']}")
    print(f"质量警告: {stats['quality_warnings']}")
    print(f"格式转换: {stats['format_conversions']}")
    print(f"尺寸调整: {stats['resize_operations']}")
    print(f"质量警告率: {stats['quality_warning_rate']:.2%}")


def demo_format_conversion():
    """演示格式转换功能"""
    print("\n=== 格式转换演示 ===")
    
    # 创建测试帧
    test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
    
    formats = [VideoFormat.BGR, VideoFormat.RGB, VideoFormat.GRAY, VideoFormat.HSV]
    
    for format_type in formats:
        processor = VideoProcessor(target_format=format_type)
        result = processor.process_frame(test_frame)
        
        if format_type == VideoFormat.GRAY:
            print(f"{format_type.value}: {result.shape} (灰度)")
        else:
            print(f"{format_type.value}: {result.shape} (彩色)")


def demo_resolution_support():
    """演示多分辨率支持"""
    print("\n=== 多分辨率支持演示 ===")
    
    # 创建测试帧
    test_frame = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    print(f"原始帧尺寸: {test_frame.shape[1]}x{test_frame.shape[0]}")
    
    resolutions = [
        (320, 240, "QVGA"),
        (640, 480, "VGA"),
        (800, 600, "SVGA"),
        (1024, 768, "XGA"),
        (1920, 1080, "Full HD")
    ]
    
    for width, height, name in resolutions:
        processor = VideoProcessor(target_size=(width, height))
        result = processor.process_frame(test_frame)
        print(f"{name}: {result.shape[1]}x{result.shape[0]}")


def demo_with_video_capture():
    """
    演示与VideoCapture的集成使用
    
    注意: 这个演示需要摄像头或视频文件
    """
    print("\n=== VideoCapture集成演示 ===")
    
    # 尝试使用摄像头 (如果没有摄像头会失败)
    try:
        # 创建视频采集器 (使用摄像头0)
        capture = VideoCapture(source=0, target_fps=15)
        
        # 创建视频处理器
        processor = VideoProcessor(
            target_format=VideoFormat.BGR,
            target_size=(640, 480),
            quality_threshold=0.3,
            enable_enhancement=True
        )
        
        print("尝试启动摄像头...")
        if capture.start_capture():
            print("摄像头启动成功!")
            
            # 处理几帧进行演示
            frame_count = 0
            max_frames = 5
            
            while frame_count < max_frames:
                frame = capture.get_frame()
                if frame is not None:
                    # 处理帧
                    processed_frame = processor.process_frame(frame)
                    
                    # 分析质量
                    quality_score = processor.check_quality(processed_frame)
                    quality_level = processor.get_quality_level(quality_score)
                    
                    print(f"帧 {frame_count + 1}: "
                          f"{processed_frame.shape[1]}x{processed_frame.shape[0]}, "
                          f"质量: {quality_score:.3f} ({quality_level.value})")
                    
                    frame_count += 1
                else:
                    print("无法获取帧")
                    break
                
                time.sleep(0.1)  # 短暂延迟
            
            # 显示统计信息
            stats = processor.get_processing_stats()
            print(f"\n处理统计: {stats['processed_frames']} 帧, "
                  f"{stats['quality_warnings']} 质量警告")
            
            capture.stop_capture()
            print("摄像头已停止")
        else:
            print("无法启动摄像头，跳过集成演示")
    
    except Exception as e:
        print(f"集成演示失败: {e}")


def create_test_frames():
    """创建测试帧"""
    frames = {}
    
    # 1. 高质量帧 (清晰的棋盘格)
    high_quality = np.zeros((480, 640, 3), dtype=np.uint8)
    square_size = 40
    for i in range(0, 480, square_size):
        for j in range(0, 640, square_size):
            if (i // square_size + j // square_size) % 2 == 0:
                high_quality[i:i+square_size, j:j+square_size] = [255, 255, 255]
    frames["高质量帧"] = high_quality
    
    # 2. 低质量帧 (模糊噪声)
    low_quality = np.random.randint(100, 150, (480, 640, 3), dtype=np.uint8)
    noise = np.random.normal(0, 30, low_quality.shape).astype(np.uint8)
    low_quality = cv2.add(low_quality, noise)
    low_quality = cv2.GaussianBlur(low_quality, (15, 15), 0)
    frames["低质量帧"] = low_quality
    
    # 3. 不同尺寸帧
    different_size = np.random.randint(0, 255, (360, 480, 3), dtype=np.uint8)
    frames["不同尺寸帧"] = different_size
    
    # 4. 高对比度帧
    high_contrast = np.zeros((480, 640, 3), dtype=np.uint8)
    high_contrast[:240, :] = [255, 255, 255]  # 上半部分白色
    high_contrast[240:, :] = [0, 0, 0]        # 下半部分黑色
    frames["高对比度帧"] = high_contrast
    
    return frames


if __name__ == "__main__":
    # 运行所有演示
    demo_video_processing()
    demo_format_conversion()
    demo_resolution_support()
    demo_with_video_capture()
    
    print("\n=== 演示完成 ===")