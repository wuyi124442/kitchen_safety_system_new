"""
事件日志记录系统演示

演示如何使用增强的事件日志记录功能，包括详细事件记录和视频片段保存。
满足需求 5.3 和 5.5 的演示。
"""

import time
import numpy as np
from typing import Dict, Any, List
from datetime import datetime

from ..core.interfaces import AlertEvent, AlertType, AlertLevel
from ..core.models import SystemConfig
from .alert_manager import AlertManager
from .event_logger import EventLogger
from ..utils.logger import get_logger


def create_demo_detection_data() -> Dict[str, Any]:
    """创建演示检测数据"""
    return {
        'detections': [
            {
                'type': 'person',
                'confidence': 0.92,
                'bbox': [150, 100, 200, 400],
                'center': [250, 300]
            },
            {
                'type': 'stove',
                'confidence': 0.88,
                'bbox': [400, 200, 150, 100],
                'center': [475, 250]
            }
        ],
        'pose_data': {
            'keypoints': [
                {'name': 'head', 'x': 250, 'y': 120, 'confidence': 0.95},
                {'name': 'shoulder_left', 'x': 230, 'y': 180, 'confidence': 0.90},
                {'name': 'shoulder_right', 'x': 270, 'y': 180, 'confidence': 0.90},
                {'name': 'hip_left', 'x': 240, 'y': 350, 'confidence': 0.85},
                {'name': 'hip_right', 'x': 260, 'y': 350, 'confidence': 0.85}
            ],
            'fall_probability': 0.95,
            'pose_confidence': 0.88
        },
        'frame_info': {
            'frame_id': 12345,
            'timestamp': time.time(),
            'resolution': [640, 480],
            'fps': 15.2
        }
    }


def create_demo_system_state() -> Dict[str, Any]:
    """创建演示系统状态"""
    return {
        'system_status': 'running',
        'cpu_usage': 45.2,
        'memory_usage': 62.8,
        'gpu_usage': 78.5,
        'fps': 15.2,
        'detection_latency': 0.045,
        'active_cameras': 1,
        'storage_usage': 35.6,
        'network_status': 'connected',
        'last_maintenance': '2024-01-15T10:30:00',
        'uptime_hours': 72.5,
        'error_count_24h': 0,
        'alert_count_24h': 3
    }


def create_demo_video_frames(count: int = 30) -> List[np.ndarray]:
    """创建演示视频帧"""
    frames = []
    for i in range(count):
        # 创建随机视频帧（模拟真实视频）
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 添加一些模拟内容（简单的矩形表示检测对象）
        # 人员区域
        frame[100:400, 150:350] = [100, 150, 200]  # 蓝色区域表示人员
        
        # 灶台区域
        frame[200:300, 400:550] = [200, 100, 50]   # 橙色区域表示灶台
        
        # 添加帧编号
        frame[10:30, 10:100] = [255, 255, 255]     # 白色背景
        
        frames.append(frame)
    
    return frames


def demo_fall_detection_event():
    """演示跌倒检测事件记录"""
    logger = get_logger(__name__)
    logger.info("=== 跌倒检测事件记录演示 ===")
    
    # 创建报警管理器
    config = SystemConfig()
    alert_manager = AlertManager(config)
    
    # 创建跌倒检测报警事件
    fall_alert = AlertEvent(
        alert_type=AlertType.FALL_DETECTED,
        alert_level=AlertLevel.HIGH,
        timestamp=time.time(),
        location=(250, 300),
        description="检测到人员跌倒，位置：厨房中央区域",
        additional_data={
            'confidence': 0.95,
            'detection_method': 'pose_analysis',
            'camera_id': 'kitchen_cam_01'
        }
    )
    
    # 准备检测数据
    detection_data = create_demo_detection_data()
    system_state = create_demo_system_state()
    
    # 模拟视频帧缓存
    video_frames = create_demo_video_frames(20)
    for frame in video_frames:
        alert_manager.update_video_buffer(frame)
    
    # 触发报警（包含详细事件记录和视频保存）
    success = alert_manager.trigger_alert(
        alert_event=fall_alert,
        detection_data=detection_data,
        system_state=system_state
    )
    
    logger.info(f"跌倒检测报警处理结果: {success}")
    
    # 获取事件统计
    stats = alert_manager.get_event_statistics()
    logger.info(f"事件统计: {stats}")
    
    # 获取最近事件
    recent_events = alert_manager.get_recent_events_detailed(5)
    logger.info(f"最近事件数量: {len(recent_events)}")
    
    return alert_manager


def demo_unattended_stove_event():
    """演示无人看管灶台事件记录"""
    logger = get_logger(__name__)
    logger.info("=== 无人看管灶台事件记录演示 ===")
    
    # 创建报警管理器
    config = SystemConfig()
    alert_manager = AlertManager(config)
    
    # 创建无人看管报警事件
    stove_alert = AlertEvent(
        alert_type=AlertType.UNATTENDED_STOVE,
        alert_level=AlertLevel.MEDIUM,
        timestamp=time.time(),
        location=(475, 250),
        description="检测到灶台无人看管超过5分钟",
        additional_data={
            'unattended_duration': 300,  # 5分钟
            'flame_detected': True,
            'last_person_seen': time.time() - 300,
            'stove_id': 'stove_02'
        }
    )
    
    # 准备检测数据
    detection_data = {
        'detections': [
            {
                'type': 'stove',
                'confidence': 0.88,
                'bbox': [400, 200, 150, 100],
                'center': [475, 250]
            },
            {
                'type': 'flame',
                'confidence': 0.92,
                'bbox': [460, 220, 30, 40],
                'center': [475, 240]
            }
        ],
        'risk_assessment': {
            'risk_level': 'medium',
            'distance_to_nearest_person': 5.2,  # 米
            'unattended_time': 300,
            'flame_intensity': 0.75
        },
        'frame_info': {
            'frame_id': 12346,
            'timestamp': time.time(),
            'resolution': [640, 480]
        }
    }
    
    system_state = create_demo_system_state()
    
    # 模拟视频帧缓存
    video_frames = create_demo_video_frames(15)
    for frame in video_frames:
        alert_manager.update_video_buffer(frame)
    
    # 触发报警
    success = alert_manager.trigger_alert(
        alert_event=stove_alert,
        detection_data=detection_data,
        system_state=system_state
    )
    
    logger.info(f"无人看管灶台报警处理结果: {success}")
    
    return alert_manager


