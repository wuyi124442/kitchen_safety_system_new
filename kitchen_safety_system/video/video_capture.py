"""
视频采集器实现

支持摄像头和视频文件输入，具备视频流中断重连机制。
实现需求 1.1, 1.2, 1.4。
"""

import cv2
import numpy as np
import time
import threading
import logging
from typing import Optional, Union
from pathlib import Path

from ..core.interfaces import IVideoCapture


class VideoCapture(IVideoCapture):
    """
    视频采集器实现类
    
    支持功能:
    - 摄像头输入 (通过设备ID)
    - 视频文件输入 (通过文件路径)
    - 自动重连机制
    - 连接状态监控
    - 帧率控制
    """
    
    def __init__(self, source: Union[int, str], target_fps: int = 15):
        """
        初始化视频采集器
        
        Args:
            source: 视频源，可以是摄像头ID(int)或视频文件路径(str)
            target_fps: 目标帧率，默认15fps (满足需求1.4)
        """
        self.source = source
        self.target_fps = target_fps
        self.frame_interval = 1.0 / target_fps
        
        self.cap: Optional[cv2.VideoCapture] = None
        self.is_running = False
        self.last_frame_time = 0.0
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 2.0  # 重连延迟(秒)
        
        # 线程安全锁
        self._lock = threading.Lock()
        
        # 日志记录器
        self.logger = logging.getLogger(__name__)
        
        # 判断输入源类型
        self.is_camera = isinstance(source, int)
        self.is_file = isinstance(source, str) and Path(source).exists()
        
        if not self.is_camera and not self.is_file:
            raise ValueError(f"无效的视频源: {source}")
    
    def start_capture(self) -> bool:
        """
        开始视频采集
        
        Returns:
            bool: 启动成功返回True，否则返回False
        """
        with self._lock:
            if self.is_running:
                self.logger.warning("视频采集已在运行中")
                return True
            
            try:
                # 创建VideoCapture对象
                self.cap = cv2.VideoCapture(self.source)
                
                if not self.cap.isOpened():
                    self.logger.error(f"无法打开视频源: {self.source}")
                    return False
                
                # 设置缓冲区大小以减少延迟
                if self.is_camera:
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                
                # 验证能否读取帧
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.logger.error("无法从视频源读取帧")
                    self.cap.release()
                    return False
                
                self.is_running = True
                self.reconnect_attempts = 0
                self.last_frame_time = time.time()
                
                self.logger.info(f"视频采集启动成功，源: {self.source}, 目标帧率: {self.target_fps}fps")
                return True
                
            except Exception as e:
                self.logger.error(f"启动视频采集时发生错误: {e}")
                if self.cap:
                    self.cap.release()
                return False
    
    def stop_capture(self) -> None:
        """停止视频采集"""
        with self._lock:
            if not self.is_running:
                return
            
            self.is_running = False
            
            if self.cap:
                self.cap.release()
                self.cap = None
            
            self.logger.info("视频采集已停止")
    
    def get_frame(self) -> Optional[np.ndarray]:
        """
        获取视频帧
        
        Returns:
            Optional[np.ndarray]: 成功返回帧数据，失败返回None
        """
        if not self.is_running or not self.cap:
            return None
        
        # 帧率控制
        current_time = time.time()
        time_since_last_frame = current_time - self.last_frame_time
        
        if time_since_last_frame < self.frame_interval:
            # 等待到下一帧时间
            sleep_time = self.frame_interval - time_since_last_frame
            time.sleep(sleep_time)
        
        try:
            ret, frame = self.cap.read()
            
            if not ret or frame is None:
                self.logger.warning("读取视频帧失败")
                
                # 对于摄像头，尝试重连
                if self.is_camera:
                    self._handle_connection_loss()
                else:
                    # 对于视频文件，检查是否到达末尾
                    if self.cap.get(cv2.CAP_PROP_POS_FRAMES) >= self.cap.get(cv2.CAP_PROP_FRAME_COUNT):
                        self.logger.info("视频文件播放完毕")
                    else:
                        self.logger.error("视频文件读取错误")
                
                return None
            
            self.last_frame_time = time.time()
            self.reconnect_attempts = 0  # 重置重连计数
            
            return frame
            
        except Exception as e:
            self.logger.error(f"获取视频帧时发生错误: {e}")
            self._handle_connection_loss()
            return None
    
    def is_connected(self) -> bool:
        """
        检查连接状态
        
        Returns:
            bool: 连接正常返回True，否则返回False
        """
        if not self.is_running or not self.cap:
            return False
        
        try:
            # 检查VideoCapture对象是否仍然打开
            return self.cap.isOpened()
        except:
            return False
    
    def reconnect(self) -> bool:
        """
        重新连接视频源
        
        Returns:
            bool: 重连成功返回True，否则返回False
        """
        self.logger.info(f"尝试重新连接视频源: {self.source}")
        
        # 先停止当前连接
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # 等待一段时间后重连
        time.sleep(self.reconnect_delay)
        
        try:
            self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                self.logger.error("重连失败: 无法打开视频源")
                return False
            
            # 设置缓冲区大小
            if self.is_camera:
                self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # 验证能否读取帧
            ret, frame = self.cap.read()
            if not ret or frame is None:
                self.logger.error("重连失败: 无法读取帧")
                self.cap.release()
                return False
            
            self.logger.info("视频源重连成功")
            return True
            
        except Exception as e:
            self.logger.error(f"重连时发生错误: {e}")
            return False
    
    def _handle_connection_loss(self) -> None:
        """
        处理连接丢失情况
        
        实现需求1.2: 视频流中断时记录中断事件并尝试重新连接
        """
        self.reconnect_attempts += 1
        
        self.logger.warning(f"检测到视频流中断，第{self.reconnect_attempts}次尝试重连")
        
        if self.reconnect_attempts <= self.max_reconnect_attempts:
            if self.reconnect():
                self.logger.info("视频流重连成功")
                self.reconnect_attempts = 0
            else:
                self.logger.error(f"第{self.reconnect_attempts}次重连失败")
        else:
            self.logger.error(f"达到最大重连次数({self.max_reconnect_attempts})，停止重连尝试")
            self.is_running = False
    
    def get_video_info(self) -> dict:
        """
        获取视频信息
        
        Returns:
            dict: 包含视频信息的字典
        """
        if not self.cap or not self.cap.isOpened():
            return {}
        
        try:
            info = {
                'width': int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)),
                'fps': self.cap.get(cv2.CAP_PROP_FPS),
                'frame_count': int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) if not self.is_camera else -1,
                'current_frame': int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)) if not self.is_camera else -1,
                'source': self.source,
                'is_camera': self.is_camera,
                'target_fps': self.target_fps
            }
            return info
        except:
            return {}
    
    def set_resolution(self, width: int, height: int) -> bool:
        """
        设置视频分辨率 (仅对摄像头有效)
        
        Args:
            width: 宽度
            height: 高度
            
        Returns:
            bool: 设置成功返回True
        """
        if not self.is_camera or not self.cap:
            return False
        
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            
            # 验证设置是否生效
            actual_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            if actual_width == width and actual_height == height:
                self.logger.info(f"分辨率设置成功: {width}x{height}")
                return True
            else:
                self.logger.warning(f"分辨率设置部分成功: 请求{width}x{height}, 实际{actual_width}x{actual_height}")
                return False
                
        except Exception as e:
            self.logger.error(f"设置分辨率时发生错误: {e}")
            return False
    
    def __del__(self):
        """析构函数，确保资源释放"""
        self.stop_capture()