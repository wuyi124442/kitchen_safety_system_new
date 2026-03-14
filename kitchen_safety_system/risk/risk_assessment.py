"""
风险评估模块

实现综合风险评估算法，结合多种安全因素进行厨房安全评估。
"""

import time
import math
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..core.interfaces import (
    DetectionResult, DetectionType, AlertEvent, AlertType, AlertLevel, 
    BoundingBox, PoseResult
)
from ..core.models import SystemConfig
from ..utils.logger import get_logger


class RiskLevel(Enum):
    """风险等级枚举"""
    SAFE = "safe"           # 安全 (0-25)
    LOW = "low"             # 低风险 (26-50)
    MEDIUM = "medium"       # 中等风险 (51-75)
    HIGH = "high"           # 高风险 (76-90)
    CRITICAL = "critical"   # 危急 (91-100)


@dataclass
class RiskFactor:
    """风险因子数据结构"""
    name: str
    score: float            # 0-100 分数
    weight: float           # 权重 0-1
    confidence: float       # 置信度 0-1
    description: str
    details: Optional[Dict[str, Any]] = None
    
    @property
    def weighted_score(self) -> float:
        """获取加权分数"""
        return self.score * self.weight * self.confidence


@dataclass
class RiskAssessmentResult:
    """风险评估结果"""
    overall_risk_score: float       # 总体风险分数 0-100
    risk_level: RiskLevel          # 风险等级
    risk_factors: List[RiskFactor] # 风险因子列表
    timestamp: float               # 评估时间戳
    frame_id: int                  # 帧ID
    alert_events: List[AlertEvent] # 触发的警报事件
    recommendations: List[str]      # 安全建议
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            'overall_risk_score': self.overall_risk_score,
            'risk_level': self.risk_level.value,
            'risk_factors': [
                {
                    'name': rf.name,
                    'score': rf.score,
                    'weight': rf.weight,
                    'confidence': rf.confidence,
                    'weighted_score': rf.weighted_score,
                    'description': rf.description,
                    'details': rf.details
                }
                for rf in self.risk_factors
            ],
            'timestamp': self.timestamp,
            'frame_id': self.frame_id,
            'alert_events': [
                {
                    'alert_type': ae.alert_type.value,
                    'alert_level': ae.alert_level.value,
                    'description': ae.description,
                    'location': ae.location
                }
                for ae in self.alert_events
            ],
            'recommendations': self.recommendations
        }


