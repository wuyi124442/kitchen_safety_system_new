"""
风险评估模块演示脚本

展示风险评估算法的各种功能和使用场景。
"""

import time
import json
from typing import List, Dict, Any

from .risk_assessment import RiskAssessment, RiskLevel
from ..core.interfaces import (
    DetectionResult, DetectionType, BoundingBox, PoseResult, PoseKeypoint
)
from ..core.models import SystemConfig


def create_sample_detections() -> Dict[str, List[DetectionResult]]:
    """创建示例检测数据"""
    current_time = time.time()
    
    scenarios = {
        "safe_cooking": [
            # 安全烹饪场景：人员在灶台附近
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=200, y=150, width=80, height=160, confidence=0.92),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.STOVE,
                bbox=BoundingBox(x=300, y=200, width=100, height=60, confidence=0.88),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.FLAME,
                bbox=BoundingBox(x=320, y=180, width=30, height=40, confidence=0.85),
                timestamp=current_time,
                frame_id=1
            )
        ],
        
        "unattended_stove": [
            # 无人看管灶台场景：灶台有火但人员距离较远
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=50, y=150, width=80, height=160, confidence=0.90),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.STOVE,
                bbox=BoundingBox(x=400, y=200, width=100, height=60, confidence=0.87),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.FLAME,
                bbox=BoundingBox(x=420, y=180, width=35, height=45, confidence=0.82),
                timestamp=current_time,
                frame_id=1
            )
        ],
        
        "fall_incident": [
            # 跌倒事件场景
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=150, y=250, width=120, height=80, confidence=0.88),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.STOVE,
                bbox=BoundingBox(x=300, y=200, width=100, height=60, confidence=0.85),
                timestamp=current_time,
                frame_id=1
            )
        ],
        
        "multiple_risks": [
            # 多重风险场景：多人、多灶台、检测质量问题
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=100, y=150, width=80, height=160, confidence=0.45),  # 低置信度
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=200, y=150, width=80, height=160, confidence=0.50),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=300, y=150, width=80, height=160, confidence=0.48),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=400, y=150, width=80, height=160, confidence=0.52),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.STOVE,
                bbox=BoundingBox(x=250, y=200, width=100, height=60, confidence=0.80),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.STOVE,
                bbox=BoundingBox(x=400, y=200, width=100, height=60, confidence=0.82),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.FLAME,
                bbox=BoundingBox(x=270, y=180, width=30, height=40, confidence=0.75),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.FLAME,
                bbox=BoundingBox(x=420, y=180, width=30, height=40, confidence=0.78),
                timestamp=current_time,
                frame_id=1
            )
        ],
        
        "no_detection": []  # 检测失败场景
    }
    
    return scenarios


def create_sample_poses() -> Dict[str, List[PoseResult]]:
    """创建示例姿态数据"""
    current_time = time.time()
    
    scenarios = {
        "normal_standing": [
            PoseResult(
                keypoints=[
                    PoseKeypoint(x=240, y=170, confidence=0.95, visible=True),  # 头部
                    PoseKeypoint(x=240, y=200, confidence=0.90, visible=True),  # 颈部
                    PoseKeypoint(x=240, y=230, confidence=0.88, visible=True),  # 躯干中部
                    PoseKeypoint(x=240, y=260, confidence=0.85, visible=True),  # 臀部
                    PoseKeypoint(x=240, y=290, confidence=0.82, visible=True),  # 膝盖
                    PoseKeypoint(x=240, y=320, confidence=0.80, visible=True),  # 脚踝
                ],
                timestamp=current_time,
                frame_id=1,
                is_fall_detected=False,
                fall_confidence=0.05
            )
        ],
        
        "fall_detected": [
            PoseResult(
                keypoints=[
                    PoseKeypoint(x=200, y=280, confidence=0.90, visible=True),  # 头部（低位置）
                    PoseKeypoint(x=180, y=285, confidence=0.85, visible=True),  # 颈部
                    PoseKeypoint(x=160, y=290, confidence=0.80, visible=True),  # 躯干
                    PoseKeypoint(x=140, y=295, confidence=0.75, visible=True),  # 臀部
                    PoseKeypoint(x=120, y=300, confidence=0.70, visible=True),  # 膝盖
                    PoseKeypoint(x=100, y=305, confidence=0.65, visible=True),  # 脚踝
                ],
                timestamp=current_time,
                frame_id=1,
                is_fall_detected=True,
                fall_confidence=0.92
            )
        ],
        
        "low_confidence_pose": [
            PoseResult(
                keypoints=[
                    PoseKeypoint(x=240, y=170, confidence=0.35, visible=True),  # 低置信度
                    PoseKeypoint(x=240, y=200, confidence=0.30, visible=True),
                    PoseKeypoint(x=240, y=230, confidence=0.25, visible=False), # 不可见
                    PoseKeypoint(x=240, y=260, confidence=0.20, visible=False),
                    PoseKeypoint(x=240, y=290, confidence=0.15, visible=False),
                    PoseKeypoint(x=240, y=320, confidence=0.10, visible=False),
                ],
                timestamp=current_time,
                frame_id=1,
                is_fall_detected=False,
                fall_confidence=0.15
            )
        ],
        
        "multiple_persons": [
            # 多人姿态
            PoseResult(
                keypoints=[
                    PoseKeypoint(x=140, y=170, confidence=0.90, visible=True),
                    PoseKeypoint(x=140, y=200, confidence=0.85, visible=True),
                    PoseKeypoint(x=140, y=230, confidence=0.80, visible=True),
                    PoseKeypoint(x=140, y=260, confidence=0.75, visible=True),
                    PoseKeypoint(x=140, y=290, confidence=0.70, visible=True),
                    PoseKeypoint(x=140, y=320, confidence=0.65, visible=True),
                ],
                timestamp=current_time,
                frame_id=1,
                is_fall_detected=False,
                fall_confidence=0.08
            ),
            PoseResult(
                keypoints=[
                    PoseKeypoint(x=240, y=170, confidence=0.88, visible=True),
                    PoseKeypoint(x=240, y=200, confidence=0.83, visible=True),
                    PoseKeypoint(x=240, y=230, confidence=0.78, visible=True),
                    PoseKeypoint(x=240, y=260, confidence=0.73, visible=True),
                    PoseKeypoint(x=240, y=290, confidence=0.68, visible=True),
                    PoseKeypoint(x=240, y=320, confidence=0.63, visible=True),
                ],
                timestamp=current_time,
                frame_id=1,
                is_fall_detected=False,
                fall_confidence=0.12
            )
        ]
    }
    
    return scenarios


