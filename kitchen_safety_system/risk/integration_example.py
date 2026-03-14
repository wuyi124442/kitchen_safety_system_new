"""
风险评估模块集成示例

展示如何将风险评估模块与其他系统组件集成使用。
"""

import time
import numpy as np
from typing import List, Dict, Any

from .risk_assessment import RiskAssessment, RiskLevel
from .stove_monitor import StoveMonitor
from ..detection.yolo_detector import YOLODetector
from ..pose.pose_analyzer import PoseAnalyzer
from ..core.interfaces import DetectionResult, PoseResult
from ..core.models import SystemConfig
from ..utils.logger import get_logger


class IntegratedKitchenSafetySystem:
    """
    集成厨房安全系统
    
    整合YOLO检测、姿态分析、灶台监控和风险评估功能。
    """
    
    def __init__(self, config: SystemConfig = None):
        """
        初始化集成系统
        
        Args:
            config: 系统配置
        """
        self.logger = get_logger(__name__)
        self.config = config or SystemConfig()
        
        # 初始化各个组件
        try:
            # 注意：在实际使用中需要确保模型文件存在
            # self.yolo_detector = YOLODetector()
            # self.pose_analyzer = PoseAnalyzer()
            self.stove_monitor = StoveMonitor(
                distance_threshold=self.config.stove_distance_threshold,
                unattended_time_threshold=self.config.unattended_time_threshold
            )
            self.risk_assessment = RiskAssessment(self.config)
            
            self.logger.info("集成厨房安全系统初始化完成")
            
        except Exception as e:
            self.logger.error(f"系统初始化失败: {e}")
            raise
    
    def process_frame(self, frame: np.ndarray, frame_id: int = 0) -> Dict[str, Any]:
        """
        处理单帧图像，执行完整的安全检测流程
        
        Args:
            frame: 输入图像帧
            frame_id: 帧ID
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 1. 目标检测（模拟结果，实际使用时调用YOLO检测器）
            detections = self._simulate_yolo_detection(frame, frame_id)
            
            # 2. 姿态分析（模拟结果，实际使用时调用姿态分析器）
            pose_results = self._simulate_pose_analysis(frame, detections, frame_id)
            
            # 3. 灶台监控
            stove_alert = self.stove_monitor.monitor_stove_safety(detections)
            stove_status = self.stove_monitor.get_monitoring_status()
            
            # 4. 综合风险评估
            risk_result = self.risk_assessment.assess_risk(
                detections=detections,
                pose_results=pose_results,
                stove_monitor_status=stove_status,
                frame_id=frame_id
            )
            
            # 5. 整合结果
            result = {
                'frame_id': frame_id,
                'timestamp': time.time(),
                'detections': detections,
                'pose_results': pose_results,
                'stove_alert': stove_alert,
                'stove_status': stove_status,
                'risk_assessment': risk_result,
                'system_status': self._get_system_status()
            }
            
            # 6. 记录重要事件
            self._log_important_events(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"帧处理失败 (frame_id: {frame_id}): {e}")
            return {
                'frame_id': frame_id,
                'timestamp': time.time(),
                'error': str(e),
                'system_status': 'error'
            }
    
    def _simulate_yolo_detection(self, frame: np.ndarray, frame_id: int) -> List[DetectionResult]:
        """
        模拟YOLO检测结果
        
        Args:
            frame: 输入图像
            frame_id: 帧ID
            
        Returns:
            List[DetectionResult]: 模拟的检测结果
        """
        from ..core.interfaces import DetectionType, BoundingBox
        
        # 模拟检测结果（实际使用时替换为真实的YOLO检测）
        current_time = time.time()
        
        # 根据帧ID模拟不同场景
        if frame_id % 10 < 3:
            # 安全场景：人员在灶台附近
            return [
                DetectionResult(
                    detection_type=DetectionType.PERSON,
                    bbox=BoundingBox(x=200, y=150, width=80, height=160, confidence=0.92),
                    timestamp=current_time,
                    frame_id=frame_id
                ),
                DetectionResult(
                    detection_type=DetectionType.STOVE,
                    bbox=BoundingBox(x=300, y=200, width=100, height=60, confidence=0.88),
                    timestamp=current_time,
                    frame_id=frame_id
                ),
                DetectionResult(
                    detection_type=DetectionType.FLAME,
                    bbox=BoundingBox(x=320, y=180, width=30, height=40, confidence=0.85),
                    timestamp=current_time,
                    frame_id=frame_id
                )
            ]
        elif frame_id % 10 < 6:
            # 无人看管场景
            return [
                DetectionResult(
                    detection_type=DetectionType.PERSON,
                    bbox=BoundingBox(x=50, y=150, width=80, height=160, confidence=0.90),
                    timestamp=current_time,
                    frame_id=frame_id
                ),
                DetectionResult(
                    detection_type=DetectionType.STOVE,
                    bbox=BoundingBox(x=400, y=200, width=100, height=60, confidence=0.87),
                    timestamp=current_time,
                    frame_id=frame_id
                ),
                DetectionResult(
                    detection_type=DetectionType.FLAME,
                    bbox=BoundingBox(x=420, y=180, width=35, height=45, confidence=0.82),
                    timestamp=current_time,
                    frame_id=frame_id
                )
            ]
        elif frame_id % 10 < 8:
            # 跌倒场景
            return [
                DetectionResult(
                    detection_type=DetectionType.PERSON,
                    bbox=BoundingBox(x=150, y=250, width=120, height=80, confidence=0.88),
                    timestamp=current_time,
                    frame_id=frame_id
                )
            ]
        else:
            # 无检测场景
            return []
    
    def _simulate_pose_analysis(self, frame: np.ndarray, 
                               detections: List[DetectionResult], 
                               frame_id: int) -> List[PoseResult]:
        """
        模拟姿态分析结果
        
        Args:
            frame: 输入图像
            detections: 检测结果
            frame_id: 帧ID
            
        Returns:
            List[PoseResult]: 模拟的姿态分析结果
        """
        from ..core.interfaces import PoseKeypoint
        
        pose_results = []
        current_time = time.time()
        
        # 为每个检测到的人员生成姿态结果
        person_detections = [d for d in detections if d.detection_type.value == "person"]
        
        for person in person_detections:
            # 根据边界框判断是否为跌倒（简化逻辑）
            is_fall = person.bbox.width > person.bbox.height * 1.2
            
            if is_fall:
                # 跌倒姿态
                pose_result = PoseResult(
                    keypoints=[
                        PoseKeypoint(x=200, y=280, confidence=0.90, visible=True),
                        PoseKeypoint(x=180, y=285, confidence=0.85, visible=True),
                        PoseKeypoint(x=160, y=290, confidence=0.80, visible=True),
                        PoseKeypoint(x=140, y=295, confidence=0.75, visible=True),
                        PoseKeypoint(x=120, y=300, confidence=0.70, visible=True),
                        PoseKeypoint(x=100, y=305, confidence=0.65, visible=True),
                    ],
                    timestamp=current_time,
                    frame_id=frame_id,
                    is_fall_detected=True,
                    fall_confidence=0.92
                )
            else:
                # 正常姿态
                pose_result = PoseResult(
                    keypoints=[
                        PoseKeypoint(x=240, y=170, confidence=0.95, visible=True),
                        PoseKeypoint(x=240, y=200, confidence=0.90, visible=True),
                        PoseKeypoint(x=240, y=230, confidence=0.88, visible=True),
                        PoseKeypoint(x=240, y=260, confidence=0.85, visible=True),
                        PoseKeypoint(x=240, y=290, confidence=0.82, visible=True),
                        PoseKeypoint(x=240, y=320, confidence=0.80, visible=True),
                    ],
                    timestamp=current_time,
                    frame_id=frame_id,
                    is_fall_detected=False,
                    fall_confidence=0.05
                )
            
            pose_results.append(pose_result)
        
        return pose_results
    
    def _get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态信息
        
        Returns:
            Dict[str, Any]: 系统状态
        """
        return {
            'stove_monitor_active': True,
            'risk_assessment_active': True,
            'total_risk_assessments': len(self.risk_assessment.risk_history),
            'last_assessment_time': time.time()
        }
    
    def _log_important_events(self, result: Dict[str, Any]) -> None:
        """
        记录重要事件
        
        Args:
            result: 处理结果
        """
        risk_result = result.get('risk_assessment')
        if not risk_result:
            return
        
        # 记录高风险事件
        if risk_result.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self.logger.warning(
                f"检测到{risk_result.risk_level.value}风险 "
                f"(分数: {risk_result.overall_risk_score:.1f}, "
                f"帧ID: {result['frame_id']})"
            )
        
        # 记录警报事件
        for alert in risk_result.alert_events:
            self.logger.warning(
                f"触发警报: {alert.alert_type.value} - {alert.description}"
            )
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """
        获取系统统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'stove_monitor_status': self.stove_monitor.get_monitoring_status(),
            'risk_statistics': self.risk_assessment.get_risk_statistics(),
            'system_config': self.config.to_dict()
        }
    
    def update_configuration(self, new_config: Dict[str, Any]) -> bool:
        """
        更新系统配置
        
        Args:
            new_config: 新配置参数
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 更新灶台监控配置
            if 'stove_distance_threshold' in new_config:
                self.stove_monitor.set_distance_threshold(
                    new_config['stove_distance_threshold']
                )
            
            if 'unattended_time_threshold' in new_config:
                self.stove_monitor.set_unattended_time_threshold(
                    new_config['unattended_time_threshold']
                )
            
            # 更新风险评估配置
            if 'risk_thresholds' in new_config:
                self.risk_assessment.update_risk_thresholds(
                    new_config['risk_thresholds']
                )
            
            if 'risk_weights' in new_config:
                self.risk_assessment.update_risk_weights(
                    new_config['risk_weights']
                )
            
            self.logger.info("系统配置更新成功")
            return True
            
        except Exception as e:
            self.logger.error(f"配置更新失败: {e}")
            return False