class RiskAssessment:
    """
    综合风险评估器
    
    结合多种风险因素进行厨房安全评估：
    1. 灶台安全风险（无人看管、距离等）
    2. 人员安全风险（跌倒检测、活动状态）
    3. 检测质量风险（置信度、稳定性）
    4. 环境风险（人员数量、活动密度）
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        """
        初始化风险评估器
        
        Args:
            config: 系统配置对象
        """
        self.logger = get_logger(__name__)
        
        # 配置参数
        self.config = config or SystemConfig()
        
        # 风险阈值配置
        self.risk_thresholds = {
            RiskLevel.SAFE: (0, 25),
            RiskLevel.LOW: (26, 50),
            RiskLevel.MEDIUM: (51, 75),
            RiskLevel.HIGH: (76, 90),
            RiskLevel.CRITICAL: (91, 100)
        }
        
        # 风险因子权重配置
        self.risk_weights = {
            'stove_safety': 0.35,      # 灶台安全权重
            'person_safety': 0.30,     # 人员安全权重
            'detection_quality': 0.20, # 检测质量权重
            'environmental': 0.15      # 环境因素权重
        }
        
        # 历史数据用于趋势分析
        self.risk_history: List[RiskAssessmentResult] = []
        self.max_history_size = 100
        
        # 警报冷却时间管理
        self.last_alert_times: Dict[str, float] = {}
        self.alert_cooldown_time = self.config.alert_cooldown_time
        
        self.logger.info("风险评估器已初始化")
    
    def assess_risk(self, 
                   detections: List[DetectionResult],
                   pose_results: List[PoseResult],
                   stove_monitor_status: Optional[Dict[str, Any]] = None,
                   frame_id: int = 0) -> RiskAssessmentResult:
        """
        执行综合风险评估
        
        Args:
            detections: 检测结果列表
            pose_results: 姿态识别结果列表
            stove_monitor_status: 灶台监控状态
            frame_id: 帧ID
            
        Returns:
            RiskAssessmentResult: 风险评估结果
        """
        current_time = time.time()
        
        try:
            # 计算各类风险因子
            risk_factors = []
            
            # 1. 灶台安全风险评估
            stove_risk_factors = self._assess_stove_safety_risk(
                detections, stove_monitor_status
            )
            risk_factors.extend(stove_risk_factors)
            
            # 2. 人员安全风险评估
            person_risk_factors = self._assess_person_safety_risk(
                detections, pose_results
            )
            risk_factors.extend(person_risk_factors)
            
            # 3. 检测质量风险评估
            quality_risk_factors = self._assess_detection_quality_risk(
                detections, pose_results
            )
            risk_factors.extend(quality_risk_factors)
            
            # 4. 环境风险评估
            env_risk_factors = self._assess_environmental_risk(
                detections, pose_results
            )
            risk_factors.extend(env_risk_factors)
            
            # 计算总体风险分数
            overall_score = self._calculate_overall_risk_score(risk_factors)
            
            # 确定风险等级
            risk_level = self._determine_risk_level(overall_score)
            
            # 生成警报事件
            alert_events = self._generate_alert_events(
                risk_factors, risk_level, current_time
            )
            
            # 生成安全建议
            recommendations = self._generate_recommendations(
                risk_factors, risk_level
            )
            
            # 创建评估结果
            result = RiskAssessmentResult(
                overall_risk_score=overall_score,
                risk_level=risk_level,
                risk_factors=risk_factors,
                timestamp=current_time,
                frame_id=frame_id,
                alert_events=alert_events,
                recommendations=recommendations
            )
            
            # 更新历史记录
            self._update_risk_history(result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"风险评估出错: {e}")
            # 返回默认安全状态
            return RiskAssessmentResult(
                overall_risk_score=0.0,
                risk_level=RiskLevel.SAFE,
                risk_factors=[],
                timestamp=current_time,
                frame_id=frame_id,
                alert_events=[],
                recommendations=[]
            )
    
    def _assess_stove_safety_risk(self, 
                                 detections: List[DetectionResult],
                                 stove_status: Optional[Dict[str, Any]]) -> List[RiskFactor]:
        """
        评估灶台安全风险
        
        Args:
            detections: 检测结果
            stove_status: 灶台监控状态
            
        Returns:
            List[RiskFactor]: 灶台安全风险因子列表
        """
        risk_factors = []
        
        # 获取灶台和火焰检测
        stoves = [d for d in detections if d.detection_type == DetectionType.STOVE]
        flames = [d for d in detections if d.detection_type == DetectionType.FLAME]
        persons = [d for d in detections if d.detection_type == DetectionType.PERSON]
        
        if not stoves and not flames:
            # 没有检测到灶台或火焰，风险较低
            risk_factors.append(RiskFactor(
                name="stove_presence",
                score=10.0,
                weight=self.risk_weights['stove_safety'],
                confidence=0.9,
                description="未检测到活跃的灶台使用",
                details={'stove_count': 0, 'flame_count': 0}
            ))
            return risk_factors
        
        # 无人看管风险评估
        if stove_status:
            unattended_stoves = stove_status.get('unattended_stoves', 0)
            total_stoves = stove_status.get('total_stoves', 0)
            
            if unattended_stoves > 0:
                # 计算无人看管风险分数
                unattended_ratio = unattended_stoves / max(total_stoves, 1)
                max_unattended_duration = 0
                
                for stove_detail in stove_status.get('stove_details', []):
                    if stove_detail.get('is_unattended', False):
                        duration = stove_detail.get('unattended_duration', 0)
                        max_unattended_duration = max(max_unattended_duration, duration)
                
                # 基于无人看管时间计算风险分数
                time_factor = min(max_unattended_duration / self.config.unattended_time_threshold, 2.0)
                unattended_score = min(50 + (time_factor * 40), 95)
                
                risk_factors.append(RiskFactor(
                    name="unattended_stove",
                    score=unattended_score,
                    weight=self.risk_weights['stove_safety'],
                    confidence=0.95,
                    description=f"{unattended_stoves}个灶台无人看管，最长{int(max_unattended_duration)}秒",
                    details={
                        'unattended_count': unattended_stoves,
                        'max_duration': max_unattended_duration,
                        'unattended_ratio': unattended_ratio
                    }
                ))
        
        # 人员-灶台距离风险评估
        if stoves and persons:
            min_distance = float('inf')
            for stove in stoves:
                stove_center = stove.bbox.center
                for person in persons:
                    person_center = person.bbox.center
                    distance = self._calculate_distance(stove_center, person_center)
                    min_distance = min(min_distance, distance)
            
            if min_distance != float('inf'):
                # 转换为米（假设100像素=1米）
                distance_meters = min_distance / 100.0
                
                if distance_meters > self.config.stove_distance_threshold:
                    # 距离过远的风险
                    distance_factor = min(distance_meters / self.config.stove_distance_threshold, 3.0)
                    distance_score = min(30 + (distance_factor - 1) * 25, 70)
                    
                    risk_factors.append(RiskFactor(
                        name="stove_distance",
                        score=distance_score,
                        weight=self.risk_weights['stove_safety'] * 0.6,
                        confidence=0.8,
                        description=f"人员距离灶台过远 ({distance_meters:.1f}m)",
                        details={'min_distance_meters': distance_meters}
                    ))
        
        # 火焰强度风险评估
        if flames:
            avg_flame_confidence = sum(f.bbox.confidence for f in flames) / len(flames)
            flame_area_total = sum(f.bbox.area for f in flames)
            
            # 基于火焰检测置信度和面积评估风险
            if avg_flame_confidence > 0.8 and flame_area_total > 5000:
                flame_score = min(20 + (flame_area_total / 1000) * 5, 60)
                
                risk_factors.append(RiskFactor(
                    name="flame_intensity",
                    score=flame_score,
                    weight=self.risk_weights['stove_safety'] * 0.4,
                    confidence=avg_flame_confidence,
                    description=f"检测到{len(flames)}个火焰源，总面积{flame_area_total}像素",
                    details={
                        'flame_count': len(flames),
                        'total_area': flame_area_total,
                        'avg_confidence': avg_flame_confidence
                    }
                ))
        
        return risk_factors
    
    def _assess_person_safety_risk(self, 
                                  detections: List[DetectionResult],
                                  pose_results: List[PoseResult]) -> List[RiskFactor]:
        """
        评估人员安全风险
        
        Args:
            detections: 检测结果
            pose_results: 姿态识别结果
            
        Returns:
            List[RiskFactor]: 人员安全风险因子列表
        """
        risk_factors = []
        
        persons = [d for d in detections if d.detection_type == DetectionType.PERSON]
        
        if not persons:
            # 没有检测到人员
            risk_factors.append(RiskFactor(
                name="person_presence",
                score=15.0,
                weight=self.risk_weights['person_safety'],
                confidence=0.9,
                description="厨房内未检测到人员",
                details={'person_count': 0}
            ))
            return risk_factors
        
        # 跌倒风险评估
        fall_detected = False
        max_fall_confidence = 0.0
        
        for pose_result in pose_results:
            if pose_result.is_fall_detected:
                fall_detected = True
                max_fall_confidence = max(max_fall_confidence, pose_result.fall_confidence)
        
        if fall_detected:
            fall_score = min(80 + (max_fall_confidence * 20), 100)
            
            risk_factors.append(RiskFactor(
                name="fall_detection",
                score=fall_score,
                weight=self.risk_weights['person_safety'],
                confidence=max_fall_confidence,
                description=f"检测到人员跌倒，置信度{max_fall_confidence:.2f}",
                details={'fall_confidence': max_fall_confidence}
            ))
        
        # 人员数量风险评估
        person_count = len(persons)
        if person_count > 3:
            # 人员过多可能增加风险
            crowd_score = min(20 + (person_count - 3) * 10, 50)
            
            risk_factors.append(RiskFactor(
                name="person_density",
                score=crowd_score,
                weight=self.risk_weights['person_safety'] * 0.3,
                confidence=0.8,
                description=f"厨房内人员较多 ({person_count}人)",
                details={'person_count': person_count}
            ))
        
        # 人员活动状态评估
        if pose_results:
            avg_keypoint_confidence = 0.0
            total_keypoints = 0
            
            for pose_result in pose_results:
                for keypoint in pose_result.keypoints:
                    if keypoint.visible:
                        avg_keypoint_confidence += keypoint.confidence
                        total_keypoints += 1
            
            if total_keypoints > 0:
                avg_keypoint_confidence /= total_keypoints
                
                # 低置信度可能表示人员状态异常
                if avg_keypoint_confidence < 0.5:
                    activity_score = min(40 + (0.5 - avg_keypoint_confidence) * 60, 80)
                    
                    risk_factors.append(RiskFactor(
                        name="person_activity",
                        score=activity_score,
                        weight=self.risk_weights['person_safety'] * 0.4,
                        confidence=avg_keypoint_confidence,
                        description=f"人员活动状态异常，姿态置信度低({avg_keypoint_confidence:.2f})",
                        details={'avg_keypoint_confidence': avg_keypoint_confidence}
                    ))
        
        return risk_factors
    
    def _assess_detection_quality_risk(self, 
                                     detections: List[DetectionResult],
                                     pose_results: List[PoseResult]) -> List[RiskFactor]:
        """
        评估检测质量风险
        
        Args:
            detections: 检测结果
            pose_results: 姿态识别结果
            
        Returns:
            List[RiskFactor]: 检测质量风险因子列表
        """
        risk_factors = []
        
        if not detections:
            # 没有任何检测结果
            risk_factors.append(RiskFactor(
                name="detection_failure",
                score=60.0,
                weight=self.risk_weights['detection_quality'],
                confidence=1.0,
                description="未检测到任何目标，可能存在检测系统故障",
                details={'detection_count': 0}
            ))
            return risk_factors
        
        # 检测置信度评估
        avg_confidence = sum(d.bbox.confidence for d in detections) / len(detections)
        
        if avg_confidence < self.config.confidence_threshold:
            confidence_score = min(50 + (self.config.confidence_threshold - avg_confidence) * 100, 80)
            
            risk_factors.append(RiskFactor(
                name="low_detection_confidence",
                score=confidence_score,
                weight=self.risk_weights['detection_quality'],
                confidence=avg_confidence,
                description=f"检测置信度较低 ({avg_confidence:.2f})",
                details={'avg_confidence': avg_confidence}
            ))
        
        # 检测稳定性评估（基于历史数据）
        if len(self.risk_history) > 5:
            recent_detection_counts = []
            for i in range(-5, 0):
                if abs(i) <= len(self.risk_history):
                    hist_result = self.risk_history[i]
                    detection_count = sum(1 for rf in hist_result.risk_factors 
                                        if 'detection_count' in rf.details)
                    recent_detection_counts.append(detection_count)
            
            if recent_detection_counts:
                detection_variance = self._calculate_variance(recent_detection_counts)
                if detection_variance > 2.0:  # 检测结果波动较大
                    stability_score = min(30 + detection_variance * 10, 60)
                    
                    risk_factors.append(RiskFactor(
                        name="detection_instability",
                        score=stability_score,
                        weight=self.risk_weights['detection_quality'] * 0.6,
                        confidence=0.7,
                        description=f"检测结果不稳定，方差{detection_variance:.2f}",
                        details={'detection_variance': detection_variance}
                    ))
        
        return risk_factors
    
    def _assess_environmental_risk(self, 
                                  detections: List[DetectionResult],
                                  pose_results: List[PoseResult]) -> List[RiskFactor]:
        """
        评估环境风险因素
        
        Args:
            detections: 检测结果
            pose_results: 姿态识别结果
            
        Returns:
            List[RiskFactor]: 环境风险因子列表
        """
        risk_factors = []
        
        # 活动密度评估
        total_detections = len(detections)
        persons = [d for d in detections if d.detection_type == DetectionType.PERSON]
        stoves = [d for d in detections if d.detection_type == DetectionType.STOVE]
        flames = [d for d in detections if d.detection_type == DetectionType.FLAME]
        
        # 计算活动密度指标
        activity_density = total_detections / max(len(persons), 1)
        
        if activity_density > 3.0:  # 高活动密度
            density_score = min(25 + (activity_density - 3.0) * 15, 55)
            
            risk_factors.append(RiskFactor(
                name="high_activity_density",
                score=density_score,
                weight=self.risk_weights['environmental'],
                confidence=0.8,
                description=f"厨房活动密度较高 (密度指标: {activity_density:.1f})",
                details={'activity_density': activity_density}
            ))
        
        # 时间因素评估（基于当前时间）
        current_hour = datetime.now().hour
        
        # 深夜或凌晨时段风险较高
        if current_hour >= 23 or current_hour <= 5:
            time_score = 35.0
            
            risk_factors.append(RiskFactor(
                name="high_risk_time",
                score=time_score,
                weight=self.risk_weights['environmental'] * 0.5,
                confidence=1.0,
                description=f"当前为高风险时段 ({current_hour}:00)",
                details={'current_hour': current_hour}
            ))
        
        # 多灶台同时使用风险
        if len(stoves) > 1 and len(flames) > 1:
            multi_stove_score = min(30 + (len(stoves) - 1) * 15, 60)
            
            risk_factors.append(RiskFactor(
                name="multiple_stoves_active",
                score=multi_stove_score,
                weight=self.risk_weights['environmental'] * 0.7,
                confidence=0.9,
                description=f"多个灶台同时使用 ({len(stoves)}个灶台, {len(flames)}个火焰)",
                details={'active_stoves': len(stoves), 'active_flames': len(flames)}
            ))
        
        return risk_factors
    
    def _calculate_overall_risk_score(self, risk_factors: List[RiskFactor]) -> float:
        """
        计算总体风险分数
        
        Args:
            risk_factors: 风险因子列表
            
        Returns:
            float: 总体风险分数 (0-100)
        """
        if not risk_factors:
            return 0.0
        
        # 计算加权平均分数
        total_weighted_score = sum(rf.weighted_score for rf in risk_factors)
        total_weight = sum(rf.weight * rf.confidence for rf in risk_factors)
        
        if total_weight == 0:
            return 0.0
        
        base_score = total_weighted_score / total_weight
        
        # 应用风险放大因子
        amplification_factor = self._calculate_risk_amplification(risk_factors)
        
        # 最终分数
        final_score = min(base_score * amplification_factor, 100.0)
        
        return round(final_score, 2)
    
    def _calculate_risk_amplification(self, risk_factors: List[RiskFactor]) -> float:
        """
        计算风险放大因子
        
        Args:
            risk_factors: 风险因子列表
            
        Returns:
            float: 放大因子 (1.0-2.0)
        """
        amplification = 1.0
        
        # 检查是否存在多个高风险因子
        high_risk_factors = [rf for rf in risk_factors if rf.score > 70]
        if len(high_risk_factors) > 1:
            amplification += 0.2 * (len(high_risk_factors) - 1)
        
        # 检查是否存在跌倒和无人看管同时发生
        has_fall = any(rf.name == "fall_detection" for rf in risk_factors)
        has_unattended = any(rf.name == "unattended_stove" for rf in risk_factors)
        if has_fall and has_unattended:
            amplification += 0.3
        
        # 检查检测质量问题
        has_detection_issues = any(rf.name in ["detection_failure", "low_detection_confidence"] 
                                 for rf in risk_factors)
        if has_detection_issues:
            amplification += 0.15
        
        return min(amplification, 2.0)
    
    def _determine_risk_level(self, overall_score: float) -> RiskLevel:
        """
        根据总体分数确定风险等级
        
        Args:
            overall_score: 总体风险分数
            
        Returns:
            RiskLevel: 风险等级
        """
        for level, (min_score, max_score) in self.risk_thresholds.items():
            if min_score <= overall_score <= max_score:
                return level
        
        # 默认返回最高风险等级
        return RiskLevel.CRITICAL
    
    def _generate_alert_events(self, 
                              risk_factors: List[RiskFactor],
                              risk_level: RiskLevel,
                              timestamp: float) -> List[AlertEvent]:
        """
        生成警报事件
        
        Args:
            risk_factors: 风险因子列表
            risk_level: 风险等级
            timestamp: 时间戳
            
        Returns:
            List[AlertEvent]: 警报事件列表
        """
        alert_events = []
        current_time = timestamp
        
        # 检查冷却时间
        def should_alert(alert_type_key: str) -> bool:
            last_time = self.last_alert_times.get(alert_type_key, 0)
            return current_time - last_time >= self.alert_cooldown_time
        
        # 跌倒警报
        fall_factors = [rf for rf in risk_factors if rf.name == "fall_detection"]
        if fall_factors and should_alert("fall"):
            fall_factor = fall_factors[0]
            alert_events.append(AlertEvent(
                alert_type=AlertType.FALL_DETECTED,
                alert_level=AlertLevel.CRITICAL,
                timestamp=timestamp,
                location=None,  # 需要从检测结果中获取
                description=fall_factor.description,
                additional_data=fall_factor.details
            ))
            self.last_alert_times["fall"] = current_time
        
        # 无人看管警报
        unattended_factors = [rf for rf in risk_factors if rf.name == "unattended_stove"]
        if unattended_factors and should_alert("unattended_stove"):
            unattended_factor = unattended_factors[0]
            alert_events.append(AlertEvent(
                alert_type=AlertType.UNATTENDED_STOVE,
                alert_level=AlertLevel.HIGH,
                timestamp=timestamp,
                location=None,  # 需要从灶台位置获取
                description=unattended_factor.description,
                additional_data=unattended_factor.details
            ))
            self.last_alert_times["unattended_stove"] = current_time
        
        # 系统风险警报
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL] and should_alert("system_risk"):
            alert_events.append(AlertEvent(
                alert_type=AlertType.SYSTEM_ERROR,
                alert_level=AlertLevel.MEDIUM if risk_level == RiskLevel.HIGH else AlertLevel.HIGH,
                timestamp=timestamp,
                location=None,
                description=f"系统检测到{risk_level.value}风险等级",
                additional_data={
                    'risk_level': risk_level.value,
                    'risk_factor_count': len(risk_factors)
                }
            ))
            self.last_alert_times["system_risk"] = current_time
        
        return alert_events
    
    def _generate_recommendations(self, 
                                 risk_factors: List[RiskFactor],
                                 risk_level: RiskLevel) -> List[str]:
        """
        生成安全建议
        
        Args:
            risk_factors: 风险因子列表
            risk_level: 风险等级
            
        Returns:
            List[str]: 安全建议列表
        """
        recommendations = []
        
        # 基于风险因子生成建议
        for risk_factor in risk_factors:
            if risk_factor.name == "fall_detection":
                recommendations.append("立即检查跌倒人员状况，必要时呼叫急救服务")
                recommendations.append("确保厨房地面干燥，移除可能导致滑倒的障碍物")
            
            elif risk_factor.name == "unattended_stove":
                recommendations.append("立即返回灶台附近，关注烹饪状况")
                recommendations.append("如需离开，请关闭灶台火源")
            
            elif risk_factor.name == "stove_distance":
                recommendations.append("请靠近灶台，保持在安全监控距离内")
            
            elif risk_factor.name == "person_density":
                recommendations.append("减少厨房内人员数量，避免过度拥挤")
            
            elif risk_factor.name == "multiple_stoves_active":
                recommendations.append("避免同时使用多个灶台，集中注意力")
            
            elif risk_factor.name == "low_detection_confidence":
                recommendations.append("检查摄像头清洁度和光线条件")
                recommendations.append("确保检测区域无遮挡物")
            
            elif risk_factor.name == "high_risk_time":
                recommendations.append("深夜烹饪请格外小心，建议有人陪同")
        
        # 基于风险等级生成通用建议
        if risk_level == RiskLevel.CRITICAL:
            recommendations.insert(0, "⚠️ 危急风险：立即停止当前活动，检查安全状况")
        elif risk_level == RiskLevel.HIGH:
            recommendations.insert(0, "⚠️ 高风险：请提高警惕，采取预防措施")
        elif risk_level == RiskLevel.MEDIUM:
            recommendations.insert(0, "⚠️ 中等风险：注意安全，建议调整当前行为")
        
        # 去重并限制数量
        unique_recommendations = list(dict.fromkeys(recommendations))
        return unique_recommendations[:8]  # 最多8条建议
    
    def _update_risk_history(self, result: RiskAssessmentResult) -> None:
        """
        更新风险评估历史记录
        
        Args:
            result: 风险评估结果
        """
        self.risk_history.append(result)
        
        # 保持历史记录大小限制
        if len(self.risk_history) > self.max_history_size:
            self.risk_history = self.risk_history[-self.max_history_size:]
    
    def _calculate_distance(self, point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
        """
        计算两点之间的欧几里得距离
        
        Args:
            point1: 第一个点坐标
            point2: 第二个点坐标
            
        Returns:
            float: 距离（像素）
        """
        x1, y1 = point1
        x2, y2 = point2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    def _calculate_variance(self, values: List[float]) -> float:
        """
        计算数值列表的方差
        
        Args:
            values: 数值列表
            
        Returns:
            float: 方差
        """
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance
    
    def get_risk_statistics(self) -> Dict[str, Any]:
        """
        获取风险统计信息
        
        Returns:
            Dict[str, Any]: 风险统计数据
        """
        if not self.risk_history:
            return {
                'total_assessments': 0,
                'average_risk_score': 0.0,
                'risk_level_distribution': {},
                'common_risk_factors': [],
                'trend_analysis': {}
            }
        
        # 基本统计
        total_assessments = len(self.risk_history)
        avg_risk_score = sum(r.overall_risk_score for r in self.risk_history) / total_assessments
        
        # 风险等级分布
        level_counts = {}
        for result in self.risk_history:
            level = result.risk_level.value
            level_counts[level] = level_counts.get(level, 0) + 1
        
        # 常见风险因子
        factor_counts = {}
        for result in self.risk_history:
            for factor in result.risk_factors:
                factor_counts[factor.name] = factor_counts.get(factor.name, 0) + 1
        
        common_factors = sorted(factor_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # 趋势分析（最近10次评估）
        recent_scores = [r.overall_risk_score for r in self.risk_history[-10:]]
        trend_analysis = {
            'recent_average': sum(recent_scores) / len(recent_scores) if recent_scores else 0,
            'trend_direction': 'stable'
        }
        
        if len(recent_scores) >= 5:
            first_half = sum(recent_scores[:len(recent_scores)//2]) / (len(recent_scores)//2)
            second_half = sum(recent_scores[len(recent_scores)//2:]) / (len(recent_scores) - len(recent_scores)//2)
            
            if second_half > first_half + 5:
                trend_analysis['trend_direction'] = 'increasing'
            elif second_half < first_half - 5:
                trend_analysis['trend_direction'] = 'decreasing'
        
        return {
            'total_assessments': total_assessments,
            'average_risk_score': round(avg_risk_score, 2),
            'risk_level_distribution': level_counts,
            'common_risk_factors': common_factors,
            'trend_analysis': trend_analysis
        }
    
    def update_risk_thresholds(self, new_thresholds: Dict[str, Tuple[int, int]]) -> bool:
        """
        更新风险阈值配置
        
        Args:
            new_thresholds: 新的风险阈值配置
            
        Returns:
            bool: 是否更新成功
        """
        try:
            for level_name, (min_val, max_val) in new_thresholds.items():
                if hasattr(RiskLevel, level_name.upper()):
                    level = RiskLevel[level_name.upper()]
                    if 0 <= min_val <= max_val <= 100:
                        self.risk_thresholds[level] = (min_val, max_val)
                    else:
                        self.logger.warning(f"无效的阈值范围: {level_name} ({min_val}, {max_val})")
                        return False
            
            self.logger.info("风险阈值已更新")
            return True
            
        except Exception as e:
            self.logger.error(f"更新风险阈值失败: {e}")
            return False
    
    def update_risk_weights(self, new_weights: Dict[str, float]) -> bool:
        """
        更新风险权重配置
        
        Args:
            new_weights: 新的风险权重配置
            
        Returns:
            bool: 是否更新成功
        """
        try:
            # 验证权重总和
            total_weight = sum(new_weights.values())
            if abs(total_weight - 1.0) > 0.01:
                self.logger.warning(f"权重总和应为1.0，当前为{total_weight}")
                return False
            
            # 验证权重范围
            for category, weight in new_weights.items():
                if not (0.0 <= weight <= 1.0):
                    self.logger.warning(f"权重值应在0-1范围内: {category} = {weight}")
                    return False
            
            self.risk_weights.update(new_weights)
            self.logger.info("风险权重已更新")
            return True
            
        except Exception as e:
            self.logger.error(f"更新风险权重失败: {e}")
            return False
    
    def reset_alert_cooldowns(self) -> None:
        """重置所有警报冷却时间"""
        self.last_alert_times.clear()
        self.logger.info("警报冷却时间已重置")
    
    def clear_risk_history(self) -> None:
        """清空风险评估历史记录"""
        self.risk_history.clear()
        self.logger.info("风险评估历史记录已清空")