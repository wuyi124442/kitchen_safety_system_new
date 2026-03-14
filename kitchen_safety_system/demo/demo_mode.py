"""
演示模式实现

提供预录制视频播放功能和演示数据重置功能。
需求: 10.1, 10.5
"""

import cv2
import time
import threading
import numpy as np
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass

from ..core.interfaces import IDetectionSystem, DetectionResult
from ..core.models import SystemConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class DemoVideo:
    """演示视频信息"""
    name: str
    path: str
    description: str
    duration: float
    scenarios: List[str]  # 包含的场景类型


class DemoMode:
    """
    演示模式管理器
    
    提供预录制视频播放和演示数据管理功能。
    """
    
    def __init__(self, demo_videos_dir: str = "demo_videos"):
        """
        初始化演示模式
        
        Args:
            demo_videos_dir: 演示视频目录路径
        """
        self.demo_videos_dir = Path(demo_videos_dir)
        self.current_video: Optional[cv2.VideoCapture] = None
        self.current_video_info: Optional[DemoVideo] = None
        self.is_playing = False
        self.is_paused = False
        self.playback_thread: Optional[threading.Thread] = None
        self.frame_callback: Optional[Callable[[Any], None]] = None
        self.detection_system: Optional[IDetectionSystem] = None
        
        # 演示数据
        self.demo_detections: List[DetectionResult] = []
        self.demo_alerts: List[Dict[str, Any]] = []
        self.demo_statistics: Dict[str, Any] = {}
        
        # 预定义演示视频
        self.available_videos = self._initialize_demo_videos()
        
        logger.info(f"演示模式初始化完成，视频目录: {self.demo_videos_dir}")
    
    def _initialize_demo_videos(self) -> List[DemoVideo]:
        """初始化可用的演示视频列表"""
        videos = [
            DemoVideo(
                name="kitchen_normal",
                path="kitchen_normal_activity.mp4",
                description="正常厨房活动场景",
                duration=60.0,
                scenarios=["normal_cooking", "person_detection", "stove_monitoring"]
            ),
            DemoVideo(
                name="fall_detection",
                path="fall_detection_scenario.mp4", 
                description="跌倒检测演示场景",
                duration=45.0,
                scenarios=["fall_detection", "emergency_alert"]
            ),
            DemoVideo(
                name="unattended_stove",
                path="unattended_stove_scenario.mp4",
                description="无人看管灶台场景",
                duration=90.0,
                scenarios=["stove_monitoring", "unattended_alert", "risk_assessment"]
            ),
            DemoVideo(
                name="multi_scenario",
                path="multi_scenario_demo.mp4",
                description="综合场景演示",
                duration=120.0,
                scenarios=["person_detection", "fall_detection", "stove_monitoring", "flame_detection"]
            ),
            # 添加测试视频作为备选
            DemoVideo(
                name="test_demo",
                path="test_demo_video.mp4",
                description="测试演示视频",
                duration=10.0,
                scenarios=["person_detection", "stove_monitoring"]
            )
        ]
        
        # 检查视频文件是否存在
        available_videos = []
        for video in videos:
            video_path = self.demo_videos_dir / video.path
            if video_path.exists():
                available_videos.append(video)
                logger.info(f"找到演示视频: {video.name} - {video.description}")
            else:
                logger.warning(f"演示视频不存在: {video_path}")
        
        # 如果没有找到任何视频，创建一个虚拟视频用于演示
        if not available_videos:
            logger.info("未找到演示视频文件，将使用虚拟演示模式")
            available_videos.append(DemoVideo(
                name="virtual_demo",
                path="virtual_demo.mp4",  # 虚拟路径
                description="虚拟演示模式（无需视频文件）",
                duration=60.0,
                scenarios=["person_detection", "fall_detection", "stove_monitoring", "flame_detection"]
            ))
        
        return available_videos
    
    def get_available_videos(self) -> List[DemoVideo]:
        """获取可用的演示视频列表"""
        return self.available_videos.copy()
    
    def load_video(self, video_name: str) -> bool:
        """
        加载指定的演示视频
        
        Args:
            video_name: 视频名称
            
        Returns:
            是否加载成功
        """
        try:
            # 查找视频信息
            video_info = None
            for video in self.available_videos:
                if video.name == video_name:
                    video_info = video
                    break
            
            if not video_info:
                logger.error(f"未找到演示视频: {video_name}")
                return False
            
            # 停止当前播放
            self.stop_playback()
            
            # 处理虚拟演示模式
            if video_name == "virtual_demo":
                logger.info("启用虚拟演示模式")
                self.current_video_info = video_info
                self.current_video = None  # 虚拟模式不需要实际视频
                return True
            
            # 加载真实视频文件
            video_path = self.demo_videos_dir / video_info.path
            if not video_path.exists():
                logger.warning(f"视频文件不存在，切换到虚拟演示模式: {video_path}")
                # 切换到虚拟演示模式
                from dataclasses import replace
                virtual_video = DemoVideo(
                    name="virtual_demo",
                    path="virtual_demo.mp4",
                    description=f"虚拟演示模式 - {video_info.description}",
                    duration=video_info.duration,
                    scenarios=video_info.scenarios
                )
                self.current_video_info = virtual_video
                self.current_video = None
                return True
            
            self.current_video = cv2.VideoCapture(str(video_path))
            
            if not self.current_video.isOpened():
                logger.error(f"无法打开演示视频: {video_path}")
                self.current_video = None
                return False
            
            self.current_video_info = video_info
            logger.info(f"已加载演示视频: {video_info.name}")
            
            return True
            
        except Exception as e:
            logger.error(f"加载演示视频失败: {e}")
            return False
    
    def start_playback(self, frame_callback: Optional[Callable[[Any], None]] = None) -> bool:
        """
        开始播放当前视频
        
        Args:
            frame_callback: 帧处理回调函数
            
        Returns:
            是否开始播放成功
        """
        if not self.current_video or not self.current_video.isOpened():
            logger.error("没有可播放的视频")
            return False
        
        if self.is_playing:
            logger.warning("视频已在播放中")
            return True
        
        self.frame_callback = frame_callback
        self.is_playing = True
        self.is_paused = False
        
        # 启动播放线程
        self.playback_thread = threading.Thread(target=self._playback_loop)
        self.playback_thread.daemon = True
        self.playback_thread.start()
        
        logger.info("开始播放演示视频")
        return True
    
    def stop_playback(self) -> None:
        """停止播放"""
        if not self.is_playing:
            return
        
        self.is_playing = False
        self.is_paused = False
        
        # 等待播放线程结束
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=2.0)
        
        logger.info("停止播放演示视频")
    
    def pause_playback(self) -> None:
        """暂停播放"""
        if self.is_playing:
            self.is_paused = True
            logger.info("暂停播放演示视频")
    
    def resume_playback(self) -> None:
        """恢复播放"""
        if self.is_playing and self.is_paused:
            self.is_paused = False
            logger.info("恢复播放演示视频")
    
    def _playback_loop(self) -> None:
        """播放循环"""
        # 处理虚拟演示模式
        if self.current_video is None and self.current_video_info:
            self._virtual_playback_loop()
            return
        
        if not self.current_video:
            return
        
        # 获取视频帧率
        fps = self.current_video.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30  # 默认帧率
        
        frame_delay = 1.0 / fps
        
        try:
            while self.is_playing:
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                
                ret, frame = self.current_video.read()
                if not ret:
                    # 视频播放完毕，重新开始
                    self.current_video.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                
                # 调用帧处理回调
                if self.frame_callback:
                    try:
                        self.frame_callback(frame)
                    except Exception as e:
                        logger.error(f"帧处理回调出错: {e}")
                
                # 控制播放速度
                time.sleep(frame_delay)
                
        except Exception as e:
            logger.error(f"视频播放循环出错: {e}")
        finally:
            self.is_playing = False
    
    def _virtual_playback_loop(self) -> None:
        """虚拟播放循环（生成模拟帧）"""
        logger.info("启动虚拟演示播放循环")
        
        fps = 15  # 虚拟模式帧率
        frame_delay = 1.0 / fps
        frame_count = 0
        
        try:
            while self.is_playing:
                if self.is_paused:
                    time.sleep(0.1)
                    continue
                
                # 生成虚拟帧
                frame = self._generate_virtual_frame(frame_count)
                
                # 调用帧处理回调
                if self.frame_callback:
                    try:
                        self.frame_callback(frame)
                    except Exception as e:
                        logger.error(f"虚拟帧处理回调出错: {e}")
                
                frame_count += 1
                
                # 控制播放速度
                time.sleep(frame_delay)
                
        except Exception as e:
            logger.error(f"虚拟播放循环出错: {e}")
        finally:
            self.is_playing = False
    
    def _generate_virtual_frame(self, frame_count: int) -> Any:
        """生成虚拟演示帧"""
        import numpy as np
        
        # 创建基础帧
        width, height = 640, 480
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # 添加背景
        cv2.rectangle(frame, (50, 50), (width-50, height-50), (40, 40, 40), -1)
        
        # 添加标题
        cv2.putText(frame, "Kitchen Safety Demo - Virtual Mode", (100, 80), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # 添加场景描述
        if self.current_video_info:
            cv2.putText(frame, self.current_video_info.description, (100, 110),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
        
        # 添加帧计数
        cv2.putText(frame, f"Frame: {frame_count}", (100, height-80),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        # 添加动态元素
        time_factor = frame_count * 0.1
        
        # 模拟移动的人员
        person_x = 150 + int(100 * np.sin(time_factor * 0.5))
        person_y = 200
        cv2.rectangle(frame, (person_x, person_y), (person_x+60, person_y+120), (0, 255, 0), 2)
        cv2.putText(frame, "Person", (person_x, person_y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # 模拟灶台
        stove_x, stove_y = 400, 300
        cv2.rectangle(frame, (stove_x, stove_y), (stove_x+80, stove_y+50), (255, 165, 0), 2)
        cv2.putText(frame, "Stove", (stove_x, stove_y-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 165, 0), 1)
        
        # 模拟火焰（闪烁效果）
        if int(time_factor) % 3 != 0:  # 间歇性显示火焰
            flame_x, flame_y = stove_x + 20, stove_y - 20
            cv2.circle(frame, (flame_x, flame_y), 15, (0, 0, 255), 2)
            cv2.putText(frame, "Flame", (flame_x-20, flame_y-25), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1)
        
        # 添加时间信息
        cv2.putText(frame, f"Time: {time_factor:.1f}s", (100, height-50),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        return frame
    
    def get_current_frame(self) -> Optional[Any]:
        """获取当前帧"""
        if not self.current_video or not self.current_video.isOpened():
            return None
        
        ret, frame = self.current_video.read()
        if ret:
            return frame
        return None
    
    def get_playback_info(self) -> Dict[str, Any]:
        """获取播放信息"""
        info = {
            'is_playing': self.is_playing,
            'is_paused': self.is_paused,
            'current_video': None,
            'position': 0.0,
            'duration': 0.0,
            'fps': 0.0
        }
        
        if self.current_video_info:
            info['current_video'] = {
                'name': self.current_video_info.name,
                'description': self.current_video_info.description,
                'scenarios': self.current_video_info.scenarios
            }
        
        if self.current_video and self.current_video.isOpened():
            total_frames = self.current_video.get(cv2.CAP_PROP_FRAME_COUNT)
            current_frame = self.current_video.get(cv2.CAP_PROP_POS_FRAMES)
            fps = self.current_video.get(cv2.CAP_PROP_FPS)
            
            if fps > 0:
                info['duration'] = total_frames / fps
                info['position'] = current_frame / fps
                info['fps'] = fps
        
        return info
    
    def reset_demo_data(self) -> None:
        """
        重置演示数据
        
        清除所有演示检测结果、报警记录和统计信息。
        需求: 10.5
        """
        logger.info("重置演示数据")
        
        # 清除检测结果
        self.demo_detections.clear()
        
        # 清除报警记录
        self.demo_alerts.clear()
        
        # 重置统计信息
        self.demo_statistics = {
            'total_frames_processed': 0,
            'total_detections': 0,
            'person_detections': 0,
            'stove_detections': 0,
            'flame_detections': 0,
            'fall_events': 0,
            'unattended_stove_events': 0,
            'alerts_triggered': 0,
            'demo_start_time': time.time()
        }
        
        # 如果有检测系统，也重置其状态
        if self.detection_system:
            try:
                # 重置检测系统的演示相关状态
                if hasattr(self.detection_system, 'reset_demo_state'):
                    self.detection_system.reset_demo_state()
            except Exception as e:
                logger.error(f"重置检测系统演示状态失败: {e}")
        
        logger.info("演示数据重置完成")
    
    def add_demo_detection(self, detection: DetectionResult) -> None:
        """添加演示检测结果"""
        self.demo_detections.append(detection)
        
        # 更新统计信息
        self.demo_statistics['total_detections'] += 1
        
        detection_type = detection.detection_type.value
        if detection_type == 'person':
            self.demo_statistics['person_detections'] += 1
        elif detection_type == 'stove':
            self.demo_statistics['stove_detections'] += 1
        elif detection_type == 'flame':
            self.demo_statistics['flame_detections'] += 1
    
    def add_demo_alert(self, alert_type: str, description: str, **kwargs) -> None:
        """添加演示报警记录"""
        alert = {
            'type': alert_type,
            'description': description,
            'timestamp': time.time(),
            **kwargs
        }
        
        self.demo_alerts.append(alert)
        self.demo_statistics['alerts_triggered'] += 1
        
        # 更新特定事件统计
        if alert_type == 'fall_detected':
            self.demo_statistics['fall_events'] += 1
        elif alert_type == 'unattended_stove':
            self.demo_statistics['unattended_stove_events'] += 1
    
    def get_demo_statistics(self) -> Dict[str, Any]:
        """获取演示统计信息"""
        stats = self.demo_statistics.copy()
        
        # 计算运行时间
        if 'demo_start_time' in stats:
            stats['demo_duration'] = time.time() - stats['demo_start_time']
        
        # 计算检测率
        if stats['total_frames_processed'] > 0:
            stats['detection_rate'] = stats['total_detections'] / stats['total_frames_processed']
        else:
            stats['detection_rate'] = 0.0
        
        return stats
    
    def set_detection_system(self, detection_system: IDetectionSystem) -> None:
        """设置检测系统引用"""
        self.detection_system = detection_system
    
    def create_demo_scenario(self, scenario_name: str) -> bool:
        """
        创建演示场景
        
        Args:
            scenario_name: 场景名称
            
        Returns:
            是否创建成功
        """
        logger.info(f"创建演示场景: {scenario_name}")
        
        # 重置演示数据
        self.reset_demo_data()
        
        # 根据场景类型加载相应视频
        scenario_video_map = {
            'normal_cooking': 'kitchen_normal',
            'fall_detection': 'fall_detection', 
            'unattended_stove': 'unattended_stove',
            'comprehensive': 'multi_scenario',
            'test': 'test_demo',
            'virtual': 'virtual_demo'
        }
        
        video_name = scenario_video_map.get(scenario_name)
        
        # 首先尝试加载指定的视频
        if video_name and self._video_exists(video_name):
            return self.load_video(video_name)
        
        # 如果指定视频不存在，尝试使用可用的第一个视频
        if self.available_videos:
            logger.info(f"场景 {scenario_name} 对应的视频不存在，使用第一个可用视频: {self.available_videos[0].name}")
            return self.load_video(self.available_videos[0].name)
        
        # 如果没有任何可用视频，创建虚拟演示
        logger.info(f"没有可用视频，创建虚拟演示场景")
        return self.load_video("virtual_demo")
    
    def _video_exists(self, video_name: str) -> bool:
        """检查视频是否存在"""
        for video in self.available_videos:
            if video.name == video_name:
                return True
        return False
    
    def cleanup(self) -> None:
        """清理资源"""
        logger.info("清理演示模式资源")
        
        # 停止播放
        self.stop_playback()
        
        # 释放视频资源
        if self.current_video:
            self.current_video.release()
            self.current_video = None
        
        # 清除数据
        self.demo_detections.clear()
        self.demo_alerts.clear()
        self.demo_statistics.clear()