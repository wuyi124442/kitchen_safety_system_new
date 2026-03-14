"""
姿态分析器集成示例

演示如何将MediaPipe姿态分析器与YOLO检测器集成使用。
"""

import cv2
import numpy as np
import time
from typing import List, Optional

from .pose_analyzer import PoseAnalyzer
from ..detection.yolo_detector import YOLODetector
from ..core.interfaces import DetectionResult, DetectionType, BoundingBox
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PoseDetectionIntegration:
    """姿态检测集成类"""
    
    def __init__(self, yolo_model_path: str = "yolo/yolo11n.pt"):
        """
        初始化集成系统
        
        Args:
            yolo_model_path: YOLO模型路径
        """
        # 初始化YOLO检测器
        self.yolo_detector = YOLODetector()
        if not self.yolo_detector.load_model(yolo_model_path):
            logger.error(f"Failed to load YOLO model: {yolo_model_path}")
            raise RuntimeError("YOLO model loading failed")
        
        # 初始化姿态分析器
        self.pose_analyzer = PoseAnalyzer(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        
        logger.info("Pose detection integration initialized")
    
    def process_frame(self, frame: np.ndarray) -> dict:
        """
        处理单帧图像
        
        Args:
            frame: 输入视频帧
            
        Returns:
            dict: 处理结果，包含检测和姿态信息
        """
        results = {
            'detections': [],
            'pose_results': [],
            'fall_detected': False,
            'timestamp': time.time()
        }
        
        try:
            # 1. YOLO目标检测
            detections = self.yolo_detector.detect(frame)
            results['detections'] = detections
            
            # 2. 对每个检测到的人员进行姿态分析
            person_detections = [d for d in detections if d.detection_type == DetectionType.PERSON]
            
            for person_detection in person_detections:
                pose_result = self.pose_analyzer.analyze_pose(frame, person_detection.bbox)
                results['pose_results'].append({
                    'detection': person_detection,
                    'pose': pose_result
                })
                
                # 检查是否有跌倒
                if pose_result.is_fall_detected:
                    results['fall_detected'] = True
                    logger.warning(f"Fall detected with confidence: {pose_result.fall_confidence:.2f}")
            
            logger.debug(f"Processed frame: {len(person_detections)} persons, "
                        f"fall_detected={results['fall_detected']}")
            
        except Exception as e:
            logger.error(f"Error processing frame: {e}")
        
        return results
    
    def run_webcam_integration(self, camera_id: int = 0):
        """运行摄像头集成演示"""
        logger.info(f"Starting webcam integration demo with camera {camera_id}")
        
        cap = cv2.VideoCapture(camera_id)
        if not cap.isOpened():
            logger.error(f"Cannot open camera {camera_id}")
            return
        
        # 设置摄像头参数
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        logger.info("Press 'q' to quit, 's' to save screenshot")
        
        frame_count = 0
        fps_start_time = time.time()
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    logger.warning("Failed to read frame")
                    break
                
                frame_count += 1
                
                # 处理帧
                start_time = time.time()
                results = self.process_frame(frame)
                processing_time = time.time() - start_time
                
                # 可视化结果
                vis_frame = self._visualize_results(frame, results)
                
                # 计算FPS
                if frame_count % 30 == 0:
                    fps = 30 / (time.time() - fps_start_time)
                    fps_start_time = time.time()
                    logger.info(f"FPS: {fps:.1f}, Processing time: {processing_time:.3f}s")
                
                # 显示信息
                self._draw_performance_info(vis_frame, 
                                          fps if 'fps' in locals() else 0, 
                                          processing_time)
                
                # 显示结果
                cv2.imshow('YOLO + MediaPose Integration Demo', vis_frame)
                
                # 处理按键
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    filename = f"integration_demo_{int(time.time())}.jpg"
                    cv2.imwrite(filename, vis_frame)
                    logger.info(f"Screenshot saved: {filename}")
        
        except KeyboardInterrupt:
            logger.info("Demo interrupted by user")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            logger.info("Integration demo finished")
    
    def _visualize_results(self, frame: np.ndarray, results: dict) -> np.ndarray:
        """可视化处理结果"""
        vis_frame = frame.copy()
        
        # 1. 绘制YOLO检测结果
        for detection in results['detections']:
            self._draw_detection(vis_frame, detection)
        
        # 2. 绘制姿态分析结果
        for pose_data in results['pose_results']:
            self._draw_pose_analysis(vis_frame, pose_data)
        
        # 3. 绘制跌倒警报
        if results['fall_detected']:
            self._draw_fall_alert(vis_frame)
        
        return vis_frame
    
    def _draw_detection(self, frame: np.ndarray, detection: DetectionResult):
        """绘制检测结果"""
        bbox = detection.bbox
        
        # 选择颜色
        colors = {
            DetectionType.PERSON: (0, 255, 0),  # 绿色
            DetectionType.STOVE: (255, 0, 0),   # 蓝色
            DetectionType.FLAME: (0, 0, 255)    # 红色
        }
        color = colors.get(detection.detection_type, (255, 255, 255))
        
        # 绘制边界框
        cv2.rectangle(frame,
                     (bbox.x, bbox.y),
                     (bbox.x + bbox.width, bbox.y + bbox.height),
                     color, 2)
        
        # 绘制标签
        label = f"{detection.detection_type.value}: {bbox.confidence:.2f}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
        
        cv2.rectangle(frame,
                     (bbox.x, bbox.y - label_size[1] - 10),
                     (bbox.x + label_size[0], bbox.y),
                     color, -1)
        
        cv2.putText(frame, label,
                   (bbox.x, bbox.y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    def _draw_pose_analysis(self, frame: np.ndarray, pose_data: dict):
        """绘制姿态分析结果"""
        detection = pose_data['detection']
        pose_result = pose_data['pose']
        
        if not pose_result.keypoints:
            return
        
        # 绘制关键点
        for keypoint in pose_result.keypoints:
            if keypoint.visible and keypoint.confidence > 0.5:
                center = (int(keypoint.x), int(keypoint.y))
                cv2.circle(frame, center, 3, (0, 255, 255), -1)
        
        # 绘制姿态状态
        bbox = detection.bbox
        status_y = bbox.y + bbox.height + 20
        
        if pose_result.is_fall_detected:
            status_text = f"FALL! ({pose_result.fall_confidence:.2f})"
            color = (0, 0, 255)
        else:
            # 检查是否为正常动作
            is_normal = self.pose_analyzer.is_normal_action(pose_result)
            if is_normal:
                status_text = "Normal Action"
                color = (0, 255, 255)
            else:
                status_text = "Standing"
                color = (0, 255, 0)
        
        cv2.putText(frame, status_text,
                   (bbox.x, status_y),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
    
    def _draw_fall_alert(self, frame: np.ndarray):
        """绘制跌倒警报"""
        # 闪烁的红色警报
        if int(time.time() * 6) % 2:  # 6Hz闪烁
            overlay = frame.copy()
            cv2.rectangle(overlay, (0, 0), (frame.shape[1], 100), (0, 0, 255), -1)
            cv2.addWeighted(frame, 0.7, overlay, 0.3, 0, frame)
        
        # 警报文字
        alert_text = "⚠️ FALL DETECTED! ⚠️"
        text_size = cv2.getTextSize(alert_text, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
        text_x = (frame.shape[1] - text_size[0]) // 2
        
        cv2.putText(frame, alert_text, (text_x, 50),
                   cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
    
    def _draw_performance_info(self, frame: np.ndarray, fps: float, processing_time: float):
        """绘制性能信息"""
        info_y = frame.shape[0] - 60
        
        # 背景
        cv2.rectangle(frame, (10, info_y - 10), (300, frame.shape[0] - 10), 
                     (0, 0, 0, 128), -1)
        
        # 性能信息
        info_lines = [
            f"FPS: {fps:.1f}",
            f"Processing: {processing_time*1000:.1f}ms"
        ]
        
        for i, line in enumerate(info_lines):
            cv2.putText(frame, line, (20, info_y + i * 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='YOLO + MediaPipe Integration Demo')
    parser.add_argument('--model', type=str, default='yolo/yolo11n.pt',
                       help='YOLO model path')
    parser.add_argument('--camera', type=int, default=0, 
                       help='Camera ID')
    
    args = parser.parse_args()
    
    try:
        integration = PoseDetectionIntegration(args.model)
        integration.run_webcam_integration(args.camera)
    except Exception as e:
        logger.error(f"Integration demo failed: {e}")


if __name__ == "__main__":
    main()