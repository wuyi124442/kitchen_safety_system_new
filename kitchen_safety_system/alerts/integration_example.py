"""
报警管理器集成示例

演示AlertManager与风险评估系统的集成使用。
"""

import time
from typing import List, Dict, Any

from ..core.interfaces import AlertEvent, AlertType, AlertLevel, DetectionResult, DetectionType, BoundingBox, PoseResult
from ..core.models import SystemConfig
from ..risk.risk_assessment import RiskAssessment
from .alert_manager import AlertManager


class IntegratedAlertSystem:
    """
    集成报警系统
    
    结合风险评估和报警管理功能，提供完整的安全监控解决方案。
    """
    
    def __init__(self, config: SystemConfig = None):
        """
        初始化集成报警系统
        
        Args:
            config: 系统配置
        """
        self.config = config or SystemConfig()
        
        # 初始化风险评估器
        self.risk_assessment = RiskAssessment(self.config)
        
        # 初始化报警管理器
        self.alert_manager = AlertManager(self.config)
        
        print("集成报警系统已初始化")
    
    def process_detection_frame(self, 
                               detections: List[DetectionResult],
                               pose_results: List[PoseResult],
                               stove_monitor_status: Dict[str, Any] = None,
                               frame_id: int = 0) -> Dict[str, Any]:
        """
        处理检测帧并执行风险评估和报警管理
        
        Args:
            detections: 检测结果列表
            pose_results: 姿态识别结果列表
            stove_monitor_status: 灶台监控状态
            frame_id: 帧ID
            
        Returns:
            Dict[str, Any]: 处理结果
        """
        try:
            # 1. 执行风险评估
            risk_result = self.risk_assessment.assess_risk(
                detections=detections,
                pose_results=pose_results,
                stove_monitor_status=stove_monitor_status,
                frame_id=frame_id
            )
            
            # 2. 处理生成的报警事件
            alert_results = []
            for alert_event in risk_result.alert_events:
                # 触发报警
                success = self.alert_manager.trigger_alert(alert_event)
                alert_results.append({
                    'alert_event': alert_event,
                    'success': success
                })
            
            # 3. 返回综合结果
            return {
                'risk_assessment': risk_result,
                'alert_results': alert_results,
                'alert_statistics': self.alert_manager.get_alert_statistics(),
                'frame_id': frame_id,
                'timestamp': time.time()
            }
            
        except Exception as e:
            print(f"处理检测帧时出错: {e}")
            return {
                'error': str(e),
                'frame_id': frame_id,
                'timestamp': time.time()
            }
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        
        Returns:
            Dict[str, Any]: 系统状态信息
        """
        return {
            'alert_statistics': self.alert_manager.get_alert_statistics(),
            'risk_statistics': self.risk_assessment.get_risk_statistics(),
            'recent_alerts': self.alert_manager.get_recent_alerts(10),
            'system_config': self.config.to_dict()
        }
    
    def resolve_alert(self, alert_id: str) -> bool:
        """
        解决报警
        
        Args:
            alert_id: 报警ID
            
        Returns:
            bool: 是否成功解决
        """
        return self.alert_manager.resolve_alert(alert_id)
    
    def clear_history(self) -> None:
        """清空历史记录"""
        self.alert_manager.clear_alert_history()
        self.risk_assessment.clear_risk_history()
        print("历史记录已清空")


def create_demo_detections() -> List[DetectionResult]:
    """创建演示检测结果"""
    current_time = time.time()
    
    return [
        # 人员检测
        DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=100, y=150, width=80, height=200, confidence=0.92),
            timestamp=current_time,
            frame_id=1
        ),
        
        # 灶台检测
        DetectionResult(
            detection_type=DetectionType.STOVE,
            bbox=BoundingBox(x=300, y=100, width=120, height=80, confidence=0.88),
            timestamp=current_time,
            frame_id=1
        ),
        
        # 火焰检测
        DetectionResult(
            detection_type=DetectionType.FLAME,
            bbox=BoundingBox(x=320, y=110, width=30, height=40, confidence=0.85),
            timestamp=current_time,
            frame_id=1
        )
    ]


def create_demo_poses() -> List[PoseResult]:
    """创建演示姿态结果"""
    from ..core.interfaces import PoseKeypoint
    
    current_time = time.time()
    
    # 正常姿态
    normal_keypoints = [
        PoseKeypoint(x=140, y=160, confidence=0.9, visible=True),  # 头部
        PoseKeypoint(x=140, y=200, confidence=0.85, visible=True), # 颈部
        PoseKeypoint(x=120, y=220, confidence=0.8, visible=True),  # 左肩
        PoseKeypoint(x=160, y=220, confidence=0.8, visible=True),  # 右肩
        PoseKeypoint(x=140, y=280, confidence=0.75, visible=True), # 腰部
        PoseKeypoint(x=130, y=320, confidence=0.7, visible=True),  # 左膝
        PoseKeypoint(x=150, y=320, confidence=0.7, visible=True),  # 右膝
    ]
    
    return [
        PoseResult(
            keypoints=normal_keypoints,
            timestamp=current_time,
            frame_id=1,
            is_fall_detected=False,
            fall_confidence=0.1
        )
    ]


def create_fall_detection_scenario() -> tuple:
    """创建跌倒检测场景"""
    from ..core.interfaces import PoseKeypoint
    
    current_time = time.time()
    
    # 跌倒姿态
    fall_keypoints = [
        PoseKeypoint(x=200, y=300, confidence=0.8, visible=True),  # 头部（低位置）
        PoseKeypoint(x=220, y=310, confidence=0.75, visible=True), # 颈部
        PoseKeypoint(x=180, y=320, confidence=0.7, visible=True),  # 左肩
        PoseKeypoint(x=240, y=320, confidence=0.7, visible=True),  # 右肩
        PoseKeypoint(x=210, y=330, confidence=0.65, visible=True), # 腰部
        PoseKeypoint(x=160, y=340, confidence=0.6, visible=True),  # 左膝
        PoseKeypoint(x=260, y=340, confidence=0.6, visible=True),  # 右膝
    ]
    
    detections = [
        DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=150, y=280, width=120, height=80, confidence=0.90),
            timestamp=current_time,
            frame_id=2
        )
    ]
    
    poses = [
        PoseResult(
            keypoints=fall_keypoints,
            timestamp=current_time,
            frame_id=2,
            is_fall_detected=True,
            fall_confidence=0.95
        )
    ]
    
    return detections, poses


def create_unattended_stove_scenario() -> tuple:
    """创建无人看管灶台场景"""
    current_time = time.time()
    
    # 只有灶台和火焰，没有人员
    detections = [
        DetectionResult(
            detection_type=DetectionType.STOVE,
            bbox=BoundingBox(x=400, y=150, width=100, height=60, confidence=0.92),
            timestamp=current_time,
            frame_id=3
        ),
        DetectionResult(
            detection_type=DetectionType.FLAME,
            bbox=BoundingBox(x=420, y=160, width=25, height=35, confidence=0.88),
            timestamp=current_time,
            frame_id=3
        )
    ]
    
    # 灶台监控状态 - 无人看管
    stove_status = {
        'total_stoves': 1,
        'unattended_stoves': 1,
        'stove_details': [
            {
                'stove_id': 'stove_1',
                'is_unattended': True,
                'unattended_duration': 350.0,  # 超过阈值
                'last_person_time': current_time - 350
            }
        ]
    }
    
    return detections, [], stove_status


def demo_integrated_system():
    """演示集成系统功能"""
    print("=== 集成报警系统演示 ===")
    
    # 创建配置
    config = SystemConfig()
    config.enable_sound_alert = False
    config.enable_email_alert = False
    
    # 创建集成系统
    system = IntegratedAlertSystem(config)
    
    print("\n1. 正常场景处理...")
    detections = create_demo_detections()
    poses = create_demo_poses()
    
    result = system.process_detection_frame(
        detections=detections,
        pose_results=poses,
        frame_id=1
    )
    
    print(f"风险等级: {result['risk_assessment'].risk_level.value}")
    print(f"风险分数: {result['risk_assessment'].overall_risk_score}")
    print(f"生成报警: {len(result['alert_results'])}")
    
    print("\n2. 跌倒检测场景...")
    fall_detections, fall_poses = create_fall_detection_scenario()
    
    result = system.process_detection_frame(
        detections=fall_detections,
        pose_results=fall_poses,
        frame_id=2
    )
    
    print(f"风险等级: {result['risk_assessment'].risk_level.value}")
    print(f"风险分数: {result['risk_assessment'].overall_risk_score}")
    print(f"生成报警: {len(result['alert_results'])}")
    
    for alert_result in result['alert_results']:
        alert = alert_result['alert_event']
        print(f"  - {alert.alert_type.value}: {alert.description}")
    
    print("\n3. 无人看管灶台场景...")
    stove_detections, stove_poses, stove_status = create_unattended_stove_scenario()
    
    result = system.process_detection_frame(
        detections=stove_detections,
        pose_results=stove_poses,
        stove_monitor_status=stove_status,
        frame_id=3
    )
    
    print(f"风险等级: {result['risk_assessment'].risk_level.value}")
    print(f"风险分数: {result['risk_assessment'].overall_risk_score}")
    print(f"生成报警: {len(result['alert_results'])}")
    
    for alert_result in result['alert_results']:
        alert = alert_result['alert_event']
        print(f"  - {alert.alert_type.value}: {alert.description}")
    
    # 显示系统状态
    print("\n=== 系统状态 ===")
    status = system.get_system_status()
    
    alert_stats = status['alert_statistics']
    print(f"总报警数: {alert_stats['total_alerts']}")
    print(f"成功发送: {alert_stats['sent_alerts']}")
    print(f"活跃报警: {alert_stats['active_alerts']}")
    
    risk_stats = status['risk_statistics']
    print(f"风险评估次数: {risk_stats['total_assessments']}")
    print(f"平均风险分数: {risk_stats['average_risk_score']}")
    
    # 显示最近报警
    print(f"\n最近报警 ({len(status['recent_alerts'])}):")
    for alert in status['recent_alerts']:
        print(f"  - [{alert['alert_level']}] {alert['alert_type']}: {alert['description']}")
    
    return system


def main():
    """主演示函数"""
    print("厨房安全系统 - 集成报警系统演示")
    print("=" * 50)
    
    try:
        system = demo_integrated_system()
        print("\n演示完成！")
        
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")


if __name__ == "__main__":
    main()