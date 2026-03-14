"""
检测结果后处理演示

演示检测结果后处理器的功能，包括边界框过滤、NMS、置信度调整等。
"""

import cv2
import numpy as np
import time
from typing import List

from .yolo_detector import YOLODetector
from .detection_post_processor import DetectionPostProcessor
from ..core.interfaces import DetectionResult, DetectionType, BoundingBox
from ..utils.logger import get_logger


def create_demo_detections() -> List[DetectionResult]:
    """创建演示用的检测结果"""
    current_time = time.time()
    
    detections = [
        # 高置信度人员检测
        DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=100, y=100, width=80, height=160, confidence=0.95),
            timestamp=current_time,
            frame_id=1
        ),
        # 重叠的人员检测（应该被NMS过滤）
        DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=110, y=110, width=70, height=150, confidence=0.85),
            timestamp=current_time,
            frame_id=1
        ),
        # 低置信度人员检测（应该被置信度过滤）
        DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=300, y=200, width=60, height=120, confidence=0.3),
            timestamp=current_time,
            frame_id=1
        ),
        # 火焰检测
        DetectionResult(
            detection_type=DetectionType.FLAME,
            bbox=BoundingBox(x=400, y=150, width=40, height=40, confidence=0.92),
            timestamp=current_time,
            frame_id=1
        ),
        # 小尺寸灶台检测（应该被尺寸过滤）
        DetectionResult(
            detection_type=DetectionType.STOVE,
            bbox=BoundingBox(x=500, y=300, width=15, height=15, confidence=0.8),
            timestamp=current_time,
            frame_id=1
        ),
        # 正常灶台检测
        DetectionResult(
            detection_type=DetectionType.STOVE,
            bbox=BoundingBox(x=200, y=350, width=100, height=60, confidence=0.75),
            timestamp=current_time,
            frame_id=1
        ),
    ]
    
    return detections