def create_sample_stove_status() -> Dict[str, Dict[str, Any]]:
    """创建示例灶台监控状态"""
    return {
        "safe_monitoring": {
            'total_stoves': 1,
            'unattended_stoves': 0,
            'stoves_with_flame': 1,
            'distance_threshold': 2.0,
            'unattended_time_threshold': 300,
            'stove_details': [{
                'stove_id': 'stove_300_200',
                'has_flame': True,
                'is_unattended': False,
                'unattended_duration': 0,
                'nearest_person_distance': 1.2,
                'location': (350, 230)
            }]
        },
        
        "unattended_monitoring": {
            'total_stoves': 1,
            'unattended_stoves': 1,
            'stoves_with_flame': 1,
            'distance_threshold': 2.0,
            'unattended_time_threshold': 300,
            'stove_details': [{
                'stove_id': 'stove_400_200',
                'has_flame': True,
                'is_unattended': True,
                'unattended_duration': 450,  # 超过阈值
                'nearest_person_distance': 4.5,
                'location': (450, 230)
            }]
        },
        
        "multiple_stoves": {
            'total_stoves': 2,
            'unattended_stoves': 1,
            'stoves_with_flame': 2,
            'distance_threshold': 2.0,
            'unattended_time_threshold': 300,
            'stove_details': [
                {
                    'stove_id': 'stove_250_200',
                    'has_flame': True,
                    'is_unattended': False,
                    'unattended_duration': 0,
                    'nearest_person_distance': 1.8,
                    'location': (300, 230)
                },
                {
                    'stove_id': 'stove_400_200',
                    'has_flame': True,
                    'is_unattended': True,
                    'unattended_duration': 380,
                    'nearest_person_distance': 3.2,
                    'location': (450, 230)
                }
            ]
        }
    }


def print_risk_assessment_result(result, scenario_name: str):
    """打印风险评估结果"""
    print(f"\n{'='*60}")
    print(f"场景: {scenario_name}")
    print(f"{'='*60}")
    
    print(f"总体风险分数: {result.overall_risk_score:.2f}")
    print(f"风险等级: {result.risk_level.value.upper()}")
    print(f"评估时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.timestamp))}")
    
    print(f"\n风险因子详情 ({len(result.risk_factors)}个):")
    print("-" * 50)
    for i, factor in enumerate(result.risk_factors, 1):
        print(f"{i}. {factor.name}")
        print(f"   分数: {factor.score:.1f} | 权重: {factor.weight:.2f} | 置信度: {factor.confidence:.2f}")
        print(f"   加权分数: {factor.weighted_score:.2f}")
        print(f"   描述: {factor.description}")
        if factor.details:
            print(f"   详情: {factor.details}")
        print()
    
    if result.alert_events:
        print(f"触发的警报事件 ({len(result.alert_events)}个):")
        print("-" * 50)
        for i, alert in enumerate(result.alert_events, 1):
            print(f"{i}. {alert.alert_type.value} - {alert.alert_level.value}")
            print(f"   描述: {alert.description}")
            if alert.location:
                print(f"   位置: {alert.location}")
            print()
    
    if result.recommendations:
        print(f"安全建议 ({len(result.recommendations)}条):")
        print("-" * 50)
        for i, rec in enumerate(result.recommendations, 1):
            print(f"{i}. {rec}")
        print()


