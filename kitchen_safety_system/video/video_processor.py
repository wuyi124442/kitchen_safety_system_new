"""
视频预处理器实现

实现视频帧格式转换、尺寸调整和质量检测功能。
实现需求 1.3, 1.5。
"""

import cv2
import numpy as np
import logging
from typing import Tuple, Optional, Dict, Any
from enum import Enum

from ..core.interfaces import IVideoProcessor
from ..utils.logger import get_logger
from ..core.exception_handler import exception_handler


class VideoFormat(Enum):
    """支持的视频格式枚举"""
    BGR = "BGR"
    RGB = "RGB"
    GRAY = "GRAY"
    HSV = "HSV"
    YUV = "YUV"


class QualityLevel(Enum):
    """视频质量级别枚举"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    VERY_POOR = "very_poor"


class VideoProcessor(IVideoProcessor):
    """
    视频预处理器实现类
    
    支持功能:
    - 多种视频格式转换 (BGR, RGB, GRAY, HSV, YUV)
    - 智能尺寸调整和缩放
    - 视频质量检测和评估
    - 图像增强和优化
    - 支持多种分辨率 (需求1.5)
    - 质量不佳时记录警告但继续处理 (需求1.3)
    """
    
    def __init__(self, 
                 target_format: VideoFormat = VideoFormat.BGR,
                 target_size: Optional[Tuple[int, int]] = None,
                 quality_threshold: float = 0.3,
                 enable_enhancement: bool = True):
        """
        初始化视频预处理器
        
        Args:
            target_format: 目标视频格式，默认BGR
            target_size: 目标尺寸 (width, height)，None表示保持原尺寸
            quality_threshold: 质量阈值，低于此值将记录警告
            enable_enhancement: 是否启用图像增强
        """
        self.target_format = target_format
        self.target_size = target_size
        self.quality_threshold = quality_threshold
        self.enable_enhancement = enable_enhancement
        
        # 日志记录器
        self.logger = get_logger(__name__)
        
        # 注册异常处理
        exception_handler.register_module('video_processor', self._recovery_handler)
        
        # 统计信息
        self.processed_frames = 0
        self.quality_warnings = 0
        self.format_conversions = 0
        self.resize_operations = 0
        
        # 支持的输入格式 (这里暂时不使用，保留用于未来扩展)
        self.supported_formats = {
            'BGR': None,  # 默认格式，无需转换
            'RGB': cv2.COLOR_RGB2BGR,
            'GRAY': cv2.COLOR_GRAY2BGR,
            'HSV': cv2.COLOR_HSV2BGR,
            'YUV': cv2.COLOR_YUV2BGR
        }
        
        # 输出格式转换映射
        self.output_conversions = {
            VideoFormat.BGR: None,  # 默认格式，无需转换
            VideoFormat.RGB: cv2.COLOR_BGR2RGB,
            VideoFormat.GRAY: cv2.COLOR_BGR2GRAY,
            VideoFormat.HSV: cv2.COLOR_BGR2HSV,
            VideoFormat.YUV: cv2.COLOR_BGR2YUV
        }
        
        self.logger.info(f"视频预处理器初始化完成 - 目标格式: {target_format.value}, "
                        f"目标尺寸: {target_size}, 质量阈值: {quality_threshold}")
    
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        处理视频帧
        
        Args:
            frame: 输入视频帧
            
        Returns:
            np.ndarray: 处理后的视频帧
        """
        if frame is None or frame.size == 0:
            self.logger.error("输入帧为空或无效")
            return frame
        
        try:
            processed_frame = frame.copy()
            
            # 1. 检查视频质量
            quality_score = self.check_quality(processed_frame)
            if quality_score < self.quality_threshold:
                self.quality_warnings += 1
                self.logger.warning(f"视频质量较差 (得分: {quality_score:.3f}), "
                                  f"但继续处理 (需求1.3)")
            
            # 2. 尺寸调整
            if self.target_size is not None:
                processed_frame = self.resize_frame(processed_frame, self.target_size)
                self.resize_operations += 1
            
            # 3. 格式转换
            if self.target_format != VideoFormat.BGR:
                processed_frame = self._convert_format(processed_frame, self.target_format)
                self.format_conversions += 1
            
            # 4. 图像增强 (可选)
            if self.enable_enhancement and quality_score < self.quality_threshold:
                processed_frame = self._enhance_frame(processed_frame)
            
            self.processed_frames += 1
            
            return processed_frame
            
        except Exception as e:
            self.logger.error(f"处理视频帧时发生错误: {e}")
            # 使用异常处理器记录异常
            exception_handler.handle_exception(e, 'video_processor')
            return frame  # 返回原始帧以确保系统继续运行
    
    def check_quality(self, frame: np.ndarray) -> float:
        """
        检查视频质量
        
        使用多种指标评估视频质量:
        - 拉普拉斯方差 (清晰度)
        - 亮度分布
        - 对比度
        - 噪声水平
        
        Args:
            frame: 输入视频帧
            
        Returns:
            float: 质量得分 (0-1之间，1表示最佳质量)
        """
        if frame is None or frame.size == 0:
            return 0.0
        
        try:
            # 转换为灰度图像进行分析
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            
            # 1. 清晰度检测 (拉普拉斯方差)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            sharpness_score = min(laplacian_var / 1000.0, 1.0)  # 归一化到0-1
            
            # 2. 亮度分析
            mean_brightness = np.mean(gray)
            # 理想亮度范围 [80, 180]
            if 80 <= mean_brightness <= 180:
                brightness_score = 1.0
            else:
                brightness_score = max(0.0, 1.0 - abs(mean_brightness - 130) / 130.0)
            
            # 3. 对比度分析
            contrast = np.std(gray)
            contrast_score = min(contrast / 64.0, 1.0)  # 归一化
            
            # 4. 噪声检测 (使用高斯模糊后的差异)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            noise_level = np.mean(np.abs(gray.astype(np.float32) - blurred.astype(np.float32)))
            noise_score = max(0.0, 1.0 - noise_level / 20.0)
            
            # 综合质量得分 (加权平均)
            quality_score = (
                sharpness_score * 0.4 +      # 清晰度权重最高
                brightness_score * 0.25 +    # 亮度
                contrast_score * 0.25 +      # 对比度
                noise_score * 0.1             # 噪声
            )
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            self.logger.error(f"质量检测时发生错误: {e}")
            return 0.5  # 返回中等质量得分
    
    def resize_frame(self, frame: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """
        调整帧尺寸
        
        支持多种插值方法，自动选择最适合的方法。
        支持多种分辨率 (需求1.5)。
        
        Args:
            frame: 输入视频帧
            target_size: 目标尺寸 (width, height)
            
        Returns:
            np.ndarray: 调整尺寸后的帧
        """
        if frame is None or frame.size == 0:
            self.logger.error("输入帧为空，无法调整尺寸")
            return frame
        
        try:
            current_height, current_width = frame.shape[:2]
            target_width, target_height = target_size
            
            # 如果尺寸已经匹配，直接返回
            if current_width == target_width and current_height == target_height:
                return frame
            
            # 选择插值方法
            # 放大使用双三次插值，缩小使用区域插值
            if target_width * target_height > current_width * current_height:
                interpolation = cv2.INTER_CUBIC
            else:
                interpolation = cv2.INTER_AREA
            
            # 执行尺寸调整
            resized_frame = cv2.resize(frame, target_size, interpolation=interpolation)
            
            self.logger.debug(f"帧尺寸调整: {current_width}x{current_height} -> {target_width}x{target_height}")
            
            return resized_frame
            
        except Exception as e:
            self.logger.error(f"调整帧尺寸时发生错误: {e}")
            return frame
    
    def _convert_format(self, frame: np.ndarray, target_format: VideoFormat) -> np.ndarray:
        """
        转换视频格式
        
        Args:
            frame: 输入帧 (假设为BGR格式)
            target_format: 目标格式
            
        Returns:
            np.ndarray: 转换后的帧
        """
        try:
            conversion_code = self.output_conversions.get(target_format)
            
            if conversion_code is None:
                # BGR格式，无需转换
                return frame
            
            converted_frame = cv2.cvtColor(frame, conversion_code)
            
            self.logger.debug(f"格式转换: BGR -> {target_format.value}")
            
            return converted_frame
            
        except Exception as e:
            self.logger.error(f"格式转换时发生错误: {e}")
            return frame
    
    def _enhance_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        增强视频帧质量
        
        当质量较差时应用图像增强技术:
        - 直方图均衡化
        - 对比度增强
        - 降噪处理
        
        Args:
            frame: 输入帧
            
        Returns:
            np.ndarray: 增强后的帧
        """
        try:
            enhanced_frame = frame.copy()
            
            # 如果是彩色图像
            if len(enhanced_frame.shape) == 3:
                # 转换到LAB色彩空间进行亮度增强
                lab = cv2.cvtColor(enhanced_frame, cv2.COLOR_BGR2LAB)
                l_channel, a_channel, b_channel = cv2.split(lab)
                
                # 对L通道应用CLAHE (对比度限制自适应直方图均衡化)
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                l_channel = clahe.apply(l_channel)
                
                # 合并通道并转换回BGR
                enhanced_lab = cv2.merge([l_channel, a_channel, b_channel])
                enhanced_frame = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
                
            else:
                # 灰度图像直接应用CLAHE
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                enhanced_frame = clahe.apply(enhanced_frame)
            
            # 轻微降噪
            enhanced_frame = cv2.bilateralFilter(enhanced_frame, 5, 50, 50)
            
            self.logger.debug("应用图像增强处理")
            
            return enhanced_frame
            
        except Exception as e:
            self.logger.error(f"图像增强时发生错误: {e}")
            return frame
    
    def set_target_format(self, format_type: VideoFormat) -> None:
        """设置目标格式"""
        self.target_format = format_type
        self.logger.info(f"目标格式已更新为: {format_type.value}")
    
    def set_target_size(self, size: Optional[Tuple[int, int]]) -> None:
        """设置目标尺寸"""
        self.target_size = size
        self.logger.info(f"目标尺寸已更新为: {size}")
    
    def set_quality_threshold(self, threshold: float) -> None:
        """设置质量阈值"""
        self.quality_threshold = max(0.0, min(1.0, threshold))
        self.logger.info(f"质量阈值已更新为: {self.quality_threshold}")
    
    def enable_frame_enhancement(self, enable: bool) -> None:
        """启用/禁用帧增强"""
        self.enable_enhancement = enable
        self.logger.info(f"帧增强已{'启用' if enable else '禁用'}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        获取处理统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        return {
            'processed_frames': self.processed_frames,
            'quality_warnings': self.quality_warnings,
            'format_conversions': self.format_conversions,
            'resize_operations': self.resize_operations,
            'quality_warning_rate': (
                self.quality_warnings / max(1, self.processed_frames)
            ),
            'target_format': self.target_format.value,
            'target_size': self.target_size,
            'quality_threshold': self.quality_threshold,
            'enhancement_enabled': self.enable_enhancement
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.processed_frames = 0
        self.quality_warnings = 0
        self.format_conversions = 0
        self.resize_operations = 0
        self.logger.info("处理统计信息已重置")
    
    def get_quality_level(self, quality_score: float) -> QualityLevel:
        """
        根据质量得分获取质量级别
        
        Args:
            quality_score: 质量得分 (0-1)
            
        Returns:
            QualityLevel: 质量级别
        """
        if quality_score >= 0.8:
            return QualityLevel.EXCELLENT
        elif quality_score >= 0.6:
            return QualityLevel.GOOD
        elif quality_score >= 0.4:
            return QualityLevel.FAIR
        elif quality_score >= 0.2:
            return QualityLevel.POOR
        else:
            return QualityLevel.VERY_POOR
    
    def analyze_frame_properties(self, frame: np.ndarray) -> Dict[str, Any]:
        """
        分析帧属性
        
        Args:
            frame: 输入帧
            
        Returns:
            Dict[str, Any]: 帧属性信息
        """
        if frame is None or frame.size == 0:
            return {}
        
        try:
            properties = {
                'shape': frame.shape,
                'dtype': str(frame.dtype),
                'size_bytes': frame.nbytes,
                'channels': len(frame.shape) if len(frame.shape) == 2 else frame.shape[2],
                'width': frame.shape[1],
                'height': frame.shape[0],
                'quality_score': self.check_quality(frame)
            }
            
            # 如果是彩色图像，添加颜色统计
            if len(frame.shape) == 3:
                properties.update({
                    'mean_bgr': [float(np.mean(frame[:, :, i])) for i in range(3)],
                    'std_bgr': [float(np.std(frame[:, :, i])) for i in range(3)]
                })
            else:
                properties.update({
                    'mean_gray': float(np.mean(frame)),
                    'std_gray': float(np.std(frame))
                })
            
            properties['quality_level'] = self.get_quality_level(
                properties['quality_score']
            ).value
            
            return properties
            
        except Exception as e:
            self.logger.error(f"分析帧属性时发生错误: {e}")
            return {}
    
    def _recovery_handler(self) -> bool:
        """
        视频处理器恢复处理器
        
        Returns:
            是否恢复成功
        """
        try:
            self.logger.info("开始视频处理器恢复...")
            
            # 重置统计信息
            self.processed_frames = 0
            self.quality_warnings = 0
            self.format_conversions = 0
            self.resize_operations = 0
            
            # 重置配置为默认值
            self.target_format = VideoFormat.BGR
            self.quality_threshold = 0.3
            self.enable_enhancement = True
            
            self.logger.info("视频处理器恢复成功")
            return True
            
        except Exception as e:
            self.logger.error(f"视频处理器恢复失败: {e}")
            return False