def visualize_detections_comparison(frame: np.ndarray, 
                                  original_detections: List[DetectionResult],
                                  processed_detections: List[DetectionResult]) -> np.ndarray:
    """
    可视化原始检测结果和后处理结果的对比
    
    Args:
        frame: 原始图像帧
        original_detections: 原始检测结果
        processed_detections: 后处理检测结果
        
    Returns:
        np.ndarray: 对比可视化图像
    """
    # 创建并排对比图像
    height, width = frame.shape[:2]
    comparison_frame = np.zeros((height, width * 2, 3), dtype=np.uint8)
    
    # 左侧显示原始结果
    left_frame = frame.copy()
    for detection in original_detections:
        bbox = detection.bbox
        color = (0, 0, 255)  # 红色表示原始检测
        
        cv2.rectangle(
            left_frame,
            (bbox.x, bbox.y),
            (bbox.x + bbox.width, bbox.y + bbox.height),
            color,
            2
        )
        
        # 添加标签
        label = f"{detection.detection_type.value}: {bbox.confidence:.2f}"
        cv2.putText(
            left_frame,
            label,
            (bbox.x, bbox.y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1
        )
    
    # 右侧显示后处理结果
    right_frame = frame.copy()
    for detection in processed_detections:
        bbox = detection.bbox
        color = (0, 255, 0)  # 绿色表示后处理结果
        
        cv2.rectangle(
            right_frame,
            (bbox.x, bbox.y),
            (bbox.x + bbox.width, bbox.y + bbox.height),
            color,
            2
        )
        
        # 添加标签
        label = f"{detection.detection_type.value}: {bbox.confidence:.2f}"
        cv2.putText(
            right_frame,
            label,
            (bbox.x, bbox.y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            1
        )
    
    # 组合图像
    comparison_frame[:, :width] = left_frame
    comparison_frame[:, width:] = right_frame
    
    # 添加标题
    cv2.putText(
        comparison_frame,
        "Original Detections",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )
    
    cv2.putText(
        comparison_frame,
        "Post-processed Detections",
        (width + 10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2
    )
    
    return comparison_frame


def demo_post_processing_features():
    """演示后处理功能"""
    logger = get_logger(__name__)
    logger.info("开始演示检测结果后处理功能")
    
    # 创建演示图像
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    
    # 添加一些背景内容
    cv2.rectangle(frame, (50, 50), (590, 430), (50, 50, 50), -1)
    cv2.putText(frame, "Kitchen Safety Detection Demo", (150, 250), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    # 创建演示检测结果
    original_detections = create_demo_detections()
    
    print(f"\n=== 检测结果后处理演示 ===")
    print(f"原始检测结果数量: {len(original_detections)}")
    
    # 创建后处理器
    post_processor = DetectionPostProcessor(
        confidence_threshold=0.5,
        nms_threshold=0.45,
        min_box_size=20,
        max_detections=50
    )
    
    # 演示不同的后处理步骤
    print(f"\n1. 置信度过滤 (阈值: {post_processor.confidence_threshold})")
    confidence_filtered = post_processor._filter_by_confidence(original_detections)
    print(f"   过滤后数量: {len(confidence_filtered)}")
    
    print(f"\n2. 尺寸过滤 (最小尺寸: {post_processor.min_box_size})")
    size_filtered = post_processor._filter_by_size(confidence_filtered)
    print(f"   过滤后数量: {len(size_filtered)}")
    
    print(f"\n3. 非极大值抑制 (IoU阈值: {post_processor.nms_threshold})")
    nms_filtered = post_processor._apply_nms(size_filtered)
    print(f"   过滤后数量: {len(nms_filtered)}")
    
    # 完整后处理流程
    print(f"\n4. 完整后处理流程")
    processed_detections = post_processor.process_detections(
        original_detections, 
        frame_shape=(frame.shape[0], frame.shape[1])
    )
    print(f"   最终检测数量: {len(processed_detections)}")
    
    # 显示性能统计
    stats = post_processor.get_performance_stats()
    print(f"\n=== 性能统计 ===")
    print(f"处理次数: {stats['processing_count']}")
    print(f"平均处理时间: {stats['average_processing_time']:.4f}s")
    
    # 创建对比可视化
    comparison_image = visualize_detections_comparison(
        frame, original_detections, processed_detections
    )
    
    # 保存结果图像
    output_path = "post_processing_demo_result.jpg"
    cv2.imwrite(output_path, comparison_image)
    print(f"\n对比结果已保存到: {output_path}")
    
    return processed_detections, stats


def demo_threshold_adjustment():
    """演示阈值调整功能"""
    logger = get_logger(__name__)
    logger.info("演示阈值调整功能")
    
    post_processor = DetectionPostProcessor()
    detections = create_demo_detections()
    
    print(f"\n=== 阈值调整演示 ===")
    
    # 测试不同的置信度阈值
    thresholds = [0.3, 0.5, 0.7, 0.9]
    
    for threshold in thresholds:
        post_processor.set_confidence_threshold(threshold)
        filtered = post_processor._filter_by_confidence(detections)
        print(f"置信度阈值 {threshold}: {len(filtered)} 个检测结果")
    
    # 测试类别特定阈值
    print(f"\n类别特定阈值设置:")
    post_processor.set_confidence_threshold(0.8, DetectionType.FLAME)
    post_processor.set_confidence_threshold(0.6, DetectionType.PERSON)
    post_processor.set_confidence_threshold(0.7, DetectionType.STOVE)
    
    filtered = post_processor._filter_by_confidence(detections)
    print(f"使用类别特定阈值: {len(filtered)} 个检测结果")
    
    # 显示每个类别的阈值
    for detection_type, threshold in post_processor.class_thresholds.items():
        print(f"  {detection_type.value}: {threshold}")


def demo_optimization_modes():
    """演示优化模式"""
    logger = get_logger(__name__)
    logger.info("演示优化模式")
    
    detections = create_demo_detections()
    
    print(f"\n=== 优化模式演示 ===")
    
    # 实时优化模式
    print(f"\n1. 实时优化模式")
    realtime_processor = DetectionPostProcessor()
    realtime_processor.optimize_for_realtime()
    
    start_time = time.time()
    realtime_result = realtime_processor.process_detections(detections)
    realtime_time = time.time() - start_time
    
    print(f"   处理时间: {realtime_time:.4f}s")
    print(f"   检测数量: {len(realtime_result)}")
    print(f"   最大检测数: {realtime_processor.max_detections}")
    print(f"   NMS阈值: {realtime_processor.nms_threshold}")
    
    # 精度优化模式
    print(f"\n2. 精度优化模式")
    accuracy_processor = DetectionPostProcessor()
    accuracy_processor.optimize_for_accuracy()
    
    start_time = time.time()
    accuracy_result = accuracy_processor.process_detections(detections)
    accuracy_time = time.time() - start_time
    
    print(f"   处理时间: {accuracy_time:.4f}s")
    print(f"   检测数量: {len(accuracy_result)}")
    print(f"   最大检测数: {accuracy_processor.max_detections}")
    print(f"   NMS阈值: {accuracy_processor.nms_threshold}")


def demo_yolo_integration():
    """演示与YOLO检测器的集成"""
    logger = get_logger(__name__)
    logger.info("演示与YOLO检测器的集成")
    
    print(f"\n=== YOLO检测器集成演示 ===")
    
    try:
        # 创建带后处理的YOLO检测器
        detector_with_pp = YOLODetector(enable_post_processing=True)
        print(f"✓ 已创建带后处理的YOLO检测器")
        
        # 创建不带后处理的YOLO检测器
        detector_without_pp = YOLODetector(enable_post_processing=False)
        print(f"✓ 已创建不带后处理的YOLO检测器")
        
        # 测试阈值设置
        detector_with_pp.set_confidence_threshold(0.7)
        detector_with_pp.set_class_confidence_threshold(DetectionType.FLAME, 0.9)
        print(f"✓ 已设置检测阈值")
        
        # 测试优化模式
        detector_with_pp.optimize_for_realtime()
        print(f"✓ 已优化为实时模式")
        
        # 显示性能统计
        stats = detector_with_pp.get_performance_stats()
        print(f"✓ 后处理状态: {stats.get('post_processing_enabled', False)}")
        
        if 'post_processor_stats' in stats:
            pp_stats = stats['post_processor_stats']
            print(f"✓ 后处理器配置:")
            print(f"   - 置信度阈值: {pp_stats.get('confidence_threshold', 'N/A')}")
            print(f"   - NMS阈值: {pp_stats.get('nms_threshold', 'N/A')}")
            print(f"   - 最小框尺寸: {pp_stats.get('min_box_size', 'N/A')}")
        
    except Exception as e:
        logger.error(f"YOLO集成演示失败: {e}")
        print(f"✗ YOLO集成演示失败: {e}")


def main():
    """主演示函数"""
    print("厨房安全检测系统 - 检测结果后处理演示")
    print("=" * 50)
    
    try:
        # 1. 基本后处理功能演示
        demo_post_processing_features()
        
        # 2. 阈值调整演示
        demo_threshold_adjustment()
        
        # 3. 优化模式演示
        demo_optimization_modes()
        
        # 4. YOLO集成演示
        demo_yolo_integration()
        
        print(f"\n✓ 所有演示完成！")
        
    except Exception as e:
        print(f"\n✗ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()