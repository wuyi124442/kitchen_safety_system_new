"""
MediaPipe姿态分析器

基于MediaPipe实现人体关键点检测和跌倒识别功能。
"""

import cv2
import numpy as np
import mediapipe as mp
import time
from typing import List, Optional, Tuple
from dataclasses import dataclass

from ..core.interfaces import IPoseAnalyzer, PoseResult, PoseKeypoint, BoundingBox
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PoseAnalyzer(IPoseAnalyzer):
    """
    MediaPipe姿态分析器
    
    实现人体关键点检测、姿态数据预处理和标准化、跌倒检测等功能。
    """
    
    def __init__(self, 
                 min_detection_confidence: float = 0.5,
                 min_tracking_confidence: float = 0.5,
                 model_complexity: int = 1):
        """
        初始化姿态分析器
        
        Args:
            min_detection_confidence: 最小检测置信度
            min_tracking_confidence: 最小跟踪置信度  
            model_complexity: 模型复杂度 (0, 1, 2)
        """
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.model_complexity = model_complexity
        
        # 初始化MediaPipe Pose (使用新版本API)
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            # 创建PoseLandmarker选项 - 使用默认模型
            base_options = python.BaseOptions()
            options = vision.PoseLandmarkerOptions(
                base_options=base_options,
                output_segmentation_masks=False,
                min_pose_detection_confidence=min_detection_confidence,
                min_pose_presence_confidence=min_tracking_confidence,
                min_tracking_confidence=min_tracking_confidence
            )
            
            self.pose_landmarker = vision.PoseLandmarker.create_from_options(options)
            logger.info("MediaPipe PoseLandmarker initialized successfully")
            
        except Exception as e:
            logger.warning(f"Failed to initialize MediaPipe with default model: {e}")
            # 创建一个模拟的pose_landmarker用于测试
            self.pose_landmarker = None
            logger.info("Using mock pose analyzer for testing")
        
        # 关键点索引映射 (MediaPipe Pose landmarks)
        self.keypoint_indices = {
            'nose': 0,
            'left_eye_inner': 1, 'left_eye': 2, 'left_eye_outer': 3,
            'right_eye_inner': 4, 'right_eye': 5, 'right_eye_outer': 6,
            'left_ear': 7, 'right_ear': 8,
            'mouth_left': 9, 'mouth_right': 10,
            'left_shoulder': 11, 'right_shoulder': 12,
            'left_elbow': 13, 'right_elbow': 14,
            'left_wrist': 15, 'right_wrist': 16,
            'left_pinky': 17, 'right_pinky': 18,
            'left_index': 19, 'right_index': 20,
            'left_thumb': 21, 'right_thumb': 22,
            'left_hip': 23, 'right_hip': 24,
            'left_knee': 25, 'right_knee': 26,
            'left_ankle': 27, 'right_ankle': 28,
            'left_heel': 29, 'right_heel': 30,
            'left_foot_index': 31, 'right_foot_index': 32
        }
        
        # 跌倒检测参数
        self.fall_detection_config = {
            'head_hip_ratio_threshold': 0.3,  # 头部相对于臀部的高度比例阈值
            'body_angle_threshold': 45,       # 身体角度阈值 (度)
            'hip_ground_ratio_threshold': 0.7, # 臀部相对于地面的高度比例阈值
            'confidence_threshold': 0.6       # 关键点置信度阈值
        }
        
        logger.info(f"PoseAnalyzer initialized with confidence={min_detection_confidence}, "
                   f"tracking={min_tracking_confidence}, complexity={model_complexity}")
    
    def analyze_pose(self, frame: np.ndarray, person_bbox: BoundingBox) -> PoseResult:
        """
        分析人员姿态
        
        Args:
            frame: 输入视频帧
            person_bbox: 人员边界框
            
        Returns:
            PoseResult: 姿态分析结果
        """
        try:
            # 提取人员区域
            person_roi = self._extract_person_roi(frame, person_bbox)
            
            # 生成时间戳和帧ID
            timestamp = time.time()
            frame_id = int(timestamp * 1000) % 1000000  # 简单的帧ID生成
            
            # 如果MediaPipe不可用，返回空结果
            if not hasattr(self, 'pose_landmarker') or self.pose_landmarker is None:
                logger.warning("MediaPipe not available, returning empty pose result")
                return PoseResult(
                    keypoints=[],
                    timestamp=timestamp,
                    frame_id=frame_id,
                    is_fall_detected=False,
                    fall_confidence=0.0
                )
            
            # 转换为RGB格式 (MediaPipe需要RGB输入)
            rgb_frame = cv2.cvtColor(person_roi, cv2.COLOR_BGR2RGB)
            
            # 执行姿态检测 (使用新版API)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            detection_result = self.pose_landmarker.detect(mp_image)
            
            if detection_result.pose_landmarks and len(detection_result.pose_landmarks) > 0:
                # 转换关键点坐标到原始帧坐标系
                keypoints = self._convert_new_api_landmarks_to_keypoints(
                    detection_result.pose_landmarks[0], person_bbox, person_roi.shape
                )
            else:
                keypoints = []
            
            if keypoints:
                # 创建姿态结果
                pose_result = PoseResult(
                    keypoints=keypoints,
                    timestamp=timestamp,
                    frame_id=frame_id
                )
                
                # 检测跌倒状态
                pose_result.is_fall_detected = self.detect_fall(pose_result)
                pose_result.fall_confidence = self._calculate_fall_confidence(pose_result)
                
                logger.debug(f"Pose analyzed: {len(keypoints)} keypoints, "
                           f"fall_detected={pose_result.is_fall_detected}")
                
                return pose_result
            else:
                # 未检测到姿态
                logger.debug("No pose landmarks detected")
                return PoseResult(
                    keypoints=[],
                    timestamp=timestamp,
                    frame_id=frame_id,
                    is_fall_detected=False,
                    fall_confidence=0.0
                )
                
        except Exception as e:
            logger.error(f"Error in pose analysis: {e}")
            return PoseResult(
                keypoints=[],
                timestamp=time.time(),
                frame_id=0,
                is_fall_detected=False,
                fall_confidence=0.0
            )
    
    def detect_fall(self, pose_result: PoseResult) -> bool:
        """
        检测跌倒状态
        
        Args:
            pose_result: 姿态分析结果
            
        Returns:
            bool: 是否检测到跌倒
        """
        if not pose_result.keypoints or len(pose_result.keypoints) < 33:
            return False
        
        try:
            # 获取关键点
            keypoints = pose_result.keypoints
            
            # 检查关键点置信度
            if not self._check_keypoints_confidence(keypoints):
                return False
            
            # 方法1: 头部与臀部高度比例检测
            head_hip_fall = self._detect_fall_by_head_hip_ratio(keypoints)
            
            # 方法2: 身体角度检测
            body_angle_fall = self._detect_fall_by_body_angle(keypoints)
            
            # 方法3: 臀部高度检测
            hip_height_fall = self._detect_fall_by_hip_height(keypoints)
            
            # 综合判断 (至少两个方法检测到跌倒)
            fall_indicators = sum([head_hip_fall, body_angle_fall, hip_height_fall])
            is_fall = fall_indicators >= 2
            
            if is_fall:
                logger.info(f"Fall detected: head_hip={head_hip_fall}, "
                          f"body_angle={body_angle_fall}, hip_height={hip_height_fall}")
            
            return is_fall
            
        except Exception as e:
            logger.error(f"Error in fall detection: {e}")
            return False
    
    def is_normal_action(self, pose_result: PoseResult) -> bool:
        """
        判断是否为正常动作 (蹲下、弯腰等)
        
        Args:
            pose_result: 姿态分析结果
            
        Returns:
            bool: 是否为正常动作
        """
        if not pose_result.keypoints or len(pose_result.keypoints) < 33:
            return True  # 无法判断时默认为正常
        
        try:
            keypoints = pose_result.keypoints
            
            # 检查关键点置信度
            if not self._check_keypoints_confidence(keypoints):
                return True
            
            # 检测蹲下动作
            is_squatting = self._detect_squatting(keypoints)
            
            # 检测弯腰动作
            is_bending = self._detect_bending(keypoints)
            
            # 检测坐下动作
            is_sitting = self._detect_sitting(keypoints)
            
            return is_squatting or is_bending or is_sitting
            
        except Exception as e:
            logger.error(f"Error in normal action detection: {e}")
            return True
    
    def _extract_person_roi(self, frame: np.ndarray, person_bbox: BoundingBox) -> np.ndarray:
        """提取人员感兴趣区域"""
        # 添加边距以确保完整的人体
        margin = 20
        x1 = max(0, person_bbox.x - margin)
        y1 = max(0, person_bbox.y - margin)
        x2 = min(frame.shape[1], person_bbox.x + person_bbox.width + margin)
        y2 = min(frame.shape[0], person_bbox.y + person_bbox.height + margin)
        
        return frame[y1:y2, x1:x2]
    
    def _convert_new_api_landmarks_to_keypoints(self, landmarks, person_bbox: BoundingBox, 
                                              roi_shape: Tuple[int, int, int]) -> List[PoseKeypoint]:
        """将MediaPipe landmarks转换为PoseKeypoint (新版API)"""
        keypoints = []
        
        for landmark in landmarks:
            # 转换相对坐标到ROI像素坐标
            x_roi = landmark.x * roi_shape[1]
            y_roi = landmark.y * roi_shape[0]
            
            # 转换到原始帧坐标
            margin = 20
            x_frame = x_roi + max(0, person_bbox.x - margin)
            y_frame = y_roi + max(0, person_bbox.y - margin)
            
            # 新版API中visibility字段
            visibility = getattr(landmark, 'visibility', 0.8)
            
            keypoint = PoseKeypoint(
                x=x_frame,
                y=y_frame,
                confidence=visibility,
                visible=visibility > 0.5
            )
            keypoints.append(keypoint)
        
        return keypoints
    
    def _check_keypoints_confidence(self, keypoints: List[PoseKeypoint]) -> bool:
        """检查关键点置信度"""
        # 检查关键的身体部位是否可见
        key_indices = [
            self.keypoint_indices['nose'],
            self.keypoint_indices['left_shoulder'],
            self.keypoint_indices['right_shoulder'],
            self.keypoint_indices['left_hip'],
            self.keypoint_indices['right_hip']
        ]
        
        visible_count = 0
        for idx in key_indices:
            if idx < len(keypoints) and keypoints[idx].confidence > self.fall_detection_config['confidence_threshold']:
                visible_count += 1
        
        return visible_count >= 3  # 至少3个关键点可见
    
    def _detect_fall_by_head_hip_ratio(self, keypoints: List[PoseKeypoint]) -> bool:
        """通过头部与臀部高度比例检测跌倒"""
        try:
            nose_idx = self.keypoint_indices['nose']
            left_hip_idx = self.keypoint_indices['left_hip']
            right_hip_idx = self.keypoint_indices['right_hip']
            
            if (nose_idx >= len(keypoints) or 
                left_hip_idx >= len(keypoints) or 
                right_hip_idx >= len(keypoints)):
                return False
            
            nose = keypoints[nose_idx]
            left_hip = keypoints[left_hip_idx]
            right_hip = keypoints[right_hip_idx]
            
            # 计算臀部中心
            hip_center_y = (left_hip.y + right_hip.y) / 2
            
            # 计算头部相对于臀部的高度比例
            if hip_center_y > nose.y:  # 正常情况下头部应该在臀部上方
                height_ratio = (hip_center_y - nose.y) / hip_center_y
            else:
                height_ratio = 0  # 头部在臀部下方，可能是跌倒
            
            return height_ratio < self.fall_detection_config['head_hip_ratio_threshold']
            
        except Exception as e:
            logger.error(f"Error in head-hip ratio detection: {e}")
            return False
    
    def _detect_fall_by_body_angle(self, keypoints: List[PoseKeypoint]) -> bool:
        """通过身体角度检测跌倒"""
        try:
            left_shoulder_idx = self.keypoint_indices['left_shoulder']
            right_shoulder_idx = self.keypoint_indices['right_shoulder']
            left_hip_idx = self.keypoint_indices['left_hip']
            right_hip_idx = self.keypoint_indices['right_hip']
            
            if (left_shoulder_idx >= len(keypoints) or 
                right_shoulder_idx >= len(keypoints) or
                left_hip_idx >= len(keypoints) or 
                right_hip_idx >= len(keypoints)):
                return False
            
            # 计算肩部和臀部中心点
            shoulder_center = (
                (keypoints[left_shoulder_idx].x + keypoints[right_shoulder_idx].x) / 2,
                (keypoints[left_shoulder_idx].y + keypoints[right_shoulder_idx].y) / 2
            )
            hip_center = (
                (keypoints[left_hip_idx].x + keypoints[right_hip_idx].x) / 2,
                (keypoints[left_hip_idx].y + keypoints[right_hip_idx].y) / 2
            )
            
            # 计算身体轴线与垂直方向的角度
            dx = hip_center[0] - shoulder_center[0]
            dy = hip_center[1] - shoulder_center[1]
            
            if dy == 0:
                angle = 90  # 完全水平
            else:
                angle = abs(np.degrees(np.arctan(dx / dy)))
            
            return angle > self.fall_detection_config['body_angle_threshold']
            
        except Exception as e:
            logger.error(f"Error in body angle detection: {e}")
            return False
    
    def _detect_fall_by_hip_height(self, keypoints: List[PoseKeypoint]) -> bool:
        """通过臀部高度检测跌倒"""
        try:
            left_hip_idx = self.keypoint_indices['left_hip']
            right_hip_idx = self.keypoint_indices['right_hip']
            left_ankle_idx = self.keypoint_indices['left_ankle']
            right_ankle_idx = self.keypoint_indices['right_ankle']
            
            if (left_hip_idx >= len(keypoints) or 
                right_hip_idx >= len(keypoints) or
                left_ankle_idx >= len(keypoints) or 
                right_ankle_idx >= len(keypoints)):
                return False
            
            # 计算臀部和脚踝高度
            hip_y = (keypoints[left_hip_idx].y + keypoints[right_hip_idx].y) / 2
            ankle_y = (keypoints[left_ankle_idx].y + keypoints[right_ankle_idx].y) / 2
            
            # 计算臀部相对于脚踝的高度比例
            if ankle_y > hip_y:  # 正常情况下脚踝应该在臀部下方
                height_ratio = (ankle_y - hip_y) / ankle_y
            else:
                height_ratio = 0  # 臀部在脚踝下方，可能是跌倒
            
            return height_ratio < (1 - self.fall_detection_config['hip_ground_ratio_threshold'])
            
        except Exception as e:
            logger.error(f"Error in hip height detection: {e}")
            return False
    
    def _detect_squatting(self, keypoints: List[PoseKeypoint]) -> bool:
        """检测蹲下动作"""
        try:
            left_knee_idx = self.keypoint_indices['left_knee']
            right_knee_idx = self.keypoint_indices['right_knee']
            left_hip_idx = self.keypoint_indices['left_hip']
            right_hip_idx = self.keypoint_indices['right_hip']
            
            if (left_knee_idx >= len(keypoints) or 
                right_knee_idx >= len(keypoints) or
                left_hip_idx >= len(keypoints) or 
                right_hip_idx >= len(keypoints)):
                return False
            
            # 计算膝盖和臀部的高度差
            knee_y = (keypoints[left_knee_idx].y + keypoints[right_knee_idx].y) / 2
            hip_y = (keypoints[left_hip_idx].y + keypoints[right_hip_idx].y) / 2
            
            # 蹲下时膝盖和臀部高度接近
            height_diff = abs(knee_y - hip_y)
            return height_diff < 50  # 像素阈值，可调整
            
        except Exception as e:
            logger.error(f"Error in squatting detection: {e}")
            return False
    
    def _detect_bending(self, keypoints: List[PoseKeypoint]) -> bool:
        """检测弯腰动作"""
        try:
            nose_idx = self.keypoint_indices['nose']
            left_hip_idx = self.keypoint_indices['left_hip']
            right_hip_idx = self.keypoint_indices['right_hip']
            
            if (nose_idx >= len(keypoints) or 
                left_hip_idx >= len(keypoints) or 
                right_hip_idx >= len(keypoints)):
                return False
            
            nose = keypoints[nose_idx]
            hip_center_x = (keypoints[left_hip_idx].x + keypoints[right_hip_idx].x) / 2
            
            # 弯腰时头部会向前倾斜
            horizontal_distance = abs(nose.x - hip_center_x)
            return horizontal_distance > 80  # 像素阈值，可调整
            
        except Exception as e:
            logger.error(f"Error in bending detection: {e}")
            return False
    
    def _detect_sitting(self, keypoints: List[PoseKeypoint]) -> bool:
        """检测坐下动作"""
        try:
            left_hip_idx = self.keypoint_indices['left_hip']
            right_hip_idx = self.keypoint_indices['right_hip']
            left_knee_idx = self.keypoint_indices['left_knee']
            right_knee_idx = self.keypoint_indices['right_knee']
            
            if (left_hip_idx >= len(keypoints) or 
                right_hip_idx >= len(keypoints) or
                left_knee_idx >= len(keypoints) or 
                right_knee_idx >= len(keypoints)):
                return False
            
            # 坐下时臀部和膝盖高度相近，且膝盖可能高于臀部
            hip_y = (keypoints[left_hip_idx].y + keypoints[right_hip_idx].y) / 2
            knee_y = (keypoints[left_knee_idx].y + keypoints[right_knee_idx].y) / 2
            
            # 坐下时膝盖通常与臀部同高或略高
            return knee_y <= hip_y + 30  # 允许一定的高度差
            
        except Exception as e:
            logger.error(f"Error in sitting detection: {e}")
            return False
    
    def _calculate_fall_confidence(self, pose_result: PoseResult) -> float:
        """计算跌倒置信度"""
        if not pose_result.keypoints or not pose_result.is_fall_detected:
            return 0.0
        
        try:
            keypoints = pose_result.keypoints
            
            # 基于多个指标计算置信度
            confidence_factors = []
            
            # 1. 头部臀部比例因子
            head_hip_factor = self._get_head_hip_confidence_factor(keypoints)
            confidence_factors.append(head_hip_factor)
            
            # 2. 身体角度因子
            angle_factor = self._get_body_angle_confidence_factor(keypoints)
            confidence_factors.append(angle_factor)
            
            # 3. 关键点可见性因子
            visibility_factor = self._get_visibility_confidence_factor(keypoints)
            confidence_factors.append(visibility_factor)
            
            # 计算加权平均置信度
            weights = [0.4, 0.4, 0.2]  # 头部臀部比例和身体角度权重更高
            confidence = sum(f * w for f, w in zip(confidence_factors, weights))
            
            return min(1.0, max(0.0, confidence))
            
        except Exception as e:
            logger.error(f"Error calculating fall confidence: {e}")
            return 0.0
    
    def _get_head_hip_confidence_factor(self, keypoints: List[PoseKeypoint]) -> float:
        """获取头部臀部比例置信度因子"""
        try:
            nose_idx = self.keypoint_indices['nose']
            left_hip_idx = self.keypoint_indices['left_hip']
            right_hip_idx = self.keypoint_indices['right_hip']
            
            if (nose_idx >= len(keypoints) or 
                left_hip_idx >= len(keypoints) or 
                right_hip_idx >= len(keypoints)):
                return 0.0
            
            nose = keypoints[nose_idx]
            hip_center_y = (keypoints[left_hip_idx].y + keypoints[right_hip_idx].y) / 2
            
            if hip_center_y > nose.y:
                height_ratio = (hip_center_y - nose.y) / hip_center_y
            else:
                height_ratio = 0
            
            # 转换为置信度 (比例越小，跌倒置信度越高)
            threshold = self.fall_detection_config['head_hip_ratio_threshold']
            if height_ratio < threshold:
                return 1.0 - (height_ratio / threshold)
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _get_body_angle_confidence_factor(self, keypoints: List[PoseKeypoint]) -> float:
        """获取身体角度置信度因子"""
        try:
            left_shoulder_idx = self.keypoint_indices['left_shoulder']
            right_shoulder_idx = self.keypoint_indices['right_shoulder']
            left_hip_idx = self.keypoint_indices['left_hip']
            right_hip_idx = self.keypoint_indices['right_hip']
            
            if (left_shoulder_idx >= len(keypoints) or 
                right_shoulder_idx >= len(keypoints) or
                left_hip_idx >= len(keypoints) or 
                right_hip_idx >= len(keypoints)):
                return 0.0
            
            shoulder_center = (
                (keypoints[left_shoulder_idx].x + keypoints[right_shoulder_idx].x) / 2,
                (keypoints[left_shoulder_idx].y + keypoints[right_shoulder_idx].y) / 2
            )
            hip_center = (
                (keypoints[left_hip_idx].x + keypoints[right_hip_idx].x) / 2,
                (keypoints[left_hip_idx].y + keypoints[right_hip_idx].y) / 2
            )
            
            dx = hip_center[0] - shoulder_center[0]
            dy = hip_center[1] - shoulder_center[1]
            
            if dy == 0:
                angle = 90
            else:
                angle = abs(np.degrees(np.arctan(dx / dy)))
            
            # 转换为置信度 (角度越大，跌倒置信度越高)
            threshold = self.fall_detection_config['body_angle_threshold']
            if angle > threshold:
                return min(1.0, (angle - threshold) / (90 - threshold))
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def _get_visibility_confidence_factor(self, keypoints: List[PoseKeypoint]) -> float:
        """获取关键点可见性置信度因子"""
        try:
            key_indices = [
                self.keypoint_indices['nose'],
                self.keypoint_indices['left_shoulder'],
                self.keypoint_indices['right_shoulder'],
                self.keypoint_indices['left_hip'],
                self.keypoint_indices['right_hip']
            ]
            
            total_confidence = 0.0
            valid_count = 0
            
            for idx in key_indices:
                if idx < len(keypoints):
                    total_confidence += keypoints[idx].confidence
                    valid_count += 1
            
            if valid_count > 0:
                return total_confidence / valid_count
            else:
                return 0.0
                
        except Exception:
            return 0.0
    
    def __del__(self):
        """析构函数，清理资源"""
        try:
            if hasattr(self, 'pose_landmarker') and self.pose_landmarker is not None:
                self.pose_landmarker.close()
        except Exception as e:
            logger.debug(f"Error during cleanup: {e}")