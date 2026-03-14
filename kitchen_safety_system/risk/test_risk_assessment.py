"""
风险评估模块单元测试

测试风险评估算法的各种场景和边界情况。
"""

import unittest
import time
from unittest.mock import Mock, patch
from typing import List

from .risk_assessment import RiskAssessment, RiskLevel, RiskFactor, RiskAssessmentResult
from ..core.interfaces import (
    DetectionResult, DetectionType, BoundingBox, PoseResult, PoseKeypoint,
    AlertType, AlertLevel
)
from ..core.models import SystemConfig


class TestRiskAssessment(unittest.TestCase):
    """风险评估测试类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = SystemConfig()
        self.risk_assessment = RiskAssessment(self.config)
        
        # 创建测试用的检测结果
        self.person_detection = DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=100, y=100, width=80, height=160, confidence=0.9),
            timestamp=time.time(),
            frame_id=1
        )
        
        self.stove_detection = DetectionResult(
            detection_type=DetectionType.STOVE,
            bbox=BoundingBox(x=300, y=200, width=100, height=60, confidence=0.85),
            timestamp=time.time(),
            frame_id=1
        )
        
        self.flame_detection = DetectionResult(
            detection_type=DetectionType.FLAME,
            bbox=BoundingBox(x=320, y=180, width=30, height=40, confidence=0.8),
            timestamp=time.time(),
            frame_id=1
        )
        
        # 创建测试用的姿态结果
        self.normal_pose = PoseResult(
            keypoints=[
                PoseKeypoint(x=140, y=120, confidence=0.9, visible=True),  # 头部
                PoseKeypoint(x=140, y=180, confidence=0.8, visible=True),  # 躯干
                PoseKeypoint(x=140, y=240, confidence=0.7, visible=True),  # 臀部
            ],
            timestamp=time.time(),
            frame_id=1,
            is_fall_detected=False,
            fall_confidence=0.1
        )
        
        self.fall_pose = PoseResult(
            keypoints=[
                PoseKeypoint(x=200, y=240, confidence=0.9, visible=True),  # 头部（低位置）
                PoseKeypoint(x=180, y=250, confidence=0.8, visible=True),  # 躯干
                PoseKeypoint(x=160, y=260, confidence=0.7, visible=True),  # 臀部
            ],
            timestamp=time.time(),
            frame_id=1,
            is_fall_detected=True,
            fall_confidence=0.95
        )
    
    def test_safe_scenario(self):
        """测试安全场景"""
        # 只有人员，没有灶台活动
        detections = [self.person_detection]
        pose_results = [self.normal_pose]
        
        result = self.risk_assessment.assess_risk(
            detections=detections,
            pose_results=pose_results,
            frame_id=1
        )
        
        self.assertEqual(result.risk_level, RiskLevel.SAFE)
        self.assertLess(result.overall_risk_score, 30)
        self.assertEqual(len(result.alert_events), 0)
    
    def test_fall_detection_risk(self):
        """测试跌倒检测风险"""
        detections = [self.person_detection]
        pose_results = [self.fall_pose]
        
        result = self.risk_assessment.assess_risk(
            detections=detections,
            pose_results=pose_results,
            frame_id=1
        )
        
        # 跌倒应该触发中等以上风险
        self.assertIn(result.risk_level, [RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL])
        self.assertGreater(result.overall_risk_score, 50)
        
        # 应该有跌倒警报
        fall_alerts = [ae for ae in result.alert_events if ae.alert_type == AlertType.FALL_DETECTED]
        self.assertGreater(len(fall_alerts), 0)
        
        # 应该有跌倒相关的风险因子
        fall_factors = [rf for rf in result.risk_factors if rf.name == "fall_detection"]
        self.assertGreater(len(fall_factors), 0)
        self.assertGreater(fall_factors[0].score, 80)
    
    def test_unattended_stove_risk(self):
        """测试无人看管灶台风险"""
        detections = [self.stove_detection, self.flame_detection]
        pose_results = []
        
        # 模拟灶台监控状态 - 有无人看管的灶台
        stove_status = {
            'total_stoves': 1,
            'unattended_stoves': 1,
            'stoves_with_flame': 1,
            'stove_details': [{
                'stove_id': 'stove_300_200',
                'has_flame': True,
                'is_unattended': True,
                'unattended_duration': 400,  # 超过阈值
                'nearest_person_distance': None,
                'location': (350, 230)
            }]
        }
        
        result = self.risk_assessment.assess_risk(
            detections=detections,
            pose_results=pose_results,
            stove_monitor_status=stove_status,
            frame_id=1
        )
        
        # 无人看管应该触发高风险
        self.assertIn(result.risk_level, [RiskLevel.MEDIUM, RiskLevel.HIGH])
        self.assertGreater(result.overall_risk_score, 50)
        
        # 应该有无人看管相关的风险因子
        unattended_factors = [rf for rf in result.risk_factors if rf.name == "unattended_stove"]
        self.assertGreater(len(unattended_factors), 0)
    
    def test_multiple_risk_factors(self):
        """测试多重风险因子"""
        # 同时有跌倒和无人看管灶台
        detections = [self.person_detection, self.stove_detection, self.flame_detection]
        pose_results = [self.fall_pose]
        
        stove_status = {
            'total_stoves': 1,
            'unattended_stoves': 1,
            'stoves_with_flame': 1,
            'stove_details': [{
                'stove_id': 'stove_300_200',
                'has_flame': True,
                'is_unattended': True,
                'unattended_duration': 400,
                'nearest_person_distance': None,
                'location': (350, 230)
            }]
        }
        
        result = self.risk_assessment.assess_risk(
            detections=detections,
            pose_results=pose_results,
            stove_monitor_status=stove_status,
            frame_id=1
        )
        
        # 多重风险应该触发危急等级
        self.assertEqual(result.risk_level, RiskLevel.CRITICAL)
        self.assertGreater(result.overall_risk_score, 85)
        
        # 应该有多个警报事件
        self.assertGreater(len(result.alert_events), 1)
        
        # 应该有多个风险因子
        self.assertGreater(len(result.risk_factors), 2)
    
    def test_low_detection_confidence(self):
        """测试低检测置信度风险"""
        # 创建低置信度检测结果
        low_conf_detection = DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=100, y=100, width=80, height=160, confidence=0.3),
            timestamp=time.time(),
            frame_id=1
        )
        
        detections = [low_conf_detection]
        pose_results = [self.normal_pose]
        
        result = self.risk_assessment.assess_risk(
            detections=detections,
            pose_results=pose_results,
            frame_id=1
        )
        
        # 应该有检测质量相关的风险因子
        quality_factors = [rf for rf in result.risk_factors 
                          if rf.name == "low_detection_confidence"]
        self.assertGreater(len(quality_factors), 0)
        
        # 应该有相关建议
        confidence_recommendations = [rec for rec in result.recommendations 
                                    if "摄像头" in rec or "光线" in rec]
        self.assertGreater(len(confidence_recommendations), 0)
    
    def test_no_detections(self):
        """测试无检测结果场景"""
        detections = []
        pose_results = []
        
        result = self.risk_assessment.assess_risk(
            detections=detections,
            pose_results=pose_results,
            frame_id=1
        )
        
        # 应该有检测失败的风险因子
        failure_factors = [rf for rf in result.risk_factors 
                          if rf.name == "detection_failure"]
        self.assertGreater(len(failure_factors), 0)
        
        # 风险分数应该适中（检测失败本身是个问题）
        self.assertGreater(result.overall_risk_score, 25)
    
    def test_high_person_density(self):
        """测试高人员密度风险"""
        # 创建多个人员检测
        persons = []
        for i in range(5):  # 5个人员，超过阈值
            person = DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=100+i*50, y=100, width=80, height=160, confidence=0.9),
                timestamp=time.time(),
                frame_id=1
            )
            persons.append(person)
        
        pose_results = [self.normal_pose] * 5
        
        result = self.risk_assessment.assess_risk(
            detections=persons,
            pose_results=pose_results,
            frame_id=1
        )
        
        # 应该有人员密度相关的风险因子
        density_factors = [rf for rf in result.risk_factors 
                          if rf.name == "person_density"]
        self.assertGreater(len(density_factors), 0)
    
    def test_multiple_stoves_active(self):
        """测试多灶台同时使用风险"""
        # 创建多个灶台和火焰
        stoves = []
        flames = []
        
        for i in range(3):  # 3个灶台
            stove = DetectionResult(
                detection_type=DetectionType.STOVE,
                bbox=BoundingBox(x=200+i*100, y=200, width=100, height=60, confidence=0.85),
                timestamp=time.time(),
                frame_id=1
            )
            stoves.append(stove)
            
            flame = DetectionResult(
                detection_type=DetectionType.FLAME,
                bbox=BoundingBox(x=220+i*100, y=180, width=30, height=40, confidence=0.8),
                timestamp=time.time(),
                frame_id=1
            )
            flames.append(flame)
        
        detections = [self.person_detection] + stoves + flames
        pose_results = [self.normal_pose]
        
        result = self.risk_assessment.assess_risk(
            detections=detections,
            pose_results=pose_results,
            frame_id=1
        )
        
        # 应该有多灶台使用的风险因子
        multi_stove_factors = [rf for rf in result.risk_factors 
                              if rf.name == "multiple_stoves_active"]
        self.assertGreater(len(multi_stove_factors), 0)
    
    def test_risk_threshold_configuration(self):
        """测试风险阈值配置"""
        # 测试更新风险阈值
        new_thresholds = {
            'safe': (0, 20),
            'low': (21, 40),
            'medium': (41, 60),
            'high': (61, 80),
            'critical': (81, 100)
        }
        
        success = self.risk_assessment.update_risk_thresholds(new_thresholds)
        self.assertTrue(success)
        
        # 验证阈值已更新
        self.assertEqual(self.risk_assessment.risk_thresholds[RiskLevel.SAFE], (0, 20))
        self.assertEqual(self.risk_assessment.risk_thresholds[RiskLevel.CRITICAL], (81, 100))
    
    def test_risk_weight_configuration(self):
        """测试风险权重配置"""
        # 测试更新风险权重
        new_weights = {
            'stove_safety': 0.4,
            'person_safety': 0.3,
            'detection_quality': 0.2,
            'environmental': 0.1
        }
        
        success = self.risk_assessment.update_risk_weights(new_weights)
        self.assertTrue(success)
        
        # 验证权重已更新
        self.assertEqual(self.risk_assessment.risk_weights['stove_safety'], 0.4)
        
        # 测试无效权重（总和不为1）
        invalid_weights = {
            'stove_safety': 0.5,
            'person_safety': 0.5,
            'detection_quality': 0.2,
            'environmental': 0.1
        }
        
        success = self.risk_assessment.update_risk_weights(invalid_weights)
        self.assertFalse(success)
    
    def test_alert_cooldown(self):
        """测试警报冷却时间"""
        detections = [self.person_detection]
        pose_results = [self.fall_pose]
        
        # 第一次评估应该产生警报
        result1 = self.risk_assessment.assess_risk(
            detections=detections,
            pose_results=pose_results,
            frame_id=1
        )
        
        fall_alerts1 = [ae for ae in result1.alert_events if ae.alert_type == AlertType.FALL_DETECTED]
        self.assertGreater(len(fall_alerts1), 0)
        
        # 立即进行第二次评估，应该没有警报（冷却期内）
        result2 = self.risk_assessment.assess_risk(
            detections=detections,
            pose_results=pose_results,
            frame_id=2
        )
        
        fall_alerts2 = [ae for ae in result2.alert_events if ae.alert_type == AlertType.FALL_DETECTED]
        self.assertEqual(len(fall_alerts2), 0)
    
    def test_risk_statistics(self):
        """测试风险统计功能"""
        # 进行多次评估以建立历史记录
        for i in range(10):
            detections = [self.person_detection]
            pose_results = [self.normal_pose if i % 2 == 0 else self.fall_pose]
            
            self.risk_assessment.assess_risk(
                detections=detections,
                pose_results=pose_results,
                frame_id=i
            )
        
        # 获取统计信息
        stats = self.risk_assessment.get_risk_statistics()
        
        self.assertEqual(stats['total_assessments'], 10)
        self.assertGreater(stats['average_risk_score'], 0)
        self.assertIn('risk_level_distribution', stats)
        self.assertIn('common_risk_factors', stats)
        self.assertIn('trend_analysis', stats)
    
    def test_recommendations_generation(self):
        """测试安全建议生成"""
        # 跌倒场景
        detections = [self.person_detection]
        pose_results = [self.fall_pose]
        
        result = self.risk_assessment.assess_risk(
            detections=detections,
            pose_results=pose_results,
            frame_id=1
        )
        
        # 应该有跌倒相关的建议
        fall_recommendations = [rec for rec in result.recommendations 
                               if "跌倒" in rec or "急救" in rec]
        self.assertGreater(len(fall_recommendations), 0)
        
        # 建议数量应该合理
        self.assertLessEqual(len(result.recommendations), 8)
    
    def test_risk_amplification(self):
        """测试风险放大因子"""
        # 创建多个高风险因子
        risk_factors = [
            RiskFactor(
                name="fall_detection",
                score=85.0,
                weight=0.3,
                confidence=0.95,
                description="跌倒检测"
            ),
            RiskFactor(
                name="unattended_stove",
                score=80.0,
                weight=0.35,
                confidence=0.9,
                description="无人看管灶台"
            )
        ]
        
        amplification = self.risk_assessment._calculate_risk_amplification(risk_factors)
        
        # 多个高风险因子应该增加放大因子
        self.assertGreater(amplification, 1.0)
        
        # 跌倒+无人看管应该有额外放大
        self.assertGreater(amplification, 1.3)
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 空输入
        result = self.risk_assessment.assess_risk([], [], frame_id=1)
        self.assertIsInstance(result, RiskAssessmentResult)
        
        # 极高置信度
        high_conf_detection = DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=100, y=100, width=80, height=160, confidence=1.0),
            timestamp=time.time(),
            frame_id=1
        )
        
        result = self.risk_assessment.assess_risk([high_conf_detection], [self.normal_pose], frame_id=1)
        self.assertIsInstance(result, RiskAssessmentResult)
        
        # 极低置信度
        low_conf_detection = DetectionResult(
            detection_type=DetectionType.PERSON,
            bbox=BoundingBox(x=100, y=100, width=80, height=160, confidence=0.01),
            timestamp=time.time(),
            frame_id=1
        )
        
        result = self.risk_assessment.assess_risk([low_conf_detection], [self.normal_pose], frame_id=1)
        self.assertIsInstance(result, RiskAssessmentResult)


if __name__ == '__main__':
    unittest.main()