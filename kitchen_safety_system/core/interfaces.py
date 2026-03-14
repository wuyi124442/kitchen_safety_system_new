"""
核心接口定义

定义系统各模块的标准接口，确保模块间的低耦合和高内聚。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
import numpy as np
from dataclasses import dataclass
from enum import Enum
import cv2


class DetectionType(Enum):
    """检测目标类型枚举"""
    PERSON = "person"
    STOVE = "stove"
    FLAME = "flame"


class AlertType(Enum):
    """报警类型枚举"""
    FALL_DETECTED = "fall_detected"
    UNATTENDED_STOVE = "unattended_stove"
    SYSTEM_ERROR = "system_error"


class AlertLevel(Enum):
    """报警级别枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class BoundingBox:
    """边界框数据结构"""
    x: int
    y: int
    width: int
    height: int
    confidence: float
    
    @property
    def center(self) -> Tuple[int, int]:
        """获取边界框中心点"""
        return (self.x + self.width // 2, self.y + self.height // 2)
    
    @property
    def area(self) -> int:
        """获取边界框面积"""
        return self.width * self.height


@dataclass
class DetectionResult:
    """检测结果数据结构"""
    detection_type: DetectionType
    bbox: BoundingBox
    timestamp: float
    frame_id: int
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class PoseKeypoint:
    """姿态关键点数据结构"""
    x: float
    y: float
    confidence: float
    visible: bool = True


@dataclass
class PoseResult:
    """姿态识别结果"""
    keypoints: List[PoseKeypoint]
    timestamp: float
    frame_id: int
    is_fall_detected: bool = False
    fall_confidence: float = 0.0


@dataclass
class AlertEvent:
    """报警事件数据结构"""
    alert_type: AlertType
    alert_level: AlertLevel
    timestamp: float
    location: Optional[Tuple[int, int]]
    description: str
    video_clip_path: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class IVideoCapture(ABC):
    """视频采集接口"""
    
    @abstractmethod
    def start_capture(self) -> bool:
        """开始视频采集"""
        pass
    
    @abstractmethod
    def stop_capture(self) -> None:
        """停止视频采集"""
        pass
    
    @abstractmethod
    def get_frame(self) -> Optional[np.ndarray]:
        """获取视频帧"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """检查连接状态"""
        pass
    
    @abstractmethod
    def reconnect(self) -> bool:
        """重新连接"""
        pass


class IVideoProcessor(ABC):
    """视频处理接口"""
    
    @abstractmethod
    def process_frame(self, frame: np.ndarray) -> np.ndarray:
        """处理视频帧"""
        pass
    
    @abstractmethod
    def check_quality(self, frame: np.ndarray) -> float:
        """检查视频质量"""
        pass
    
    @abstractmethod
    def resize_frame(self, frame: np.ndarray, target_size: Tuple[int, int]) -> np.ndarray:
        """调整帧尺寸"""
        pass


class IObjectDetector(ABC):
    """目标检测接口"""
    
    @abstractmethod
    def detect(self, frame: np.ndarray) -> List[DetectionResult]:
        """执行目标检测"""
        pass
    
    @abstractmethod
    def load_model(self, model_path: str) -> bool:
        """加载检测模型"""
        pass
    
    @abstractmethod
    def set_confidence_threshold(self, threshold: float) -> None:
        """设置置信度阈值"""
        pass


class IPoseAnalyzer(ABC):
    """姿态分析接口"""
    
    @abstractmethod
    def analyze_pose(self, frame: np.ndarray, person_bbox: BoundingBox) -> PoseResult:
        """分析人员姿态"""
        pass
    
    @abstractmethod
    def detect_fall(self, pose_result: PoseResult) -> bool:
        """检测跌倒状态"""
        pass
    
    @abstractmethod
    def is_normal_action(self, pose_result: PoseResult) -> bool:
        """判断是否为正常动作"""
        pass


class IRiskMonitor(ABC):
    """风险监控接口"""
    
    @abstractmethod
    def monitor_stove_safety(self, detections: List[DetectionResult]) -> Optional[AlertEvent]:
        """监控灶台安全"""
        pass
    
    @abstractmethod
    def calculate_distance(self, point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
        """计算两点距离"""
        pass
    
    @abstractmethod
    def update_monitoring_state(self, detections: List[DetectionResult]) -> None:
        """更新监控状态"""
        pass


class IAlertManager(ABC):
    """报警管理接口"""
    
    @abstractmethod
    def trigger_alert(self, alert_event: AlertEvent) -> bool:
        """触发报警"""
        pass
    
    @abstractmethod
    def send_notification(self, alert_event: AlertEvent, method: str) -> bool:
        """发送通知"""
        pass
    
    @abstractmethod
    def record_event(self, alert_event: AlertEvent) -> bool:
        """记录事件"""
        pass
    
    @abstractmethod
    def save_video_clip(self, frames: List[np.ndarray], event_id: str) -> str:
        """保存视频片段"""
        pass


class IConfigurationManager(ABC):
    """配置管理接口"""
    
    @abstractmethod
    def get_config(self, key: str) -> Any:
        """获取配置值"""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> bool:
        """设置配置值"""
        pass
    
    @abstractmethod
    def reload_config(self) -> bool:
        """重新加载配置"""
        pass
    
    @abstractmethod
    def get_all_configs(self) -> Dict[str, Any]:
        """获取所有配置"""
        pass


class ILogSystem(ABC):
    """日志系统接口"""
    
    @abstractmethod
    def log_event(self, level: str, message: str, additional_data: Optional[Dict] = None) -> None:
        """记录日志事件"""
        pass
    
    @abstractmethod
    def query_logs(self, start_time: float, end_time: float, 
                   event_type: Optional[str] = None, 
                   level: Optional[str] = None) -> List[Dict]:
        """查询日志"""
        pass
    
    @abstractmethod
    def export_logs(self, start_time: float, end_time: float, 
                    format_type: str = "json") -> str:
        """导出日志"""
        pass


class IDetectionSystem(ABC):
    """主检测系统接口"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """初始化系统"""
        pass
    
    @abstractmethod
    def start_detection(self) -> bool:
        """开始检测"""
        pass
    
    @abstractmethod
    def stop_detection(self) -> None:
        """停止检测"""
        pass
    
    @abstractmethod
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        pass
    
    @abstractmethod
    def process_frame_pipeline(self, frame: np.ndarray) -> List[AlertEvent]:
        """处理帧流水线"""
        pass