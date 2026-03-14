"""
YOLO目标检测器实现

基于Ultralytics YOLO实现人员、灶台、火焰检测功能。
支持多种YOLO模型，提供高精度的实时目标检测。
"""

import os
import time
import logging
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
import cv2
from ultralytics import YOLO
from pathlib import Path

from ..core.interfaces import (
    IObjectDetector, DetectionResult, DetectionType, BoundingBox
)
from ..utils.logger import get_logger
from .yolo_config_manager import get_yolo_config_manager
from .detection_post_processor import DetectionPostProcessor


class YOLODetector(IObjectDetector):
    """
    YOLO目标检测器
    
    实现基于YOLO的人员、灶台、火焰检测功能。
    支持预训练模型和自定义训练模型。
    """
    
    # YOLO类别映射到系统检测类型
    CLASS_MAPPING = {
        'person': DetectionType.PERSON,
        'fire': DetectionType.FLAME,
        'stove': DetectionType.STOVE,
        'oven': DetectionType.STOVE,  # 烤箱也算作灶台
        'microwave': DetectionType.STOVE,  # 微波炉也算作灶台
    }
    
    def __init__(self, 
                 model_path: Optional[str] = None,
                 confidence_threshold: Optional[float] = None,
                 iou_threshold: Optional[float] = None,
                 device: Optional[str] = None,
                 config_path: Optional[str] = None,
                 enable_post_processing: bool = True):
        """
        初始化YOLO检测器
        
        Args:
            model_path: YOLO模型文件路径，None则使用配置文件中的路径
            confidence_threshold: 置信度阈值，None则使用配置文件中的值
            iou_threshold: IoU阈值用于NMS，None则使用配置文件中的值
            device: 推理设备，None则使用配置文件中的值
            config_path: 配置文件路径
            enable_post_processing: 是否启用后处理
        """
        self.logger = get_logger(__name__)
        
        # 加载配置
        self.config_manager = get_yolo_config_manager(config_path)
        
        # 使用参数或配置文件中的值
        self.model_path = model_path or self.config_manager.get_model_path()
        self.confidence_threshold = confidence_threshold or self.config_manager.get_confidence_threshold()
        self.iou_threshold = iou_threshold or self.config_manager.get_iou_threshold()
        self.device = device or self.config_manager.get_device()
        
        # 从配置获取其他参数
        self.min_box_size = self.config_manager.get_min_box_size()
        self.class_mapping_config = self.config_manager.get_class_mapping()
        
        self.model: Optional[YOLO] = None
        self.is_loaded = False
        
        # 初始化后处理器
        self.enable_post_processing = enable_post_processing
        if enable_post_processing:
            self.post_processor = DetectionPostProcessor(
                confidence_threshold=self.confidence_threshold,
                nms_threshold=self.iou_threshold,
                min_box_size=self.min_box_size
            )
        else:
            self.post_processor = None
        
        # 性能统计
        self.detection_count = 0
        self.total_inference_time = 0.0
        
        # 自动加载模型
        if self.model_path:
            self.load_model(self.model_path)
        else:
            self._load_default_model()
    
    def _load_default_model(self) -> bool:
        """加载默认预训练模型"""
        try:
            # 优先使用项目中的自定义模型
            project_models = [
                "yolo/yolo11n.pt",
                "yolo/yolov8n.pt"
            ]
            
            for model_path in project_models:
                if os.path.exists(model_path):
                    self.logger.info(f"使用项目模型: {model_path}")
                    return self.load_model(model_path)
            
            # 使用Ultralytics预训练模型
            self.logger.info("使用YOLO预训练模型: yolo11n.pt")
            return self.load_model("yolo11n.pt")
            
        except Exception as e:
            self.logger.error(f"加载默认模型失败: {e}")
            return False
    
    def load_model(self, model_path: str) -> bool:
        """
        加载YOLO模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            bool: 加载是否成功
        """
        try:
            self.logger.info(f"正在加载YOLO模型: {model_path}")
            
            # 检查模型文件是否存在
            if not model_path.endswith('.pt') and os.path.exists(model_path):
                if not os.path.exists(model_path):
                    self.logger.error(f"模型文件不存在: {model_path}")
                    return False
            
            # 加载模型
            self.model = YOLO(model_path)
            
            # 设置设备
            if self.device == 'auto':
                import torch
                device = 'cuda' if torch.cuda.is_available() else 'cpu'
            else:
                device = self.device
                
            self.model.to(device)
            self.logger.info(f"模型已加载到设备: {device}")
            
            # 获取模型信息
            model_info = self._get_model_info()
            self.logger.info(f"模型信息: {model_info}")
            
            self.model_path = model_path
            self.is_loaded = True
            
            return True
            
        except Exception as e:
            self.logger.error(f"加载模型失败: {e}")
            self.is_loaded = False
            return False
    
    def _get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        if not self.model:
            return {}
            
        try:
            names = self.model.names if hasattr(self.model, 'names') else {}
            return {
                'model_path': self.model_path,
                'class_names': names,
                'num_classes': len(names),
                'supported_types': [dt.value for dt in DetectionType if any(
                    cls_name in names.values() for cls_name in self.CLASS_MAPPING.keys()
                )]
            }
        except Exception as e:
            self.logger.warning(f"获取模型信息失败: {e}")
            return {}
    
    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """
        执行目标检测
        
        Args:
            frame: 输入图像帧
            
        Returns:
            List[DetectionResult]: 检测结果列表
        """
        if not self.is_loaded or self.model is None:
            self.logger.warning("模型未加载，无法执行检测")
            return []
        
        try:
            start_time = time.time()
            
            # 执行推理
            results = self.model(
                frame,
                conf=self.confidence_threshold,
                iou=self.iou_threshold,
                verbose=False
            )
            
            # 解析检测结果
            detections = self._parse_results(results, frame.shape)
            
            # 应用后处理（如果启用）
            if self.enable_post_processing and self.post_processor:
                detections = self.post_processor.process_detections(
                    detections, 
                    frame_shape=(frame.shape[0], frame.shape[1])
                )
            
            # 更新性能统计
            inference_time = time.time() - start_time
            self.detection_count += 1
            self.total_inference_time += inference_time
            
            if self.detection_count % 100 == 0:  # 每100次检测记录一次性能
                avg_time = self.total_inference_time / self.detection_count
                self.logger.debug(f"平均推理时间: {avg_time:.3f}s, FPS: {1/avg_time:.1f}")
            
            return detections
            
        except Exception as e:
            self.logger.error(f"检测过程出错: {e}")
            return []
    
    def _parse_results(self, results, frame_shape: Tuple[int, int, int]) -> List[DetectionResult]:
        """
        解析YOLO检测结果
        
        Args:
            results: YOLO检测结果
            frame_shape: 图像帧形状 (H, W, C)
            
        Returns:
            List[DetectionResult]: 解析后的检测结果
        """
        detections = []
        current_time = time.time()
        
        try:
            for result in results:
                if result.boxes is None:
                    continue
                    
                boxes = result.boxes
                
                for i in range(len(boxes)):
                    # 获取边界框坐标
                    x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
                    confidence = float(boxes.conf[i].cpu().numpy())
                    class_id = int(boxes.cls[i].cpu().numpy())
                    
                    # 获取类别名称
                    class_name = self.model.names.get(class_id, 'unknown')
                    
                    # 映射到系统检测类型
                    detection_type = self._map_class_to_detection_type(class_name)
                    if detection_type is None:
                        continue  # 跳过不支持的类别
                    
                    # 确保边界框在图像范围内
                    x1 = max(0, int(x1))
                    y1 = max(0, int(y1))
                    x2 = min(frame_shape[1], int(x2))
                    y2 = min(frame_shape[0], int(y2))
                    
                    width = x2 - x1
                    height = y2 - y1
                    
                    # 过滤过小的检测框
                    if width < self.min_box_size or height < self.min_box_size:
                        continue
                    
                    # 创建边界框
                    bbox = BoundingBox(
                        x=x1,
                        y=y1,
                        width=width,
                        height=height,
                        confidence=confidence
                    )
                    
                    # 创建检测结果
                    detection = DetectionResult(
                        detection_type=detection_type,
                        bbox=bbox,
                        timestamp=current_time,
                        frame_id=self.detection_count,
                        additional_data={
                            'class_name': class_name,
                            'class_id': class_id,
                            'model_confidence': confidence
                        }
                    )
                    
                    detections.append(detection)
            
            # 按置信度排序
            detections.sort(key=lambda x: x.bbox.confidence, reverse=True)
            
            self.logger.debug(f"检测到 {len(detections)} 个目标")
            
        except Exception as e:
            self.logger.error(f"解析检测结果失败: {e}")
        
        return detections
    
    def _map_class_to_detection_type(self, class_name: str) -> Optional[DetectionType]:
        """
        将YOLO类别名称映射到系统检测类型
        
        Args:
            class_name: YOLO类别名称
            
        Returns:
            Optional[DetectionType]: 对应的检测类型，None表示不支持
        """
        class_name_lower = class_name.lower()
        
        # 使用配置文件中的映射
        for yolo_class, detection_type_str in self.class_mapping_config.items():
            if yolo_class.lower() == class_name_lower:
                # 将字符串转换为DetectionType枚举
                if detection_type_str == "person":
                    return DetectionType.PERSON
                elif detection_type_str == "stove":
                    return DetectionType.STOVE
                elif detection_type_str == "flame":
                    return DetectionType.FLAME
        
        # 回退到原有的映射逻辑
        for yolo_class, detection_type in self.CLASS_MAPPING.items():
            if yolo_class in class_name_lower or class_name_lower in yolo_class:
                return detection_type
        
        return None
    
    def set_confidence_threshold(self, threshold: float) -> None:
        """
        设置置信度阈值
        
        Args:
            threshold: 置信度阈值 (0.0-1.0)
        """
        if 0.0 <= threshold <= 1.0:
            self.confidence_threshold = threshold
            # 同时更新后处理器的阈值
            if self.post_processor:
                self.post_processor.set_confidence_threshold(threshold)
            self.logger.info(f"置信度阈值已设置为: {threshold}")
        else:
            self.logger.warning(f"无效的置信度阈值: {threshold}")
    
    def set_iou_threshold(self, threshold: float) -> None:
        """
        设置IoU阈值
        
        Args:
            threshold: IoU阈值 (0.0-1.0)
        """
        if 0.0 <= threshold <= 1.0:
            self.iou_threshold = threshold
            # 同时更新后处理器的NMS阈值
            if self.post_processor:
                self.post_processor.set_nms_threshold(threshold)
            self.logger.info(f"IoU阈值已设置为: {threshold}")
        else:
            self.logger.warning(f"无效的IoU阈值: {threshold}")
    
    def set_class_confidence_threshold(self, detection_type: DetectionType, threshold: float) -> None:
        """
        设置特定类别的置信度阈值
        
        Args:
            detection_type: 检测类型
            threshold: 置信度阈值 (0.0-1.0)
        """
        if self.post_processor:
            self.post_processor.set_confidence_threshold(threshold, detection_type)
        else:
            self.logger.warning("后处理器未启用，无法设置类别特定阈值")
    
    def enable_post_processing_mode(self, enable: bool = True) -> None:
        """
        启用或禁用后处理
        
        Args:
            enable: 是否启用后处理
        """
        self.enable_post_processing = enable
        if enable and self.post_processor is None:
            self.post_processor = DetectionPostProcessor(
                confidence_threshold=self.confidence_threshold,
                nms_threshold=self.iou_threshold,
                min_box_size=self.min_box_size
            )
        self.logger.info(f"后处理已{'启用' if enable else '禁用'}")
    
    def optimize_for_realtime(self) -> None:
        """
        优化实时处理性能
        """
        if self.post_processor:
            self.post_processor.optimize_for_realtime()
        self.logger.info("已优化为实时处理模式")
    
    def optimize_for_accuracy(self) -> None:
        """
        优化检测准确性
        """
        if self.post_processor:
            self.post_processor.optimize_for_accuracy()
        self.logger.info("已优化为高精度模式")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """
        获取性能统计信息
        
        Returns:
            Dict[str, Any]: 性能统计数据
        """
        if self.detection_count == 0:
            base_stats = {
                'detection_count': 0,
                'average_inference_time': 0.0,
                'average_fps': 0.0
            }
        else:
            avg_time = self.total_inference_time / self.detection_count
            base_stats = {
                'detection_count': self.detection_count,
                'total_inference_time': self.total_inference_time,
                'average_inference_time': avg_time,
                'average_fps': 1.0 / avg_time if avg_time > 0 else 0.0,
            }
        
        base_stats.update({
            'confidence_threshold': self.confidence_threshold,
            'iou_threshold': self.iou_threshold,
            'model_path': self.model_path,
            'is_loaded': self.is_loaded,
            'post_processing_enabled': self.enable_post_processing
        })
        
        # 添加后处理器统计信息
        if self.post_processor:
            post_stats = self.post_processor.get_performance_stats()
            base_stats['post_processor_stats'] = post_stats
        
        return base_stats
    
    def reset_stats(self) -> None:
        """重置性能统计"""
        self.detection_count = 0
        self.total_inference_time = 0.0
        self.logger.info("性能统计已重置")
    
    def visualize_detections(self, 
                           frame: np.ndarray, 
                           detections: List[DetectionResult],
                           show_confidence: bool = True,
                           show_labels: bool = True) -> np.ndarray:
        """
        在图像上可视化检测结果
        
        Args:
            frame: 原始图像帧
            detections: 检测结果列表
            show_confidence: 是否显示置信度
            show_labels: 是否显示标签
            
        Returns:
            np.ndarray: 带有检测框的图像
        """
        result_frame = frame.copy()
        
        # 定义颜色映射（使用配置文件中的颜色）
        config_colors = self.config_manager.get_visualization_colors()
        colors = {
            DetectionType.PERSON: tuple(config_colors.get('person', [0, 255, 0])),
            DetectionType.STOVE: tuple(config_colors.get('stove', [255, 0, 0])),
            DetectionType.FLAME: tuple(config_colors.get('flame', [0, 0, 255])),
        }
        
        for detection in detections:
            bbox = detection.bbox
            color = colors.get(detection.detection_type, (128, 128, 128))
            
            # 绘制边界框
            cv2.rectangle(
                result_frame,
                (bbox.x, bbox.y),
                (bbox.x + bbox.width, bbox.y + bbox.height),
                color,
                2
            )
            
            # 绘制标签和置信度
            if show_labels or show_confidence:
                label_parts = []
                if show_labels:
                    label_parts.append(detection.detection_type.value)
                if show_confidence:
                    label_parts.append(f"{bbox.confidence:.2f}")
                
                label = " ".join(label_parts)
                
                # 计算文本尺寸
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                thickness = 1
                (text_width, text_height), baseline = cv2.getTextSize(
                    label, font, font_scale, thickness
                )
                
                # 绘制文本背景
                cv2.rectangle(
                    result_frame,
                    (bbox.x, bbox.y - text_height - baseline - 5),
                    (bbox.x + text_width, bbox.y),
                    color,
                    -1
                )
                
                # 绘制文本
                cv2.putText(
                    result_frame,
                    label,
                    (bbox.x, bbox.y - baseline - 2),
                    font,
                    font_scale,
                    (255, 255, 255),
                    thickness
                )
        
        return result_frame
    
    def __del__(self):
        """析构函数"""
        if hasattr(self, 'logger'):
            self.logger.info("YOLO检测器已销毁")