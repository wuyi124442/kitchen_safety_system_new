"""
灶台监控器演示模块

演示StoveMonitor的使用方法和功能。
"""

import time
import numpy as np
from typing import List

from ..core.interfaces import DetectionResult, DetectionType, BoundingBox
from .stove_monitor import StoveMonitor
from ..utils.logger import get_logger


def create_demo_detection(detection_type: DetectionType, 
                         x: int, y: int, 
                         width: int = 50, height: int = 50,
                         confidence: float = 0.8) -> DetectionResult:
    """创建演示用的检测结果"""
    bbox = BoundingBox(x=x, y=y, width=width, height=height, confidence=confidence)
    return DetectionResult(
        detection_type=detection_type,
        bbox=bbox,
        timestamp=time.time(),
        frame_id=1
    )


def demo_basic_monitoring():
    """演示基本监控功能"""
    logger = get_logger(__name__)
    logger.info("=== 灶台监控器基本功能演示 ===")
    
    # 创建监控器
    monitor = StoveMonitor(
        distance_threshold=2.0,
        unattended_time_threshold=5,  # 5秒用于演示
        alert_cooldown_time=3
    )
    
    # 场景1: 有人在灶台附近
    logger.info("\n场景1: 有人在灶台附近")
    stove = create_demo_detection(DetectionType.STOVE, 100, 100)
    flame = create_demo_detection(DetectionType.FLAME, 110, 110)
    person = create_demo_detection(DetectionType.PERSON, 150, 150)
    
    detections = [stove, flame, person]
    alert = monitor.monitor_stove_safety(detections)
    
    status = monitor.get_monitoring_status()
    logger.info(f"监控状态: {status}")
    logger.info(f"警报: {alert}")
    
    # 场景2: 人员离开，开始无人看管
    logger.info("\n场景2: 人员离开，开始无人看管")
    detections_no_person = [stove, flame]
    
    for i in range(3):
        alert = monitor.monitor_stove_safety(detections_no_person)
        status = monitor.get_monitoring_status()
        
        unattended_stove = next((s for s in status['stove_details'] if s['is_unattended']), None)
        if unattended_stove:
            logger.info(f"第{i+1}次检查 - 无人看管时间: {unattended_stove['unattended_duration']:.1f}秒")
        
        if alert:
            logger.warning(f"触发警报: {alert.description}")
            break
        
        time.sleep(2)
    
    # 场景3: 人员返回
    logger.info("\n场景3: 人员返回")
    detections_with_person = [stove, flame, person]
    alert = monitor.monitor_stove_safety(detections_with_person)
    
    status = monitor.get_monitoring_status()
    logger.info(f"人员返回后状态: {status}")


def demo_distance_calculation():
    """演示距离计算功能"""
    logger = get_logger(__name__)
    logger.info("\n=== 距离计算演示 ===")
    
    monitor = StoveMonitor()
    
    # 测试不同距离的人员
    stove = create_demo_detection(DetectionType.STOVE, 200, 200)
    
    test_positions = [
        (220, 220, "很近"),
        (250, 250, "中等距离"),
        (350, 350, "较远"),
        (500, 500, "很远")
    ]
    
    for x, y, description in test_positions:
        person = create_demo_detection(DetectionType.PERSON, x, y)
        detections = [stove, person]
        
        monitor.update_monitoring_state(detections)
        status = monitor.get_monitoring_status()
        
        if status['stove_details']:
            distance = status['stove_details'][0]['nearest_person_distance']
            logger.info(f"{description}位置 ({x}, {y}): 距离 = {distance:.2f}米")


def demo_multiple_stoves():
    """演示多灶台监控"""
    logger = get_logger(__name__)
    logger.info("\n=== 多灶台监控演示 ===")
    
    monitor = StoveMonitor(
        distance_threshold=2.0,
        unattended_time_threshold=3
    )
    
    # 创建多个灶台
    stove1 = create_demo_detection(DetectionType.STOVE, 100, 100)
    flame1 = create_demo_detection(DetectionType.FLAME, 110, 110)
    
    stove2 = create_demo_detection(DetectionType.STOVE, 300, 300)
    flame2 = create_demo_detection(DetectionType.FLAME, 310, 310)
    
    stove3 = create_demo_detection(DetectionType.STOVE, 500, 100)
    # stove3 没有火焰
    
    # 只有一个人员，靠近stove1
    person = create_demo_detection(DetectionType.PERSON, 150, 150)
    
    detections = [stove1, flame1, stove2, flame2, stove3, person]
    
    monitor.update_monitoring_state(detections)
    status = monitor.get_monitoring_status()
    
    logger.info(f"总灶台数: {status['total_stoves']}")
    logger.info(f"有火焰灶台数: {status['stoves_with_flame']}")
    logger.info(f"无人看管灶台数: {status['unattended_stoves']}")
    
    for detail in status['stove_details']:
        logger.info(f"灶台 {detail['stove_id']}: "
                   f"有火焰={detail['has_flame']}, "
                   f"无人看管={detail['is_unattended']}, "
                   f"最近距离={detail['nearest_person_distance']}")


def demo_configuration_adjustment():
    """演示配置调整功能"""
    logger = get_logger(__name__)
    logger.info("\n=== 配置调整演示 ===")
    
    monitor = StoveMonitor()
    
    # 显示初始配置
    logger.info(f"初始距离阈值: {monitor.distance_threshold}米")
    logger.info(f"初始时间阈值: {monitor.unattended_time_threshold}秒")
    logger.info(f"初始像素转换比例: {monitor.pixels_per_meter} 像素/米")
    
    # 调整配置
    monitor.set_distance_threshold(3.0)
    monitor.set_unattended_time_threshold(600)
    monitor.set_pixels_per_meter(150.0)
    
    logger.info(f"调整后距离阈值: {monitor.distance_threshold}米")
    logger.info(f"调整后时间阈值: {monitor.unattended_time_threshold}秒")
    logger.info(f"调整后像素转换比例: {monitor.pixels_per_meter} 像素/米")


def main():
    """主演示函数"""
    logger = get_logger(__name__)
    logger.info("开始灶台监控器演示")
    
    try:
        demo_basic_monitoring()
        demo_distance_calculation()
        demo_multiple_stoves()
        demo_configuration_adjustment()
        
        logger.info("\n=== 演示完成 ===")
        
    except Exception as e:
        logger.error(f"演示过程中出错: {e}")


if __name__ == "__main__":
    main()