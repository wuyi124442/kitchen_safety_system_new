"""
YOLO检测器与视频处理模块集成示例

演示如何将YOLO检测器与VideoCapture和VideoProcessor模块集成使用。
"""

import cv2
import numpy as np
import time
import sys
import os
from typing import List, Optional

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from kitchen_safety_system.detection.yolo_detector import YOLODetector
from kitchen_safety_system.video.video_capture import VideoCapture
from kitchen_safety_system.video.video_processor import VideoProcessor
from kitchen_safety_system.core.interfaces import DetectionResult, DetectionType
from kitchen_safety_system.utils.logger import get_logger


class KitchenSafetyDetectionPipeline:
    """
    厨房安全检测流水线
    
    集成视频采集、预处理和YOLO目标检测功能。
    """
    
    def __init__(self, 
                 video_source: str = "0",
                 confidence_threshold: float = 0.5,
                 target_fps: int = 15):
        """
        初始化检测流水线
        
        Args:
            video_source: 视频源（摄像头编号或文件路径）
            confidence_threshold: YOLO检测置信度阈值
            target_fps: 目标帧率
        """
        self.logger = get_logger(__name__)
        self.video_source = video_source
        self.target_fps = target_fps
        
        # 初始化各个模块
        self.video_capture: Optional[VideoCapture] = None
        self.video_processor: Optional[VideoProcessor] = None
        self.yolo_detector: Optional[YOLODetector] = None
        
        # 统计信息
        self.frame_count = 0
        self.detection_stats = {
            DetectionType.PERSON: 0,
            DetectionType.STOVE: 0,
            DetectionType.FLAME: 0
        }
        
        self._initialize_modules(confidence_threshold)
    
    def _initialize_modules(self, confidence_threshold: float) -> bool:
        """初始化各个模块"""
        try:
            # 初始化视频采集器
            self.logger.info(f"初始化视频采集器: {self.video_source}")
            if self.video_source.isdigit():
                source = int(self.video_source)
            else:
                source = self.video_source
            
            self.video_capture = VideoCapture(source, target_fps=self.target_fps)
            
            # 初始化视频处理器
            self.logger.info("初始化视频处理器")
            self.video_processor = VideoProcessor(
                target_size=(640, 480),
                enable_enhancement=True
            )
            
            # 初始化YOLO检测器
            self.logger.info("初始化YOLO检测器")
            self.yolo_detector = YOLODetector(confidence_threshold=confidence_threshold)
            
            # 检查初始化状态
            if not self.yolo_detector.is_loaded:
                self.logger.error("YOLO检测器初始化失败")
                return False
            
            self.logger.info("所有模块初始化成功")
            return True
            
        except Exception as e:
            self.logger.error(f"模块初始化失败: {e}")
            return False
    
    def start_detection(self, duration: Optional[float] = None, 
                       show_visualization: bool = True,
                       save_results: bool = False) -> bool:
        """
        开始检测流程
        
        Args:
            duration: 检测持续时间（秒），None表示持续运行
            show_visualization: 是否显示可视化结果
            save_results: 是否保存检测结果
            
        Returns:
            bool: 检测是否成功启动
        """
        if not all([self.video_capture, self.video_processor, self.yolo_detector]):
            self.logger.error("模块未正确初始化")
            return False
        
        # 启动视频采集
        if not self.video_capture.start_capture():
            self.logger.error("视频采集启动失败")
            return False
        
        self.logger.info("开始检测流程")
        start_time = time.time()
        
        try:
            while True:
                # 检查持续时间
                if duration and (time.time() - start_time) > duration:
                    self.logger.info(f"检测完成，持续时间: {duration}秒")
                    break
                
                # 获取视频帧
                frame = self.video_capture.get_frame()
                if frame is None:
                    self.logger.warning("无法获取视频帧")
                    time.sleep(0.1)
                    continue
                
                # 处理帧
                processed_frame = self._process_frame(frame)
                if processed_frame is None:
                    continue
                
                # 执行检测
                detections = self._detect_objects(processed_frame)
                
                # 更新统计
                self._update_stats(detections)
                
                # 可视化结果
                if show_visualization:
                    result_frame = self._visualize_results(processed_frame, detections)
                    cv2.imshow('Kitchen Safety Detection', result_frame)
                    
                    # 处理按键
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        self.logger.info("用户退出检测")
                        break
                    elif key == ord('s') and save_results:
                        self._save_frame(result_frame, detections)
                
                # 保存结果
                if save_results and self.frame_count % 30 == 0:  # 每30帧保存一次
                    self._save_detection_results(detections)
                
                self.frame_count += 1
                
                # 显示进度
                if self.frame_count % 100 == 0:
                    self._log_progress()
        
        except KeyboardInterrupt:
            self.logger.info("检测被用户中断")
        
        except Exception as e:
            self.logger.error(f"检测过程中出现错误: {e}")
            return False
        
        finally:
            self._cleanup()
        
        return True
    
    def _process_frame(self, frame: np.ndarray) -> Optional[np.ndarray]:
        """处理视频帧"""
        try:
            # 检查视频质量
            quality = self.video_processor.check_quality(frame)
            if quality < 0.3:  # 质量过低
                self.logger.debug(f"视频质量过低: {quality:.2f}")
                return None
            
            # 预处理帧
            processed_frame = self.video_processor.process_frame(frame)
            return processed_frame
            
        except Exception as e:
            self.logger.error(f"帧处理失败: {e}")
            return None
    
    def _detect_objects(self, frame: np.ndarray) -> List[DetectionResult]:
        """执行目标检测"""
        try:
            detections = self.yolo_detector.detect(frame)
            return detections
        except Exception as e:
            self.logger.error(f"目标检测失败: {e}")
            return []
    
    def _update_stats(self, detections: List[DetectionResult]) -> None:
        """更新检测统计"""
        for detection in detections:
            if detection.detection_type in self.detection_stats:
                self.detection_stats[detection.detection_type] += 1
    
    def _visualize_results(self, frame: np.ndarray, 
                          detections: List[DetectionResult]) -> np.ndarray:
        """可视化检测结果"""
        # 使用YOLO检测器的可视化功能
        result_frame = self.yolo_detector.visualize_detections(frame, detections)
        
        # 添加统计信息
        y_offset = 30
        for detection_type, count in self.detection_stats.items():
            text = f"{detection_type.value}: {count}"
            cv2.putText(result_frame, text, (10, y_offset), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            y_offset += 25
        
        # 添加帧计数和FPS
        fps = self.target_fps  # 简化显示
        cv2.putText(result_frame, f"Frame: {self.frame_count}", (10, y_offset), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        cv2.putText(result_frame, f"FPS: {fps}", (10, y_offset + 25), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return result_frame
    
    def _save_frame(self, frame: np.ndarray, detections: List[DetectionResult]) -> None:
        """保存检测帧"""
        timestamp = int(time.time())
        filename = f"detection_frame_{timestamp}_{self.frame_count}.jpg"
        cv2.imwrite(filename, frame)
        self.logger.info(f"帧已保存: {filename}, 检测数: {len(detections)}")
    
    def _save_detection_results(self, detections: List[DetectionResult]) -> None:
        """保存检测结果到日志"""
        if detections:
            detection_summary = {}
            for detection in detections:
                det_type = detection.detection_type.value
                if det_type not in detection_summary:
                    detection_summary[det_type] = []
                detection_summary[det_type].append({
                    'confidence': detection.bbox.confidence,
                    'position': (detection.bbox.x, detection.bbox.y),
                    'size': (detection.bbox.width, detection.bbox.height)
                })
            
            self.logger.info(f"帧 {self.frame_count} 检测结果: {detection_summary}")
    
    def _log_progress(self) -> None:
        """记录进度信息"""
        yolo_stats = self.yolo_detector.get_performance_stats()
        self.logger.info(f"处理进度 - 帧数: {self.frame_count}, "
                        f"平均FPS: {yolo_stats['average_fps']:.1f}, "
                        f"检测统计: {dict(self.detection_stats)}")
    
    def _cleanup(self) -> None:
        """清理资源"""
        if self.video_capture:
            self.video_capture.stop_capture()
        
        cv2.destroyAllWindows()
        
        # 显示最终统计
        self.logger.info("=== 检测完成统计 ===")
        self.logger.info(f"总处理帧数: {self.frame_count}")
        self.logger.info(f"检测统计: {dict(self.detection_stats)}")
        
        if self.yolo_detector:
            yolo_stats = self.yolo_detector.get_performance_stats()
            self.logger.info(f"YOLO性能: 平均FPS {yolo_stats['average_fps']:.1f}, "
                           f"平均推理时间 {yolo_stats['average_inference_time']:.3f}s")


def demo_integration():
    """集成演示"""
    print("=== 厨房安全检测系统集成演示 ===")
    
    # 创建检测流水线
    pipeline = KitchenSafetyDetectionPipeline(
        video_source="0",  # 使用默认摄像头
        confidence_threshold=0.3,
        target_fps=15
    )
    
    print("按 'q' 退出，按 's' 保存当前帧")
    print("开始检测...")
    
    # 运行检测（30秒演示）
    success = pipeline.start_detection(
        duration=30.0,
        show_visualization=True,
        save_results=True
    )
    
    if success:
        print("✅ 集成演示完成")
    else:
        print("❌ 集成演示失败")


def demo_file_processing(video_file: str):
    """文件处理演示"""
    print(f"=== 处理视频文件: {video_file} ===")
    
    if not os.path.exists(video_file):
        print(f"❌ 视频文件不存在: {video_file}")
        return
    
    # 创建检测流水线
    pipeline = KitchenSafetyDetectionPipeline(
        video_source=video_file,
        confidence_threshold=0.5,
        target_fps=15
    )
    
    print("开始处理视频文件...")
    
    # 处理整个视频文件
    success = pipeline.start_detection(
        duration=None,  # 处理整个文件
        show_visualization=True,
        save_results=True
    )
    
    if success:
        print("✅ 视频文件处理完成")
    else:
        print("❌ 视频文件处理失败")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="YOLO检测器集成演示")
    parser.add_argument('--mode', choices=['camera', 'file'], 
                       default='camera', help='演示模式')
    parser.add_argument('--video', help='视频文件路径（file模式）')
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'camera':
            demo_integration()
        elif args.mode == 'file':
            if not args.video:
                print("❌ file模式需要指定视频文件路径")
                return
            demo_file_processing(args.video)
    except Exception as e:
        print(f"❌ 演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()