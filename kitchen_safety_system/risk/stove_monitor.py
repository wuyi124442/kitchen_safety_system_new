"""
灶台监控模块

实现灶台安全监控功能，包括人员与灶台距离计算和无人看管时间统计。
"""

import time
import math
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from ..core.interfaces import (
    IRiskMonitor, DetectionResult, DetectionType, AlertEvent, 
    AlertType, AlertLevel, BoundingBox
)
from ..utils.logger import get_logger


@dataclass
class StoveState:
    """灶台状态数据结构"""
    stove_id: str
    bbox: BoundingBox
    has_flame: bool = False
    flame_bbox: Optional[BoundingBox] = None
    last_person_nearby_time: Optional[float] = None
    unattended_start_time: Optional[float] = None
    is_being_monitored: bool = False
    nearest_person_distance: Optional[float] = None
    
    @property
    def unattended_duration(self) -> float:
        """获取无人看管持续时间（秒）"""
        if self.unattended_start_time is None:
            return 0.0
        return time.time() - self.unattended_start_time
    
    @property
    def is_unattended(self) -> bool:
        """判断是否处于无人看管状态"""
        return self.has_flame and self.unattended_start_time is not None


class StoveMonitor(IRiskMonitor):
    """
    灶台监控器
    
    实现灶台安全监控功能：
    1. 计算人员与灶台的距离
    2. 跟踪无人看管的灶台时间
    3. 生成相应的安全警报
    """
    
    def __init__(self, 
                 distance_threshold: float = 2.0,
                 unattended_time_threshold: int = 300,
                 alert_cooldown_time: int = 30):
        """
        初始化灶台监控器
        
        Args:
            distance_threshold: 人员与灶台的安全距离阈值（米）
            unattended_time_threshold: 无人看管时间阈值（秒）
            alert_cooldown_time: 报警冷却时间（秒）
        """
        self.logger = get_logger(__name__)
        
        # 配置参数
        self.distance_threshold = distance_threshold
        self.unattended_time_threshold = unattended_time_threshold
        self.alert_cooldown_time = alert_cooldown_time
        
        # 灶台状态跟踪
        self.stove_states: Dict[str, StoveState] = {}
        self.last_alert_times: Dict[str, float] = {}
        
        # 像素到米的转换比例（需要根据实际摄像头配置调整）
        self.pixels_per_meter = 100.0  # 假设100像素 = 1米
        
        self.logger.info(f"灶台监控器已初始化 - 距离阈值: {distance_threshold}m, "
                        f"无人看管阈值: {unattended_time_threshold}s")
    
    def monitor_stove_safety(self, detections: List[DetectionResult]) -> Optional[AlertEvent]:
        """
        监控灶台安全状况
        
        Args:
            detections: 当前帧的检测结果列表
            
        Returns:
            Optional[AlertEvent]: 如果检测到风险则返回警报事件
        """
        try:
            # 更新监控状态
            self.update_monitoring_state(detections)
            
            # 检查是否需要触发警报
            alert_event = self._check_for_alerts()
            
            return alert_event
            
        except Exception as e:
            self.logger.error(f"灶台安全监控出错: {e}")
            return None
    
    def update_monitoring_state(self, detections: List[DetectionResult]) -> None:
        """
        更新监控状态
        
        Args:
            detections: 检测结果列表
        """
        current_time = time.time()
        
        # 分类检测结果
        persons = [d for d in detections if d.detection_type == DetectionType.PERSON]
        stoves = [d for d in detections if d.detection_type == DetectionType.STOVE]
        flames = [d for d in detections if d.detection_type == DetectionType.FLAME]
        
        # 更新灶台状态
        self._update_stove_states(stoves, flames, persons, current_time)
        
        # 清理过期的灶台状态
        self._cleanup_stale_stoves(current_time)
    
    def _update_stove_states(self, 
                           stoves: List[DetectionResult], 
                           flames: List[DetectionResult],
                           persons: List[DetectionResult], 
                           current_time: float) -> None:
        """
        更新灶台状态信息
        
        Args:
            stoves: 灶台检测结果
            flames: 火焰检测结果
            persons: 人员检测结果
            current_time: 当前时间戳
        """
        # 为每个检测到的灶台创建或更新状态
        current_stove_ids = set()
        
        for stove in stoves:
            stove_id = self._generate_stove_id(stove.bbox)
            current_stove_ids.add(stove_id)
            
            # 检查是否有火焰与此灶台关联
            associated_flame = self._find_associated_flame(stove.bbox, flames)
            has_flame = associated_flame is not None
            
            # 计算最近人员距离
            nearest_distance = self._calculate_nearest_person_distance(stove.bbox, persons)
            person_nearby = nearest_distance is not None and nearest_distance <= self.distance_threshold
            
            # 更新或创建灶台状态
            if stove_id in self.stove_states:
                stove_state = self.stove_states[stove_id]
                stove_state.bbox = stove.bbox
                stove_state.has_flame = has_flame
                stove_state.flame_bbox = associated_flame.bbox if associated_flame else None
                stove_state.nearest_person_distance = nearest_distance
            else:
                stove_state = StoveState(
                    stove_id=stove_id,
                    bbox=stove.bbox,
                    has_flame=has_flame,
                    flame_bbox=associated_flame.bbox if associated_flame else None,
                    nearest_person_distance=nearest_distance
                )
                self.stove_states[stove_id] = stove_state
            
            # 更新无人看管状态
            self._update_unattended_status(stove_state, person_nearby, current_time)
        
        # 移除不再检测到的灶台
        stale_stove_ids = set(self.stove_states.keys()) - current_stove_ids
        for stale_id in stale_stove_ids:
            del self.stove_states[stale_id]
    
    def _generate_stove_id(self, bbox: BoundingBox) -> str:
        """
        为灶台生成唯一ID（基于位置）
        
        Args:
            bbox: 灶台边界框
            
        Returns:
            str: 灶台ID
        """
        center_x, center_y = bbox.center
        # 使用网格化的位置作为ID，避免微小移动导致ID变化
        grid_x = int(center_x // 50) * 50
        grid_y = int(center_y // 50) * 50
        return f"stove_{grid_x}_{grid_y}"
    
    def _find_associated_flame(self, stove_bbox: BoundingBox, 
                             flames: List[DetectionResult]) -> Optional[DetectionResult]:
        """
        查找与灶台关联的火焰
        
        Args:
            stove_bbox: 灶台边界框
            flames: 火焰检测结果列表
            
        Returns:
            Optional[DetectionResult]: 关联的火焰检测结果
        """
        min_distance = float('inf')
        closest_flame = None
        
        stove_center = stove_bbox.center
        
        for flame in flames:
            flame_center = flame.bbox.center
            distance = self.calculate_distance(stove_center, flame_center)
            
            # 火焰必须在灶台附近才认为是关联的
            if distance < 100 and distance < min_distance:  # 100像素内
                min_distance = distance
                closest_flame = flame
        
        return closest_flame
    
    def _calculate_nearest_person_distance(self, stove_bbox: BoundingBox, 
                                         persons: List[DetectionResult]) -> Optional[float]:
        """
        计算灶台到最近人员的距离
        
        Args:
            stove_bbox: 灶台边界框
            persons: 人员检测结果列表
            
        Returns:
            Optional[float]: 最近距离（米），None表示没有检测到人员
        """
        if not persons:
            return None
        
        min_distance = float('inf')
        stove_center = stove_bbox.center
        
        for person in persons:
            person_center = person.bbox.center
            distance_pixels = self.calculate_distance(stove_center, person_center)
            distance_meters = distance_pixels / self.pixels_per_meter
            
            if distance_meters < min_distance:
                min_distance = distance_meters
        
        return min_distance if min_distance != float('inf') else None
    
    def _update_unattended_status(self, stove_state: StoveState, 
                                person_nearby: bool, current_time: float) -> None:
        """
        更新灶台的无人看管状态
        
        Args:
            stove_state: 灶台状态
            person_nearby: 是否有人在附近
            current_time: 当前时间戳
        """
        if person_nearby:
            # 有人在附近
            stove_state.last_person_nearby_time = current_time
            if stove_state.unattended_start_time is not None:
                # 结束无人看管状态
                stove_state.unattended_start_time = None
                stove_state.is_being_monitored = False
                self.logger.debug(f"灶台 {stove_state.stove_id} 有人返回，结束无人看管监控")
        else:
            # 没有人在附近
            if stove_state.has_flame:
                if stove_state.unattended_start_time is None:
                    # 开始无人看管监控
                    stove_state.unattended_start_time = current_time
                    stove_state.is_being_monitored = True
                    self.logger.info(f"灶台 {stove_state.stove_id} 开始无人看管监控")
    
    def calculate_distance(self, point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
        """
        计算两点之间的欧几里得距离
        
        Args:
            point1: 第一个点坐标 (x, y)
            point2: 第二个点坐标 (x, y)
            
        Returns:
            float: 距离（像素）
        """
        x1, y1 = point1
        x2, y2 = point2
        return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
    
    def _check_for_alerts(self) -> Optional[AlertEvent]:
        """
        检查是否需要触发警报
        
        Returns:
            Optional[AlertEvent]: 警报事件，None表示无需警报
        """
        current_time = time.time()
        
        for stove_id, stove_state in self.stove_states.items():
            if not stove_state.is_unattended:
                continue
            
            # 检查无人看管时间是否超过阈值
            if stove_state.unattended_duration >= self.unattended_time_threshold:
                # 检查是否在冷却期内
                last_alert_time = self.last_alert_times.get(stove_id, 0)
                if current_time - last_alert_time < self.alert_cooldown_time:
                    continue
                
                # 创建警报事件
                alert_event = AlertEvent(
                    alert_type=AlertType.UNATTENDED_STOVE,
                    alert_level=AlertLevel.HIGH,
                    timestamp=current_time,
                    location=stove_state.bbox.center,
                    description=f"灶台无人看管已持续 {int(stove_state.unattended_duration)} 秒",
                    additional_data={
                        'stove_id': stove_id,
                        'unattended_duration': stove_state.unattended_duration,
                        'stove_bbox': {
                            'x': stove_state.bbox.x,
                            'y': stove_state.bbox.y,
                            'width': stove_state.bbox.width,
                            'height': stove_state.bbox.height
                        },
                        'flame_bbox': {
                            'x': stove_state.flame_bbox.x,
                            'y': stove_state.flame_bbox.y,
                            'width': stove_state.flame_bbox.width,
                            'height': stove_state.flame_bbox.height
                        } if stove_state.flame_bbox else None,
                        'nearest_person_distance': stove_state.nearest_person_distance
                    }
                )
                
                # 记录警报时间
                self.last_alert_times[stove_id] = current_time
                
                self.logger.warning(f"触发无人看管警报: {alert_event.description}")
                return alert_event
        
        return None
    
    def _cleanup_stale_stoves(self, current_time: float) -> None:
        """
        清理过期的灶台状态
        
        Args:
            current_time: 当前时间戳
        """
        stale_threshold = 10.0  # 10秒内未检测到则认为过期
        stale_stove_ids = []
        
        for stove_id, stove_state in self.stove_states.items():
            if (stove_state.last_person_nearby_time and 
                current_time - stove_state.last_person_nearby_time > stale_threshold):
                stale_stove_ids.append(stove_id)
        
        for stale_id in stale_stove_ids:
            self.logger.debug(f"清理过期灶台状态: {stale_id}")
            del self.stove_states[stale_id]
            if stale_id in self.last_alert_times:
                del self.last_alert_times[stale_id]
    
    def get_monitoring_status(self) -> Dict[str, any]:
        """
        获取当前监控状态
        
        Returns:
            Dict[str, any]: 监控状态信息
        """
        status = {
            'total_stoves': len(self.stove_states),
            'unattended_stoves': sum(1 for s in self.stove_states.values() if s.is_unattended),
            'stoves_with_flame': sum(1 for s in self.stove_states.values() if s.has_flame),
            'distance_threshold': self.distance_threshold,
            'unattended_time_threshold': self.unattended_time_threshold,
            'stove_details': []
        }
        
        for stove_id, stove_state in self.stove_states.items():
            stove_detail = {
                'stove_id': stove_id,
                'has_flame': stove_state.has_flame,
                'is_unattended': stove_state.is_unattended,
                'unattended_duration': stove_state.unattended_duration,
                'nearest_person_distance': stove_state.nearest_person_distance,
                'location': stove_state.bbox.center
            }
            status['stove_details'].append(stove_detail)
        
        return status
    
    def set_distance_threshold(self, threshold: float) -> None:
        """
        设置距离阈值
        
        Args:
            threshold: 新的距离阈值（米）
        """
        if threshold > 0:
            self.distance_threshold = threshold
            self.logger.info(f"距离阈值已更新为: {threshold}m")
        else:
            self.logger.warning(f"无效的距离阈值: {threshold}")
    
    def set_unattended_time_threshold(self, threshold: int) -> None:
        """
        设置无人看管时间阈值
        
        Args:
            threshold: 新的时间阈值（秒）
        """
        if threshold > 0:
            self.unattended_time_threshold = threshold
            self.logger.info(f"无人看管时间阈值已更新为: {threshold}s")
        else:
            self.logger.warning(f"无效的时间阈值: {threshold}")
    
    def set_pixels_per_meter(self, pixels_per_meter: float) -> None:
        """
        设置像素到米的转换比例
        
        Args:
            pixels_per_meter: 每米对应的像素数
        """
        if pixels_per_meter > 0:
            self.pixels_per_meter = pixels_per_meter
            self.logger.info(f"像素转换比例已更新为: {pixels_per_meter} 像素/米")
        else:
            self.logger.warning(f"无效的像素转换比例: {pixels_per_meter}")
    
    def reset_monitoring_state(self) -> None:
        """重置所有监控状态"""
        self.stove_states.clear()
        self.last_alert_times.clear()
        self.logger.info("监控状态已重置")