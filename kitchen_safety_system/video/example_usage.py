#!/usr/bin/env python3
"""
VideoCapture 使用示例

展示如何在厨房安全检测系统中使用VideoCapture类。
"""

import time
import logging
from typing import Optional
import numpy as np

from .video_capture import VideoCapture
from ..core.config import ConfigManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class VideoStreamManager:
    """
    视频流管理器
    
    封装VideoCapture的使用，提供更高级的视频流管理功能。
    """
    
    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """
        初始化视频流管理器
        
        Args:
            config_manager: 配置管理器实例
        """
        self.config_manager = config_manager or ConfigManager()
        self.video_capture: Optional[VideoCapture] = None
        self.is_running = False
        self.frame_count = 0
        self.logger = logging.getLogger(__name__)
    
    def initialize(self) -> bool:
        """
        初始化视频流
        
        Returns:
            bool: 初始化成功返回True
        """
        try:
            # 从配置获取视频源
            video_source = self.config_manager.get_config('video.input_source')
            target_fps = self.config_manager.get_config('detection.detection_fps')
            
            # 处理视频源类型
            if video_source.isdigit():
                source = int(video_source)
            else:
                source = video_source
            
            # 创建VideoCapture实例
            self.video_capture = VideoCapture(source=source, target_fps=target_fps)
            
            # 启动视频采集
            if not self.video_capture.start_capture():
                self.logger.error("无法启动视频采集")
                return False
            
            # 设置分辨率（如果是摄像头）
            if isinstance(source, int):
                resolution = self.config_manager.get_config('video.resolution')
                if resolution and len(resolution) == 2:
                    self.video_capture.set_resolution(resolution[0], resolution[1])
            
            self.logger.info("视频流初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"视频流初始化失败: {e}")
            return False
    
    def start_processing(self) -> bool:
        """
        开始视频处理循环
        
        Returns:
            bool: 启动成功返回True
        """
        if not self.video_capture:
            self.logger.error("视频采集器未初始化")
            return False
        
        self.is_running = True
        self.frame_count = 0
        
        self.logger.info("开始视频处理循环")
        
        try:
            while self.is_running:
                # 获取视频帧
                frame = self.video_capture.get_frame()
                
                if frame is None:
                    # 检查连接状态
                    if not self.video_capture.is_connected():
                        self.logger.warning("视频连接丢失，尝试重连...")
                        if not self.video_capture.reconnect():
                            self.logger.error("视频重连失败，停止处理")
                            break
                    continue
                
                # 处理帧
                self._process_frame(frame)
                self.frame_count += 1
                
                # 每100帧输出一次状态
                if self.frame_count % 100 == 0:
                    self.logger.info(f"已处理 {self.frame_count} 帧")
                
                # 检查系统状态
                if not self._check_system_health():
                    self.logger.warning("系统健康检查失败，停止处理")
                    break
            
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，停止视频处理")
        except Exception as e:
            self.logger.error(f"视频处理过程中发生错误: {e}")
        finally:
            self.stop_processing()
        
        return True
    
    def stop_processing(self) -> None:
        """停止视频处理"""
        self.is_running = False
        
        if self.video_capture:
            self.video_capture.stop_capture()
        
        self.logger.info(f"视频处理已停止，总共处理了 {self.frame_count} 帧")
    
    def _process_frame(self, frame: np.ndarray) -> None:
        """
        处理单个视频帧
        
        Args:
            frame: 视频帧数据
        """
        # 这里是处理帧的逻辑
        # 在实际系统中，这里会调用目标检测、姿态识别等模块
        
        # 示例：简单的帧信息记录
        height, width = frame.shape[:2]
        
        # 每1000帧记录一次详细信息
        if self.frame_count % 1000 == 0:
            self.logger.debug(f"处理帧 {self.frame_count}: 尺寸 {width}x{height}")
    
    def _check_system_health(self) -> bool:
        """
        检查系统健康状态
        
        Returns:
            bool: 系统健康返回True
        """
        # 检查视频连接状态
        if not self.video_capture or not self.video_capture.is_connected():
            return False
        
        # 这里可以添加更多健康检查逻辑
        # 例如：CPU使用率、内存使用率、磁盘空间等
        
        return True
    
    def get_status(self) -> dict:
        """
        获取视频流状态信息
        
        Returns:
            dict: 状态信息字典
        """
        status = {
            'is_running': self.is_running,
            'frame_count': self.frame_count,
            'video_capture_initialized': self.video_capture is not None,
            'video_connected': False,
            'video_info': {}
        }
        
        if self.video_capture:
            status['video_connected'] = self.video_capture.is_connected()
            status['video_info'] = self.video_capture.get_video_info()
        
        return status


def main():
    """主函数 - 演示VideoCapture的使用"""
    print("VideoCapture 使用示例")
    print("=" * 50)
    
    # 创建视频流管理器
    stream_manager = VideoStreamManager()
    
    try:
        # 初始化视频流
        if not stream_manager.initialize():
            print("视频流初始化失败")
            return
        
        # 显示状态信息
        status = stream_manager.get_status()
        print("视频流状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
        
        # 运行一小段时间进行演示
        print("\n开始视频处理演示（10秒）...")
        
        # 在单独的线程中运行处理循环
        import threading
        
        def run_processing():
            stream_manager.start_processing()
        
        processing_thread = threading.Thread(target=run_processing)
        processing_thread.daemon = True
        processing_thread.start()
        
        # 等待10秒
        time.sleep(10)
        
        # 停止处理
        stream_manager.stop_processing()
        processing_thread.join(timeout=2)
        
        # 显示最终状态
        final_status = stream_manager.get_status()
        print("\n最终状态:")
        for key, value in final_status.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"演示过程中发生错误: {e}")
    finally:
        stream_manager.stop_processing()


if __name__ == "__main__":
    main()