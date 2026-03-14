"""
演示应用程序

整合演示模式和可视化功能的完整演示应用。
需求: 10.1, 10.2, 10.3, 10.4, 10.5
"""

import cv2
import time
import threading
from typing import Optional, Dict, Any, List
from pathlib import Path

from .demo_mode import DemoMode, DemoVideo
from .visualization import ComprehensiveVisualizer, VisualizationTheme
from ..core.interfaces import DetectionResult, DetectionType, BoundingBox
from ..detection.detection_system import DetectionSystem
from ..core.models import SystemConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)


class DemoApplication:
    """
    演示应用程序
    
    提供完整的演示功能，包括视频播放、检测可视化和报警展示。
    """
    
    def __init__(self, demo_videos_dir: str = "demo_videos"):
        """
        初始化演示应用
        
        Args:
            demo_videos_dir: 演示视频目录
        """
        self.demo_mode = DemoMode(demo_videos_dir)
        self.visualizer = ComprehensiveVisualizer()
        self.detection_system: Optional[DetectionSystem] = None
        
        # 演示状态
        self.is_running = False
        self.current_frame: Optional[Any] = None
        self.display_window_name = "Kitchen Safety Detection Demo"
        
        # 演示配置
        self.enable_detection = True
        self.enable_visualization = True
        self.auto_reset_interval = 300  # 5分钟自动重置
        self.last_reset_time = time.time()
        
        # 模拟检测数据（用于演示）
        self.demo_detection_enabled = True
        self.demo_detection_interval = 2.0  # 每2秒生成一次模拟检测
        self.last_demo_detection_time = time.time()
        
        logger.info("演示应用程序初始化完成")
    
    def initialize_detection_system(self, config: Optional[SystemConfig] = None) -> bool:
        """
        初始化检测系统
        
        Args:
            config: 系统配置
            
        Returns:
            是否初始化成功
        """
        try:
            if config is None:
                config = SystemConfig(
                    video_input_source="demo",
                    detection_fps=15,
                    confidence_threshold=0.6,
                    enable_sound_alert=False,  # 演示模式下禁用声音
                    enable_email_alert=False
                )
            
            self.detection_system = DetectionSystem(config)
            self.demo_mode.set_detection_system(self.detection_system)
            
            logger.info("检测系统初始化成功")
            return True
            
        except Exception as e:
            logger.error(f"检测系统初始化失败: {e}")
            return False
    
    def start_demo(self, scenario: str = "comprehensive") -> bool:
        """
        启动演示
        
        Args:
            scenario: 演示场景名称
            
        Returns:
            是否启动成功
        """
        try:
            logger.info(f"启动演示场景: {scenario}")
            
            # 创建演示场景
            if not self.demo_mode.create_demo_scenario(scenario):
                logger.error("创建演示场景失败")
                return False
            
            # 设置帧处理回调
            self.demo_mode.start_playback(self._process_frame)
            
            # 创建显示窗口
            cv2.namedWindow(self.display_window_name, cv2.WINDOW_AUTOSIZE)
            cv2.setMouseCallback(self.display_window_name, self._mouse_callback)
            
            self.is_running = True
            self.last_reset_time = time.time()
            
            # 启动主循环
            self._main_loop()
            
            return True
            
        except Exception as e:
            logger.error(f"启动演示失败: {e}")
            return False
    
    def stop_demo(self) -> None:
        """停止演示"""
        logger.info("停止演示")
        
        self.is_running = False
        self.demo_mode.stop_playback()
        
        # 关闭显示窗口
        cv2.destroyAllWindows()
        
        # 清理资源
        self.demo_mode.cleanup()
    
    def _process_frame(self, frame: Any) -> None:
        """
        处理视频帧
        
        Args:
            frame: 视频帧
        """
        try:
            if frame is None:
                return
            
            self.current_frame = frame.copy()
            
            # 生成模拟检测结果
            detections = []
            alerts = []
            
            if self.demo_detection_enabled:
                detections = self._generate_demo_detections(frame)
                alerts = self._generate_demo_alerts(detections)
            
            # 如果有真实检测系统，使用真实检测
            if self.detection_system and self.enable_detection:
                try:
                    # 这里可以调用真实的检测系统
                    # real_detections = self.detection_system.process_frame(frame)
                    # detections.extend(real_detections)
                    pass
                except Exception as e:
                    logger.error(f"真实检测处理失败: {e}")
            
            # 添加检测结果到演示数据
            for detection in detections:
                self.demo_mode.add_demo_detection(detection)
            
            # 添加报警到演示数据
            for alert in alerts:
                self.demo_mode.add_demo_alert(**alert)
            
            # 可视化处理
            if self.enable_visualization:
                additional_info = self._get_additional_info()
                vis_frame = self.visualizer.visualize_frame(
                    frame, detections, alerts, additional_info
                )
                self.current_frame = vis_frame
            
        except Exception as e:
            logger.error(f"帧处理失败: {e}")
    
    def _generate_demo_detections(self, frame: Any) -> List[DetectionResult]:
        """生成模拟检测结果"""
        current_time = time.time()
        
        # 控制检测生成频率
        if current_time - self.last_demo_detection_time < self.demo_detection_interval:
            return []
        
        self.last_demo_detection_time = current_time
        
        detections = []
        frame_height, frame_width = frame.shape[:2]
        
        # 模拟人员检测
        if current_time % 10 < 8:  # 80%的时间有人员
            person_bbox = BoundingBox(
                x=int(frame_width * 0.3),
                y=int(frame_height * 0.2),
                width=int(frame_width * 0.15),
                height=int(frame_height * 0.4),
                confidence=0.85 + (current_time % 1) * 0.1
            )
            
            detections.append(DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=person_bbox,
                timestamp=current_time,
                frame_id=int(current_time * 15)  # 假设15fps
            ))
        
        # 模拟灶台检测
        stove_bbox = BoundingBox(
            x=int(frame_width * 0.6),
            y=int(frame_height * 0.5),
            width=int(frame_width * 0.2),
            height=int(frame_height * 0.3),
            confidence=0.75 + (current_time % 1) * 0.15
        )
        
        detections.append(DetectionResult(
            detection_type=DetectionType.STOVE,
            bbox=stove_bbox,
            timestamp=current_time,
            frame_id=int(current_time * 15)
        ))
        
        # 模拟火焰检测（间歇性）
        if current_time % 15 < 10:  # 2/3的时间有火焰
            flame_bbox = BoundingBox(
                x=int(frame_width * 0.65),
                y=int(frame_height * 0.55),
                width=int(frame_width * 0.08),
                height=int(frame_height * 0.1),
                confidence=0.70 + (current_time % 1) * 0.2
            )
            
            detections.append(DetectionResult(
                detection_type=DetectionType.FLAME,
                bbox=flame_bbox,
                timestamp=current_time,
                frame_id=int(current_time * 15)
            ))
        
        return detections
    
    def _generate_demo_alerts(self, detections: List[DetectionResult]) -> List[Dict[str, Any]]:
        """生成模拟报警"""
        alerts = []
        current_time = time.time()
        
        # 检查是否有人员和火焰
        has_person = any(d.detection_type == DetectionType.PERSON for d in detections)
        has_flame = any(d.detection_type == DetectionType.FLAME for d in detections)
        
        # 模拟跌倒检测报警（低频率）
        if has_person and current_time % 60 < 5:  # 每分钟5秒钟模拟跌倒
            person_detection = next(d for d in detections if d.detection_type == DetectionType.PERSON)
            alerts.append({
                'type': 'fall_detected',
                'message': '检测到人员跌倒！',
                'location': person_detection.bbox.center,
                'level': 'high',
                'duration': 8.0
            })
        
        # 模拟无人看管灶台报警
        if has_flame and not has_person and current_time % 45 < 10:  # 模拟无人看管
            flame_detection = next(d for d in detections if d.detection_type == DetectionType.FLAME)
            alerts.append({
                'type': 'unattended_stove',
                'message': '灶台无人看管！',
                'location': flame_detection.bbox.center,
                'level': 'medium',
                'duration': 6.0
            })
        
        return alerts
    
    def _get_additional_info(self) -> Dict[str, Any]:
        """获取附加信息"""
        stats = self.demo_mode.get_demo_statistics()
        playback_info = self.demo_mode.get_playback_info()
        
        return {
            'Demo Time': f"{stats.get('demo_duration', 0):.1f}s",
            'Detections': stats.get('total_detections', 0),
            'Alerts': stats.get('alerts_triggered', 0),
            'Video': playback_info.get('current_video', {}).get('name', 'None')
        }
    
    def _main_loop(self) -> None:
        """主显示循环"""
        logger.info("启动演示主循环")
        
        try:
            while self.is_running:
                # 检查自动重置
                if time.time() - self.last_reset_time > self.auto_reset_interval:
                    self._auto_reset_demo()
                
                # 显示当前帧
                if self.current_frame is not None:
                    cv2.imshow(self.display_window_name, self.current_frame)
                else:
                    # 显示等待画面
                    waiting_frame = self._create_waiting_frame()
                    cv2.imshow(self.display_window_name, waiting_frame)
                
                # 处理键盘输入
                key = cv2.waitKey(30) & 0xFF
                if key == ord('q') or key == 27:  # 'q' 或 ESC 退出
                    break
                elif key == ord(' '):  # 空格暂停/恢复
                    self._toggle_playback()
                elif key == ord('r'):  # 'r' 重置演示
                    self._reset_demo()
                elif key == ord('t'):  # 't' 切换主题
                    self._toggle_theme()
                elif key == ord('d'):  # 'd' 切换检测
                    self._toggle_detection()
                elif key == ord('h'):  # 'h' 显示帮助
                    self._show_help()
                
        except KeyboardInterrupt:
            logger.info("用户中断演示")
        except Exception as e:
            logger.error(f"演示主循环出错: {e}")
        finally:
            self.stop_demo()
    
    def _create_waiting_frame(self) -> Any:
        """创建等待画面"""
        frame = cv2.imread("demo_placeholder.jpg") if Path("demo_placeholder.jpg").exists() else None
        
        if frame is None:
            frame = self._create_default_waiting_frame()
        
        return frame
    
    def _create_default_waiting_frame(self) -> Any:
        """创建默认等待画面"""
        frame = cv2.zeros((480, 640, 3), dtype=cv2.uint8)
        
        # 绘制标题
        cv2.putText(
            frame,
            "Kitchen Safety Detection System",
            (100, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            (255, 255, 255),
            2
        )
        
        cv2.putText(
            frame,
            "Demo Mode",
            (250, 250),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 255, 255),
            2
        )
        
        # 绘制控制说明
        controls = [
            "Controls:",
            "SPACE - Pause/Resume",
            "R - Reset Demo", 
            "T - Toggle Theme",
            "D - Toggle Detection",
            "H - Show Help",
            "Q/ESC - Quit"
        ]
        
        y_offset = 300
        for control in controls:
            cv2.putText(
                frame,
                control,
                (50, y_offset),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                1
            )
            y_offset += 25
        
        return frame
    
    def _mouse_callback(self, event, x, y, flags, param) -> None:
        """鼠标回调处理"""
        if event == cv2.EVENT_LBUTTONDOWN:
            logger.debug(f"鼠标点击: ({x}, {y})")
            # 可以添加交互功能
    
    def _toggle_playback(self) -> None:
        """切换播放/暂停"""
        if self.demo_mode.is_paused:
            self.demo_mode.resume_playback()
            logger.info("恢复播放")
        else:
            self.demo_mode.pause_playback()
            logger.info("暂停播放")
    
    def _reset_demo(self) -> None:
        """重置演示"""
        logger.info("手动重置演示")
        self.demo_mode.reset_demo_data()
        self.visualizer.clear_all()
        self.last_reset_time = time.time()
    
    def _auto_reset_demo(self) -> None:
        """自动重置演示"""
        logger.info("自动重置演示")
        self._reset_demo()
    
    def _toggle_theme(self) -> None:
        """切换可视化主题"""
        themes = [VisualizationTheme.DEFAULT, VisualizationTheme.DARK, VisualizationTheme.HIGH_CONTRAST]
        current_index = themes.index(self.visualizer.theme)
        next_theme = themes[(current_index + 1) % len(themes)]
        
        self.visualizer.set_theme(next_theme)
        logger.info(f"切换主题: {next_theme.value}")
    
    def _toggle_detection(self) -> None:
        """切换检测功能"""
        self.demo_detection_enabled = not self.demo_detection_enabled
        status = "启用" if self.demo_detection_enabled else "禁用"
        logger.info(f"检测功能: {status}")
    
    def _show_help(self) -> None:
        """显示帮助信息"""
        help_text = """
厨房安全检测系统演示

控制键:
- 空格键: 暂停/恢复播放
- R: 重置演示数据
- T: 切换可视化主题
- D: 启用/禁用检测
- H: 显示此帮助
- Q/ESC: 退出演示

功能说明:
- 绿色框: 人员检测
- 橙色框: 灶台检测  
- 红色框: 火焰检测
- 闪烁圆圈: 报警位置
- 左下角面板: 当前报警
- 右上角面板: 统计信息

演示会自动重置以展示不同场景。
        """
        
        print(help_text)
        logger.info("显示帮助信息")


def main():
    """演示应用主函数"""
    print("厨房安全检测系统 - 演示应用")
    print("=" * 50)
    
    try:
        # 创建演示应用
        app = DemoApplication()
        
        # 初始化检测系统（可选）
        app.initialize_detection_system()
        
        # 启动演示
        if app.start_demo("comprehensive"):
            print("演示启动成功")
        else:
            print("演示启动失败")
            
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    except Exception as e:
        logger.error(f"演示应用出错: {e}")
        print(f"错误: {e}")


if __name__ == "__main__":
    main()