#!/usr/bin/env python3
"""
厨房安全检测系统演示脚本

展示系统的基本功能和接口。
"""

import sys
import time
from datetime import datetime
from kitchen_safety_system.core import (
    SystemConfig, DetectionStats, AlertRecord, AlertType, AlertLevel
)
from kitchen_safety_system.database import get_db_connection
from kitchen_safety_system.utils import get_logger

logger = get_logger(__name__)


def demo_configuration():
    """演示配置管理功能"""
    print("\n=== 配置管理演示 ===")
    
    # 创建系统配置
    config = SystemConfig()
    print(f"默认配置:")
    print(f"  检测置信度阈值: {config.confidence_threshold}")
    print(f"  视频分辨率: {config.video_resolution}")
    print(f"  检测帧率: {config.detection_fps}")
    
    # 修改配置
    config.confidence_threshold = 0.7
    config.video_fps = 25
    print(f"\n修改后配置:")
    print(f"  检测置信度阈值: {config.confidence_threshold}")
    print(f"  视频帧率: {config.video_fps}")
    
    # 转换为字典
    config_dict = config.to_dict()
    print(f"\n配置字典: {config_dict}")


def demo_data_models():
    """演示数据模型功能"""
    print("\n=== 数据模型演示 ===")
    
    # 创建检测统计
    stats = DetectionStats(
        total_frames_processed=1000,
        total_detections=150,
        person_detections=80,
        stove_detections=30,
        flame_detections=20,
        fall_events=2,
        unattended_stove_events=1,
        average_fps=15.5,
        cpu_usage=65.2,
        memory_usage=45.8,
        last_update_time=datetime.now()
    )
    
    print("检测统计:")
    print(f"  处理帧数: {stats.total_frames_processed}")
    print(f"  总检测数: {stats.total_detections}")
    print(f"  人员检测: {stats.person_detections}")
    print(f"  跌倒事件: {stats.fall_events}")
    print(f"  平均帧率: {stats.average_fps}")
    
    # 创建报警记录
    alert = AlertRecord(
        alert_type=AlertType.FALL_DETECTED.value,
        alert_level=AlertLevel.HIGH.value,
        timestamp=datetime.now(),
        location_x=320,
        location_y=240,
        description="检测到人员跌倒",
        additional_data={"confidence": 0.95, "duration": 2.5}
    )
    
    print(f"\n报警记录:")
    print(f"  类型: {alert.alert_type}")
    print(f"  级别: {alert.alert_level}")
    print(f"  位置: ({alert.location_x}, {alert.location_y})")
    print(f"  描述: {alert.description}")


def demo_database_connection():
    """演示数据库连接功能"""
    print("\n=== 数据库连接演示 ===")
    
    db = get_db_connection()
    
    # 测试PostgreSQL连接
    print("尝试连接PostgreSQL...")
    if db.connect_postgresql():
        print("✓ PostgreSQL连接成功")
    else:
        print("✗ PostgreSQL连接失败 (这是正常的，如果数据库未配置)")
    
    # 测试Redis连接
    print("尝试连接Redis...")
    if db.connect_redis():
        print("✓ Redis连接成功")
        
        # 测试缓存操作
        test_key = "demo_test"
        test_value = {"message": "Hello, Kitchen Safety System!", "timestamp": datetime.now().isoformat()}
        
        if db.cache_set(test_key, test_value, 60):
            print("✓ 缓存设置成功")
            
            cached_value = db.cache_get(test_key)
            if cached_value:
                print(f"✓ 缓存读取成功: {cached_value}")
            
            if db.cache_delete(test_key):
                print("✓ 缓存删除成功")
    else:
        print("✗ Redis连接失败 (这是正常的，如果Redis未配置)")


def demo_logging():
    """演示日志功能"""
    print("\n=== 日志系统演示 ===")
    
    # 获取不同模块的日志记录器
    main_logger = get_logger("main")
    detection_logger = get_logger("detection")
    
    # 记录不同级别的日志
    main_logger.info("系统启动演示")
    main_logger.debug("这是调试信息")
    detection_logger.info("开始目标检测")
    detection_logger.warning("检测置信度较低")
    
    print("日志已记录到控制台和文件")


def demo_system_interfaces():
    """演示系统接口"""
    print("\n=== 系统接口演示 ===")
    
    from kitchen_safety_system.core.interfaces import DetectionType, BoundingBox
    
    # 创建边界框
    bbox = BoundingBox(x=100, y=150, width=200, height=300, confidence=0.85)
    print(f"边界框:")
    print(f"  位置: ({bbox.x}, {bbox.y})")
    print(f"  尺寸: {bbox.width} x {bbox.height}")
    print(f"  中心点: {bbox.center}")
    print(f"  面积: {bbox.area}")
    print(f"  置信度: {bbox.confidence}")
    
    # 检测类型
    print(f"\n检测类型:")
    for detection_type in DetectionType:
        print(f"  {detection_type.name}: {detection_type.value}")


def main():
    """主演示函数"""
    print("厨房安全检测系统演示")
    print("=" * 50)
    
    try:
        demo_configuration()
        demo_data_models()
        demo_system_interfaces()
        demo_logging()
        demo_database_connection()
        
        print("\n=== 演示完成 ===")
        print("系统核心组件已成功初始化！")
        print("\n下一步:")
        print("1. 配置PostgreSQL和Redis数据库")
        print("2. 实现视频采集和处理模块")
        print("3. 集成YOLO目标检测")
        print("4. 实现MediaPipe姿态分析")
        print("5. 开发Django Web管理界面")
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        print(f"\n错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())