def demo_system_error_event():
    """演示系统错误事件记录"""
    logger = get_logger(__name__)
    logger.info("=== 系统错误事件记录演示 ===")
    
    # 创建报警管理器
    config = SystemConfig()
    alert_manager = AlertManager(config)
    
    # 创建系统错误报警事件
    error_alert = AlertEvent(
        alert_type=AlertType.SYSTEM_ERROR,
        alert_level=AlertLevel.CRITICAL,
        timestamp=time.time(),
        location=None,
        description="摄像头连接中断，检测功能暂停",
        additional_data={
            'error_code': 'CAM_DISCONNECT',
            'error_message': 'Camera connection lost',
            'affected_cameras': ['kitchen_cam_01'],
            'retry_attempts': 3,
            'last_successful_frame': time.time() - 30
        }
    )
    
    # 准备系统状态数据
    system_state = {
        'system_status': 'error',
        'cpu_usage': 25.1,
        'memory_usage': 45.2,
        'active_cameras': 0,  # 摄像头断开
        'error_count_24h': 1,
        'last_error_time': time.time(),
        'recovery_attempts': 3,
        'network_status': 'connected'
    }
    
    # 记录事件（系统错误通常没有视频帧）
    success = alert_manager.record_event(
        alert_event=error_alert,
        system_state=system_state
    )
    
    logger.info(f"系统错误事件记录结果: {success}")
    
    return alert_manager


def demo_event_query_and_export():
    """演示事件查询和导出功能"""
    logger = get_logger(__name__)
    logger.info("=== 事件查询和导出演示 ===")
    
    # 创建事件日志记录器
    event_logger = EventLogger()
    
    # 查询最近1小时的事件
    end_time = time.time()
    start_time = end_time - 3600  # 1小时前
    
    logs = event_logger.query_logs(start_time, end_time)
    logger.info(f"查询到 {len(logs)} 条日志记录")
    
    # 导出事件日志
    export_path = event_logger.export_logs(start_time, end_time, "json")
    if export_path:
        logger.info(f"事件日志已导出到: {export_path}")
    else:
        logger.warning("事件日志导出失败")
    
    # 获取统计信息
    stats = event_logger.get_event_statistics()
    logger.info(f"事件统计信息: {stats}")
    
    return event_logger


def demo_comprehensive_event_logging():
    """综合事件日志记录演示"""
    logger = get_logger(__name__)
    logger.info("=== 综合事件日志记录系统演示 ===")
    
    try:
        # 1. 跌倒检测事件
        logger.info("1. 演示跌倒检测事件记录...")
        fall_manager = demo_fall_detection_event()
        time.sleep(1)
        
        # 2. 无人看管灶台事件
        logger.info("2. 演示无人看管灶台事件记录...")
        stove_manager = demo_unattended_stove_event()
        time.sleep(1)
        
        # 3. 系统错误事件
        logger.info("3. 演示系统错误事件记录...")
        error_manager = demo_system_error_event()
        time.sleep(1)
        
        # 4. 事件查询和导出
        logger.info("4. 演示事件查询和导出...")
        event_logger = demo_event_query_and_export()
        
        # 5. 综合统计
        logger.info("5. 获取综合统计信息...")
        
        # 合并所有管理器的统计
        all_stats = {
            'fall_detection': fall_manager.get_event_statistics(),
            'stove_monitoring': stove_manager.get_event_statistics(),
            'system_errors': error_manager.get_event_statistics(),
            'event_logger': event_logger.get_event_statistics()
        }
        
        logger.info("=== 综合统计信息 ===")
        for category, stats in all_stats.items():
            logger.info(f"{category}: {stats}")
        
        logger.info("=== 事件日志记录系统演示完成 ===")
        
        return {
            'fall_manager': fall_manager,
            'stove_manager': stove_manager,
            'error_manager': error_manager,
            'event_logger': event_logger,
            'statistics': all_stats
        }
        
    except Exception as e:
        logger.error(f"演示过程中发生错误: {e}")
        raise


if __name__ == "__main__":
    # 运行综合演示
    demo_results = demo_comprehensive_event_logging()
    
    print("\n" + "="*50)
    print("事件日志记录系统演示完成")
    print("="*50)
    
    # 显示最终统计
    stats = demo_results['statistics']
    print(f"总事件数: {sum(s.get('event_stats', {}).get('total_events', 0) for s in stats.values())}")
    print(f"带视频事件数: {sum(s.get('event_stats', {}).get('events_with_video', 0) for s in stats.values())}")
    print("演示数据已保存到 logs/ 目录")