def demo_basic_scenarios():
    """演示基本风险评估场景"""
    print("🔍 风险评估算法演示 - 基本场景")
    print("=" * 80)
    
    # 初始化风险评估器
    config = SystemConfig()
    risk_assessment = RiskAssessment(config)
    
    # 获取示例数据
    detection_scenarios = create_sample_detections()
    pose_scenarios = create_sample_poses()
    stove_scenarios = create_sample_stove_status()
    
    # 场景1: 安全烹饪
    print("\n🟢 场景1: 安全烹饪")
    result = risk_assessment.assess_risk(
        detections=detection_scenarios["safe_cooking"],
        pose_results=pose_scenarios["normal_standing"],
        stove_monitor_status=stove_scenarios["safe_monitoring"],
        frame_id=1
    )
    print_risk_assessment_result(result, "安全烹饪")
    
    # 场景2: 无人看管灶台
    print("\n🟡 场景2: 无人看管灶台")
    result = risk_assessment.assess_risk(
        detections=detection_scenarios["unattended_stove"],
        pose_results=pose_scenarios["normal_standing"],
        stove_monitor_status=stove_scenarios["unattended_monitoring"],
        frame_id=2
    )
    print_risk_assessment_result(result, "无人看管灶台")
    
    # 场景3: 跌倒事件
    print("\n🔴 场景3: 跌倒事件")
    result = risk_assessment.assess_risk(
        detections=detection_scenarios["fall_incident"],
        pose_results=pose_scenarios["fall_detected"],
        frame_id=3
    )
    print_risk_assessment_result(result, "跌倒事件")
    
    # 场景4: 多重风险
    print("\n🚨 场景4: 多重风险")
    result = risk_assessment.assess_risk(
        detections=detection_scenarios["multiple_risks"],
        pose_results=pose_scenarios["multiple_persons"],
        stove_monitor_status=stove_scenarios["multiple_stoves"],
        frame_id=4
    )
    print_risk_assessment_result(result, "多重风险")
    
    # 场景5: 检测失败
    print("\n⚠️ 场景5: 检测失败")
    result = risk_assessment.assess_risk(
        detections=detection_scenarios["no_detection"],
        pose_results=[],
        frame_id=5
    )
    print_risk_assessment_result(result, "检测失败")


def demo_configuration_management():
    """演示配置管理功能"""
    print("\n\n⚙️ 风险评估配置管理演示")
    print("=" * 80)
    
    risk_assessment = RiskAssessment()
    
    # 显示默认配置
    print("默认风险阈值:")
    for level, (min_val, max_val) in risk_assessment.risk_thresholds.items():
        print(f"  {level.value}: {min_val}-{max_val}")
    
    print("\n默认风险权重:")
    for category, weight in risk_assessment.risk_weights.items():
        print(f"  {category}: {weight}")
    
    # 更新配置
    print("\n更新风险阈值...")
    new_thresholds = {
        'safe': (0, 20),
        'low': (21, 45),
        'medium': (46, 70),
        'high': (71, 85),
        'critical': (86, 100)
    }
    
    success = risk_assessment.update_risk_thresholds(new_thresholds)
    print(f"阈值更新{'成功' if success else '失败'}")
    
    print("\n更新风险权重...")
    new_weights = {
        'stove_safety': 0.4,
        'person_safety': 0.35,
        'detection_quality': 0.15,
        'environmental': 0.1
    }
    
    success = risk_assessment.update_risk_weights(new_weights)
    print(f"权重更新{'成功' if success else '失败'}")
    
    # 显示更新后的配置
    print("\n更新后的风险阈值:")
    for level, (min_val, max_val) in risk_assessment.risk_thresholds.items():
        print(f"  {level.value}: {min_val}-{max_val}")
    
    print("\n更新后的风险权重:")
    for category, weight in risk_assessment.risk_weights.items():
        print(f"  {category}: {weight}")