def demo_integrated_system():
    """演示集成系统功能"""
    print("🏠 集成厨房安全系统演示")
    print("=" * 60)
    
    # 初始化系统
    config = SystemConfig()
    system = IntegratedKitchenSafetySystem(config)
    
    # 模拟视频帧处理
    print("\n📹 模拟视频流处理...")
    
    for frame_id in range(1, 11):
        # 创建模拟帧（实际使用时从摄像头获取）
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # 处理帧
        result = system.process_frame(frame, frame_id)
        
        # 显示结果
        risk_result = result.get('risk_assessment')
        if risk_result:
            risk_color = {
                RiskLevel.SAFE: "🟢",
                RiskLevel.LOW: "🟡",
                RiskLevel.MEDIUM: "🟠",
                RiskLevel.HIGH: "🔴",
                RiskLevel.CRITICAL: "🚨"
            }
            
            print(f"帧 {frame_id:2d}: {risk_color[risk_result.risk_level]} "
                  f"{risk_result.risk_level.value} "
                  f"(分数: {risk_result.overall_risk_score:.1f})")
            
            # 显示警报
            for alert in risk_result.alert_events:
                print(f"      ⚠️ {alert.alert_type.value}: {alert.description}")
        
        time.sleep(0.5)  # 模拟处理间隔
    
    # 显示统计信息
    print(f"\n📊 系统统计信息:")
    stats = system.get_system_statistics()
    
    risk_stats = stats['risk_statistics']
    print(f"  总评估次数: {risk_stats['total_assessments']}")
    print(f"  平均风险分数: {risk_stats['average_risk_score']:.2f}")
    
    print(f"\n  风险等级分布:")
    for level, count in risk_stats['risk_level_distribution'].items():
        print(f"    {level}: {count}次")
    
    # 演示配置更新
    print(f"\n⚙️ 配置更新演示:")
    new_config = {
        'stove_distance_threshold': 1.5,
        'unattended_time_threshold': 240,
        'risk_weights': {
            'stove_safety': 0.4,
            'person_safety': 0.35,
            'detection_quality': 0.15,
            'environmental': 0.1
        }
    }
    
    success = system.update_configuration(new_config)
    print(f"  配置更新{'成功' if success else '失败'}")
    
    print(f"\n✅ 集成系统演示完成!")


if __name__ == "__main__":
    demo_integrated_system()