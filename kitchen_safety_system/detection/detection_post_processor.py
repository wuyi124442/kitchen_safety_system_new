"""
检测结果后处理器

实现检测结果的后处理功能，包括边界框过滤、非极大值抑制(NMS)、
置信度阈值调整等功能，提升检测质量和准确性。
"""

import time
import logging
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import cv2

from ..core.interfaces import DetectionResult, DetectionType, BoundingBox
from ..utils.logger import get_logger


class DetectionPostProcessor:
    """
    检测结果后处理器
    
    提供检测结果的后处理功能，包括：
    - 边界框过滤（尺寸、位置、置信度）
    - 非极大值抑制(NMS)
    - 置信度阈值动态调整
    - 检测结果优化和去重
    """
    
    def __init__(self,
                 confidence_threshold: float = 0.5,
                 nms_threshold: float = 0.45,
                 min_box_size: int = 20,
                 max_detections: int = 100,
                 class_specific_nms: bool = True):
        """
        初始化后处理器
        
        Args:
            confidence_threshold: 置信度阈值
            nms_threshold: NMS IoU阈值
            min_box_size: 最小边界框尺寸
            max_detections: 最大检测数量
            class_specific_nms: 是否按类别进行NMS
        """
        self.logger = get_logger(__name__)
        
        self.confidence_threshold = confidence_threshold
        self.nms_threshold = nms_threshold
        self.min_box_size = min_box_size
        self.max_detections = max_detections
        self.class_specific_nms = class_specific_nms
        
        # 性能统计
        self.processing_count = 0
        self.total_processing_time = 0.0
        
        # 类别特定的阈值
        self.class_thresholds = {
            DetectionType.PERSON: 0.5,
            DetectionType.STOVE: 0.6,
            DetectionType.FLAME: 0.7
        }
        
        self.logger.info(f"检测后处理器已初始化 - 置信度阈值: {confidence_threshold}, NMS阈值: {nms_threshold}")
    
    def process_detections(self, 
                          detections: List[DetectionResult],
                          frame_shape: Optional[Tuple[int, int]] = None) -> List[DetectionResult]:
        """
        处理检测结果
        
        Args:
            detections: 原始检测结果列表
            frame_shape: 图像帧形状 (height, width)
            
        Returns:
            List[DetectionResult]: 处理后的检测结果
        """
        if not detections:
            return []
        
        start_time = time.time()
        
        try:
            # 1. 置信度过滤
            filtered_detections = self._filter_by_confidence(detections)
            
            # 2. 边界框尺寸过滤
            filtered_detections = self._filter_by_size(filtered_detections)
            
            # 3. 边界框位置过滤（确保在图像范围内）
            if frame_shape:
                filtered_detections = self._filter_by_position(filtered_detections, frame_shape)
            
            # 4. 非极大值抑制
            nms_detections = self._apply_nms(filtered_detections)
            
            # 5. 限制最大检测数量
            final_detections = self._limit_detections(nms_detections)
            
            # 6. 更新位置信息（需求2.5）
            self._update_position_info(final_detections)
            
            # 更新性能统计
            processing_time = time.time() - start_time
            self.processing_count += 1
            self.total_processing_time += processing_time
            
            self.logger.debug(f"后处理完成: {len(detections)} -> {len(final_detections)} 个检测结果")
            
            return final_detections
            
        except Exception as e:
            self.logger.error(f"检测结果后处理失败: {e}")
            return detections  # 返回原始结果作为备选
    
    def _filter_by_confidence(self, detections: List[DetectionResult]) -> List[DetectionResult]:
        """
        按置信度过滤检测结果
        
        Args:
            detections: 检测结果列表
            
        Returns:
            List[DetectionResult]: 过滤后的检测结果
        """
        filtered = []
        
        for detection in detections:
            # 使用类别特定的阈值
            threshold = self.class_thresholds.get(
                detection.detection_type, 
                self.confidence_threshold
            )
            
            if detection.bbox.confidence >= threshold:
                filtered.append(detection)
        
        self.logger.debug(f"置信度过滤: {len(detections)} -> {len(filtered)}")
        return filtered
    
    def _filter_by_size(self, detections: List[DetectionResult]) -> List[DetectionResult]:
        """
        按边界框尺寸过滤检测结果
        
        Args:
            detections: 检测结果列表
            
        Returns:
            List[DetectionResult]: 过滤后的检测结果
        """
        filtered = []
        
        for detection in detections:
            bbox = detection.bbox
            
            # 检查最小尺寸
            if bbox.width >= self.min_box_size and bbox.height >= self.min_box_size:
                # 检查长宽比（避免过于细长的框）
                aspect_ratio = max(bbox.width, bbox.height) / min(bbox.width, bbox.height)
                if aspect_ratio <= 10.0:  # 最大长宽比限制
                    filtered.append(detection)
        
        self.logger.debug(f"尺寸过滤: {len(detections)} -> {len(filtered)}")
        return filtered
    
    def _filter_by_position(self, 
                           detections: List[DetectionResult], 
                           frame_shape: Tuple[int, int]) -> List[DetectionResult]:
        """
        按位置过滤检测结果（确保边界框在图像范围内）
        
        Args:
            detections: 检测结果列表
            frame_shape: 图像形状 (height, width)
            
        Returns:
            List[DetectionResult]: 过滤后的检测结果
        """
        filtered = []
        height, width = frame_shape
        
        for detection in detections:
            bbox = detection.bbox
            
            # 修正边界框坐标
            x1 = max(0, bbox.x)
            y1 = max(0, bbox.y)
            x2 = min(width, bbox.x + bbox.width)
            y2 = min(height, bbox.y + bbox.height)
            
            # 检查修正后的边界框是否有效
            new_width = x2 - x1
            new_height = y2 - y1
            
            if new_width >= self.min_box_size and new_height >= self.min_box_size:
                # 更新边界框
                detection.bbox = BoundingBox(
                    x=x1,
                    y=y1,
                    width=new_width,
                    height=new_height,
                    confidence=bbox.confidence
                )
                filtered.append(detection)
        
        self.logger.debug(f"位置过滤: {len(detections)} -> {len(filtered)}")
        return filtered
    
    def _apply_nms(self, detections: List[DetectionResult]) -> List[DetectionResult]:
        """
        应用非极大值抑制
        
        Args:
            detections: 检测结果列表
            
        Returns:
            List[DetectionResult]: NMS后的检测结果
        """
        if len(detections) <= 1:
            return detections
        
        if self.class_specific_nms:
            # 按类别分别进行NMS
            nms_results = []
            for detection_type in DetectionType:
                type_detections = [d for d in detections if d.detection_type == detection_type]
                if type_detections:
                    nms_results.extend(self._nms_single_class(type_detections))
            return nms_results
        else:
            # 对所有检测结果统一进行NMS
            return self._nms_single_class(detections)
    
    def _nms_single_class(self, detections: List[DetectionResult]) -> List[DetectionResult]:
        """
        对单一类别进行NMS
        
        Args:
            detections: 同一类别的检测结果列表
            
        Returns:
            List[DetectionResult]: NMS后的检测结果
        """
        if len(detections) <= 1:
            return detections
        
        # 准备OpenCV NMS所需的数据
        boxes = []
        scores = []
        
        for detection in detections:
            bbox = detection.bbox
            boxes.append([bbox.x, bbox.y, bbox.x + bbox.width, bbox.y + bbox.height])
            scores.append(bbox.confidence)
        
        boxes = np.array(boxes, dtype=np.float32)
        scores = np.array(scores, dtype=np.float32)
        
        # 执行NMS
        indices = cv2.dnn.NMSBoxes(
            boxes.tolist(),
            scores.tolist(),
            score_threshold=0.0,  # 已经过置信度过滤
            nms_threshold=self.nms_threshold
        )
        
        # 提取保留的检测结果
        if len(indices) > 0:
            indices = indices.flatten()
            nms_detections = [detections[i] for i in indices]
        else:
            nms_detections = []
        
        self.logger.debug(f"NMS处理: {len(detections)} -> {len(nms_detections)}")
        return nms_detections
    
    def _limit_detections(self, detections: List[DetectionResult]) -> List[DetectionResult]:
        """
        限制检测结果数量
        
        Args:
            detections: 检测结果列表
            
        Returns:
            List[DetectionResult]: 限制数量后的检测结果
        """
        if len(detections) <= self.max_detections:
            return detections
        
        # 按置信度排序，保留置信度最高的检测结果
        sorted_detections = sorted(
            detections, 
            key=lambda x: x.bbox.confidence, 
            reverse=True
        )
        
        limited_detections = sorted_detections[:self.max_detections]
        self.logger.debug(f"数量限制: {len(detections)} -> {len(limited_detections)}")
        
        return limited_detections
    
    def _update_position_info(self, detections: List[DetectionResult]) -> None:
        """
        更新目标位置信息（需求2.5）
        
        Args:
            detections: 检测结果列表
        """
        current_time = time.time()
        
        for detection in detections:
            # 更新时间戳
            detection.timestamp = current_time
            
            # 添加位置相关的额外信息
            if detection.additional_data is None:
                detection.additional_data = {}
            
            # 添加中心点坐标
            center_x, center_y = detection.bbox.center
            detection.additional_data.update({
                'center_x': center_x,
                'center_y': center_y,
                'area': detection.bbox.area,
                'processed_timestamp': current_time
            })
    
    def set_confidence_threshold(self, threshold: float, detection_type: Optional[DetectionType] = None) -> None:
        """
        设置置信度阈值
        
        Args:
            threshold: 置信度阈值 (0.0-1.0)
            detection_type: 特定检测类型，None表示设置全局阈值
        """
        if not 0.0 <= threshold <= 1.0:
            self.logger.warning(f"无效的置信度阈值: {threshold}")
            return
        
        if detection_type:
            self.class_thresholds[detection_type] = threshold
            self.logger.info(f"{detection_type.value}类别置信度阈值已设置为: {threshold}")
        else:
            self.confidence_threshold = threshold
            self.logger.info(f"全局置信度阈值已设置为: {threshold}")
    
    def set_nms_threshold(self, threshold: float) -> None:
        """
        设置NMS阈值
        
        Args:
            threshold: NMS IoU阈值 (0.0-1.0)
        """
        if 0.0 <= threshold <= 1.0:
            self.nms_threshold = threshold
            self.logger.info(f"NMS阈值已设置为: {threshold}")
        else:
            self.logger.warning(f"无效的NMS阈值: {threshold}")
    
    def set_min_box_size(self, size: int) -> None:
        """
        设置最小边界框尺寸
        
        Args:
            size: 最小边界框尺寸（像素）
        """
        if size > 0:
            self.min_box_size = size
            self.logger.info(f"最小边界框尺寸已设置为: {size}")
        else:
            self.logger.warning(f"无效的边界框尺寸: {size}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            Dict[str, Any]: 性能统计数据
        """
        if self.processing_count == 0:
            return {
                'processing_count': 0,
                'average_processing_time': 0.0,
                'total_processing_time': 0.0
            }
        
        avg_time = self.total_processing_time / self.processing_count
        return {
            'processing_count': self.processing_count,
            'total_processing_time': self.total_processing_time,
            'average_processing_time': avg_time,
            'confidence_threshold': self.confidence_threshold,
            'nms_threshold': self.nms_threshold,
            'min_box_size': self.min_box_size,
            'max_detections': self.max_detections,
            'class_specific_nms': self.class_specific_nms,
            'class_thresholds': {k.value: v for k, v in self.class_thresholds.items()}
        }
    
    def reset_stats(self) -> None:
        """重置性能统计"""
        self.processing_count = 0
        self.total_processing_time = 0.0
        self.logger.info("后处理器性能统计已重置")
    
    def optimize_for_realtime(self) -> None:
        """
        优化实时处理性能
        """
        # 调整参数以提高实时性能
        self.max_detections = min(self.max_detections, 50)  # 限制最大检测数量
        self.nms_threshold = max(self.nms_threshold, 0.4)   # 提高NMS阈值减少计算
        
        self.logger.info("已优化为实时处理模式")
    
    def optimize_for_accuracy(self) -> None:
        """
        优化检测准确性
        """
        # 调整参数以提高准确性
        self.max_detections = 100  # 允许更多检测结果
        self.nms_threshold = 0.3   # 降低NMS阈值提高精度
        
        self.logger.info("已优化为高精度模式")