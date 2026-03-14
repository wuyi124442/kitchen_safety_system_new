"""
YOLO检测器配置管理器

负责加载和管理YOLO检测器的配置参数。
"""

import os
import yaml
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from ..utils.logger import get_logger


class YOLOConfigManager:
    """
    YOLO配置管理器
    
    负责加载、验证和提供YOLO检测器的配置参数。
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_path: 配置文件路径，None则使用默认路径
        """
        self.logger = get_logger(__name__)
        self.config_path = config_path or "config/yolo_config.yaml"
        self.config: Dict[str, Any] = {}
        
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if not os.path.exists(self.config_path):
                self.logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                self._load_default_config()
                return
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            self.logger.info(f"配置文件加载成功: {self.config_path}")
            self._validate_config()
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            self._load_default_config()
    
    def _load_default_config(self) -> None:
        """加载默认配置"""
        self.config = {
            'yolo_detector': {
                'model': {
                    'path': 'yolo/yolo11n.pt',
                    'device': 'auto',
                    'half_precision': False
                },
                'detection': {
                    'confidence_threshold': 0.5,
                    'iou_threshold': 0.45,
                    'min_box_size': 10,
                    'max_detections': 100
                },
                'class_mapping': {
                    'person': 'person',
                    'fire': 'flame',
                    'stove': 'stove',
                    'oven': 'stove',
                    'microwave': 'stove',
                    'toaster': 'stove'
                },
                'performance': {
                    'input_size': [640, 640],
                    'batch_size': 1,
                    'tensorrt': False,
                    'onnx': False
                },
                'visualization': {
                    'colors': {
                        'person': [0, 255, 0],
                        'stove': [255, 0, 0],
                        'flame': [0, 0, 255]
                    },
                    'box_thickness': 2,
                    'font_scale': 0.6,
                    'text_thickness': 1,
                    'show_confidence': True,
                    'show_labels': True
                },
                'logging': {
                    'level': 'INFO',
                    'stats_interval': 100,
                    'log_detections': False
                }
            },
            'kitchen_safety': {
                'requirements': {
                    'min_map': 0.85,
                    'min_fps': 15,
                    'supported_types': ['person', 'stove', 'flame']
                },
                'risk_assessment': {
                    'safe_distance': 100,
                    'unattended_threshold': 30,
                    'fall_confidence_threshold': 0.8
                }
            }
        }
        
        self.logger.info("使用默认配置")
    
    def _validate_config(self) -> None:
        """验证配置参数"""
        try:
            # 验证必需的配置节
            required_sections = ['yolo_detector', 'kitchen_safety']
            for section in required_sections:
                if section not in self.config:
                    raise ValueError(f"缺少必需的配置节: {section}")
            
            # 验证YOLO检测器配置
            yolo_config = self.config['yolo_detector']
            
            # 验证置信度阈值
            conf_threshold = yolo_config.get('detection', {}).get('confidence_threshold', 0.5)
            if not 0.0 <= conf_threshold <= 1.0:
                raise ValueError(f"无效的置信度阈值: {conf_threshold}")
            
            # 验证IoU阈值
            iou_threshold = yolo_config.get('detection', {}).get('iou_threshold', 0.45)
            if not 0.0 <= iou_threshold <= 1.0:
                raise ValueError(f"无效的IoU阈值: {iou_threshold}")
            
            # 验证模型路径
            model_path = yolo_config.get('model', {}).get('path')
            if model_path and not model_path.endswith('.pt'):
                self.logger.warning(f"模型路径可能无效: {model_path}")
            
            self.logger.info("配置验证通过")
            
        except Exception as e:
            self.logger.error(f"配置验证失败: {e}")
            raise
    
    def get_model_config(self) -> Dict[str, Any]:
        """获取模型配置"""
        return self.config.get('yolo_detector', {}).get('model', {})
    
    def get_detection_config(self) -> Dict[str, Any]:
        """获取检测配置"""
        return self.config.get('yolo_detector', {}).get('detection', {})
    
    def get_class_mapping(self) -> Dict[str, str]:
        """获取类别映射配置"""
        return self.config.get('yolo_detector', {}).get('class_mapping', {})
    
    def get_performance_config(self) -> Dict[str, Any]:
        """获取性能配置"""
        return self.config.get('yolo_detector', {}).get('performance', {})
    
    def get_visualization_config(self) -> Dict[str, Any]:
        """获取可视化配置"""
        return self.config.get('yolo_detector', {}).get('visualization', {})
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置"""
        return self.config.get('yolo_detector', {}).get('logging', {})
    
    def get_kitchen_safety_config(self) -> Dict[str, Any]:
        """获取厨房安全配置"""
        return self.config.get('kitchen_safety', {})
    
    def get_requirements(self) -> Dict[str, Any]:
        """获取性能要求配置"""
        return self.config.get('kitchen_safety', {}).get('requirements', {})
    
    def get_risk_assessment_config(self) -> Dict[str, Any]:
        """获取风险评估配置"""
        return self.config.get('kitchen_safety', {}).get('risk_assessment', {})
    
    def get_testing_config(self) -> Dict[str, Any]:
        """获取测试配置"""
        return self.config.get('testing', {})
    
    # 便捷方法
    def get_model_path(self) -> str:
        """获取模型路径"""
        return self.get_model_config().get('path', 'yolo/yolo11n.pt')
    
    def get_device(self) -> str:
        """获取推理设备"""
        return self.get_model_config().get('device', 'auto')
    
    def get_confidence_threshold(self) -> float:
        """获取置信度阈值"""
        return self.get_detection_config().get('confidence_threshold', 0.5)
    
    def get_iou_threshold(self) -> float:
        """获取IoU阈值"""
        return self.get_detection_config().get('iou_threshold', 0.45)
    
    def get_min_box_size(self) -> int:
        """获取最小检测框尺寸"""
        return self.get_detection_config().get('min_box_size', 10)
    
    def get_input_size(self) -> Tuple[int, int]:
        """获取输入图像尺寸"""
        size = self.get_performance_config().get('input_size', [640, 640])
        return tuple(size)
    
    def get_visualization_colors(self) -> Dict[str, List[int]]:
        """获取可视化颜色配置"""
        return self.get_visualization_config().get('colors', {
            'person': [0, 255, 0],
            'stove': [255, 0, 0],
            'flame': [0, 0, 255]
        })
    
    def get_min_fps_requirement(self) -> float:
        """获取最小FPS要求"""
        return self.get_requirements().get('min_fps', 15)
    
    def get_min_map_requirement(self) -> float:
        """获取最小mAP要求"""
        return self.get_requirements().get('min_map', 0.85)
    
    def get_supported_detection_types(self) -> List[str]:
        """获取支持的检测类型"""
        return self.get_requirements().get('supported_types', ['person', 'stove', 'flame'])
    
    def get_safe_distance(self) -> int:
        """获取安全距离阈值"""
        return self.get_risk_assessment_config().get('safe_distance', 100)
    
    def get_unattended_threshold(self) -> float:
        """获取无人看管时间阈值"""
        return self.get_risk_assessment_config().get('unattended_threshold', 30)
    
    def update_config(self, key_path: str, value: Any) -> bool:
        """
        更新配置值
        
        Args:
            key_path: 配置键路径，如 'yolo_detector.detection.confidence_threshold'
            value: 新值
            
        Returns:
            bool: 更新是否成功
        """
        try:
            keys = key_path.split('.')
            config_ref = self.config
            
            # 导航到目标位置
            for key in keys[:-1]:
                if key not in config_ref:
                    config_ref[key] = {}
                config_ref = config_ref[key]
            
            # 设置值
            config_ref[keys[-1]] = value
            
            self.logger.info(f"配置已更新: {key_path} = {value}")
            return True
            
        except Exception as e:
            self.logger.error(f"更新配置失败: {e}")
            return False
    
    def save_config(self, output_path: Optional[str] = None) -> bool:
        """
        保存配置到文件
        
        Args:
            output_path: 输出文件路径，None则使用原路径
            
        Returns:
            bool: 保存是否成功
        """
        try:
            save_path = output_path or self.config_path
            
            # 确保目录存在
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'w', encoding='utf-8') as f:
                yaml.dump(self.config, f, default_flow_style=False, 
                         allow_unicode=True, indent=2)
            
            self.logger.info(f"配置已保存到: {save_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def reload_config(self) -> bool:
        """
        重新加载配置文件
        
        Returns:
            bool: 重新加载是否成功
        """
        try:
            self._load_config()
            self.logger.info("配置已重新加载")
            return True
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")
            return False
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取完整配置"""
        return self.config.copy()
    
    def print_config_summary(self) -> None:
        """打印配置摘要"""
        print("=== YOLO检测器配置摘要 ===")
        print(f"模型路径: {self.get_model_path()}")
        print(f"推理设备: {self.get_device()}")
        print(f"置信度阈值: {self.get_confidence_threshold()}")
        print(f"IoU阈值: {self.get_iou_threshold()}")
        print(f"输入尺寸: {self.get_input_size()}")
        print(f"最小FPS要求: {self.get_min_fps_requirement()}")
        print(f"最小mAP要求: {self.get_min_map_requirement()}")
        print(f"支持的检测类型: {self.get_supported_detection_types()}")
        print(f"安全距离: {self.get_safe_distance()}px")
        print(f"无人看管阈值: {self.get_unattended_threshold()}s")


# 全局配置管理器实例
_config_manager: Optional[YOLOConfigManager] = None


def get_yolo_config_manager(config_path: Optional[str] = None) -> YOLOConfigManager:
    """
    获取全局YOLO配置管理器实例
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        YOLOConfigManager: 配置管理器实例
    """
    global _config_manager
    
    if _config_manager is None or config_path:
        _config_manager = YOLOConfigManager(config_path)
    
    return _config_manager


if __name__ == "__main__":
    # 测试配置管理器
    config_manager = YOLOConfigManager()
    config_manager.print_config_summary()