def demo_statistics_and_trends():
    """演示统计和趋势分析功能"""
    print("\n\n📊 风险统计和趋势分析演示")
    print("=" * 80)
    
    risk_assessment = RiskAssessment()
    detection_scenarios = create_sample_detections()
    pose_scenarios = create_sample_poses()
    stove_scenarios = create_sample_stove_status()
    
    # 模拟一段时间的风险评估
    print("模拟24小时的风险评估数据...")
    
    scenarios = [
        ("safe_cooking", "normal_standing", "safe_monitoring"),
        ("safe_cooking", "normal_standing", "safe_monitoring"),
        ("unattended_stove", "normal_standing", "unattended_monitoring"),
        ("safe_cooking", "normal_standing", "safe_monitoring"),
        ("fall_incident", "fall_detected", None),
        ("safe_cooking", "normal_standing", "safe_monitoring"),
        ("multiple_risks", "multiple_persons", "multiple_stoves"),
        ("safe_cooking", "normal_standing", "safe_monitoring"),
        ("no_detection", None, None),
        ("safe_cooking", "normal_standing", "safe_monitoring"),
    ]
    
    for i, (det_scenario, pose_scenario, stove_scenario) in enumerate(scenarios):
        detections = detection_scenarios.get(det_scenario, [])
        poses = pose_scenarios.get(pose_scenario, []) if pose_scenario else []
        stove_status = stove_scenarios.get(stove_scenario) if stove_scenario else None
        
        result = risk_assessment.assess_risk(
            detections=detections,
            pose_results=poses,
            stove_monitor_status=stove_status,
            frame_id=i+1
        )
        
        # 模拟时间间隔
        time.sleep(0.1)
    
    # 获取统计信息
    stats = risk_assessment.get_risk_statistics()
    
    print(f"\n统计摘要:")
    print(f"  总评估次数: {stats['total_assessments']}")
    print(f"  平均风险分数: {stats['average_risk_score']:.2f}")
    
    print(f"\n风险等级分布:")
    for level, count in stats['risk_level_distribution'].items():
        percentage = (count / stats['total_assessments']) * 100
        print(f"  {level}: {count}次 ({percentage:.1f}%)")
    
    print(f"\n常见风险因子 (前5名):")
    for factor_name, count in stats['common_risk_factors']:
        print(f"  {factor_name}: {count}次")
    
    print(f"\n趋势分析:")
    trend = stats['trend_analysis']
    print(f"  最近平均分数: {trend['recent_average']:.2f}")
    print(f"  趋势方向: {trend['trend_direction']}")


def demo_real_time_monitoring():
    """演示实时监控功能"""
    print("\n\n🔄 实时风险监控演示")
    print("=" * 80)
    
    risk_assessment = RiskAssessment()
    detection_scenarios = create_sample_detections()
    pose_scenarios = create_sample_poses()
    
    print("模拟实时风险监控 (10秒)...")
    
    # 模拟实时数据流
    scenario_sequence = [
        ("safe_cooking", "normal_standing"),
        ("safe_cooking", "normal_standing"),
        ("unattended_stove", "normal_standing"),
        ("unattended_stove", "normal_standing"),
        ("fall_incident", "fall_detected"),  # 突发事件
        ("fall_incident", "fall_detected"),
        ("safe_cooking", "normal_standing"),  # 恢复正常
        ("safe_cooking", "normal_standing"),
    ]
    
    for i, (det_scenario, pose_scenario) in enumerate(scenario_sequence):
        print(f"\n时刻 {i+1}:")
        
        detections = detection_scenarios[det_scenario]
        poses = pose_scenarios[pose_scenario]
        
        result = risk_assessment.assess_risk(
            detections=detections,
            pose_results=poses,
            frame_id=i+1
        )
        
        # 简化输出
        risk_color = {
            RiskLevel.SAFE: "🟢",
            RiskLevel.LOW: "🟡",
            RiskLevel.MEDIUM: "🟠",
            RiskLevel.HIGH: "🔴",
            RiskLevel.CRITICAL: "🚨"
        }
        
        print(f"  {risk_color[result.risk_level]} 风险等级: {result.risk_level.value} (分数: {result.overall_risk_score:.1f})")
        
        if result.alert_events:
            for alert in result.alert_events:
                print(f"  ⚠️ 警报: {alert.alert_type.value} - {alert.description}")
        
        if result.recommendations:
            print(f"  💡 建议: {result.recommendations[0]}")
        
        time.sleep(1)  # 模拟1秒间隔


def main():
    """主演示函数"""
    print("🏠 厨房安全检测系统 - 风险评估模块演示")
    print("=" * 80)
    print("本演示将展示风险评估算法的各种功能:")
    print("1. 基本风险评估场景")
    print("2. 配置管理功能")
    print("3. 统计和趋势分析")
    print("4. 实时监控模拟")
    
    try:
        # 基本场景演示
        demo_basic_scenarios()
        
        # 配置管理演示
        demo_configuration_management()
        
        # 统计分析演示
        demo_statistics_and_trends()
        
        # 实时监控演示
        demo_real_time_monitoring()
        
        print("\n\n✅ 风险评估模块演示完成!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⏹️ 演示被用户中断")
    except Exception as e:
        print(f"\n\n❌ 演示过程中出现错误: {e}")


if __name__ == "__main__":
    main()