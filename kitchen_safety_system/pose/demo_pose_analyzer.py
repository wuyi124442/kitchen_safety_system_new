"""
MediaPipe姿态分析器演示脚本

演示姿态检测、跌倒识别和可视化功能。
"""

import cv2
import numpy as np
import time
from typing import List, Tuple

from .pose_analyzer import PoseAnalyzer
from ..core.interfaces import BoundingBox, PoseKeypoint
from ..utils.logger import get_logger

logger = get_logger(__name__)


class PoseAnalyzerDemo:
    """姿态分析器演示类"""
    
    def __init__(self):
        """初始化演示"""
        self.pose_analyzer = PoseAnalyzer(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            model_complexity=1
        )
        
        # 可视化颜色配置
        self.colors = {
            'keypoint': (0, 255, 0),      # 绿色关键点
            'connection': (255, 0, 0),    # 蓝色连接线
            'fall_alert': (0, 0, 255),    # 红色跌倒警报
            'normal': (0, 255, 0),        # 绿色正常状态
            'bbox': (255, 255, 0)         # 青色边界框
        }
        
        # MediaPipe姿态连接定义
        self.pose_connections = [
            # 面部
            (0, 1), (1, 2), (2, 3), (3, 7),
            (0, 4), (4, 5), (5, 6), (6, 8),
            (9, 10),
            # 躯干
            (11, 12), (11, 23), (12, 24), (23, 24),
            # 左臂
            (11, 13), (13, 15), (15, 17), (15, 19), (15, 21), (17, 19),
            # 右臂
            (12, 14), (14, 16), (16, 18), (16, 20), (16, 22), (18, 20),
            # 左腿
            (23, 25), (25, 27), (27, 29), (27, 31), (29, 31),
            # 右腿
            (24, 26), (26, 28), (28, 30), (28, 32), (30, 32)
        ]
    
    def run_webcam_demo(self, camera_id: int = 0):
        """运行摄像头实时演示"""
        logger.info(f"Starting webcam demo with camera {camera_id}")
        
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
                
                # 创建模拟的人员边界框 (整个画面)
                person_bbox = BoundingBox(
                    x=0, y=0, 
                    width=frame.shape[1], 
                    height=frame.shape[0], 
                    confidence=1.0
                )
                
                # 执行姿态分析
                pose_result = self.pose_analyzer.analyze_pose(frame, person_bbox)
                
                # 可视化结果
                vis_frame = self._visualize_pose_result(frame, pose_result, person_bbox)
                
                # 计算并显示FPS
                if frame_count % 30 == 0:
                    fps = 30 / (time.time() - fps_start_time)
                    fps_start_time = time.time()
                    logger.info(f"FPS: {fps:.1f}")
                
                # 显示FPS和状态信息
                self._draw_info_overlay(vis_frame, pose_result, fps if 'fps' in locals() else 0)
                
                # 显示结果
                cv2.imshow('MediaPipe Pose Analysis Demo', vis_frame)
                
                # 处理按键
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    filename = f"pose_demo_{int(time.time())}.jpg"
                    cv2.imwrite(filename, vis_frame)
                    logger.info(f"Screenshot saved: {filename}")
        
        except KeyboardInterrupt:
            logger.info("Demo interrupted by user")
        
        finally:
            cap.release()
            cv2.destroyAllWindows()
            logger.info("Webcam demo finished")
    
    def run_image_demo(self, image_path: str):
        """运行单张图片演示"""
        logger.info(f"Running image demo with {image_path}")
        
        # 读取图片
        frame = cv2.imread(image_path)
        if frame is None:
            logger.error(f"Cannot read image: {image_path}")
            return
        
        # 创建人员边界框 (整个图片)
        person_bbox = BoundingBox(
            x=0, y=0,
            width=frame.shape[1],
            height=frame.shape[0],
            confidence=1.0
        )
        
        # 执行姿态分析
        start_time = time.time()
        pose_result = self.pose_analyzer.analyze_pose(frame, person_bbox)
        analysis_time = time.time() - start_time
        
        # 可视化结果
        vis_frame = self._visualize_pose_result(frame, pose_result, person_bbox)
        
        # 显示分析信息
        self._draw_info_overlay(vis_frame, pose_result, 1.0/analysis_time)
        
        # 显示结果
        cv2.imshow('MediaPipe Pose Analysis - Image Demo', vis_frame)
        
        # 保存结果
        output_path = image_path.replace('.', '_pose_result.')
        cv2.imwrite(output_path, vis_frame)
        logger.info(f"Result saved: {output_path}")
        
        logger.info(f"Analysis time: {analysis_time:.3f}s")
        logger.info("Press any key to close")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    
    def _visualize_pose_result(self, frame: np.ndarray, pose_result, person_bbox: BoundingBox) -> np.ndarray:
        """可视化姿态分析结果"""
        vis_frame = frame.copy()
        
        # 绘制人员边界框
        cv2.rectangle(vis_frame, 
                     (person_bbox.x, person_bbox.y),
                     (person_bbox.x + person_bbox.width, person_bbox.y + person_bbox.height),
                     self.colors['bbox'], 2)
        
        if not pose_result.keypoints:
            # 未检测到姿态
            cv2.putText(vis_frame, "No Pose Detected", (50, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            return vis_frame
        
        # 绘制姿态连接线
        self._draw_pose_connections(vis_frame, pose_result.keypoints)
        
        # 绘制关键点
        self._draw_keypoints(vis_frame, pose_result.keypoints)
        
        # 绘制跌倒状态
        self._draw_fall_status(vis_frame, pose_result)
        
        return vis_frame
    
    def _draw_pose_connections(self, frame: np.ndarray, keypoints: List[PoseKeypoint]):
        """绘制姿态连接线"""
        for connection in self.pose_connections:
            start_idx, end_idx = connection
            
            if (start_idx < len(keypoints) and end_idx < len(keypoints) and
                keypoints[start_idx].visible and keypoints[end_idx].visible):
                
                start_point = (int(keypoints[start_idx].x), int(keypoints[start_idx].y))
                end_point = (int(keypoints[end_idx].x), int(keypoints[end_idx].y))
                
                cv2.line(frame, start_point, end_point, self.colors['connection'], 2)
    
    def _draw_keypoints(self, frame: np.ndarray, keypoints: List[PoseKeypoint]):
        """绘制关键点"""
        for i, keypoint in enumerate(keypoints):
            if keypoint.visible and keypoint.confidence > 0.5:
                center = (int(keypoint.x), int(keypoint.y))
                
                # 根据置信度调整颜色强度
                confidence_factor = min(1.0, keypoint.confidence)
                color = tuple(int(c * confidence_factor) for c in self.colors['keypoint'])
                
                cv2.circle(frame, center, 4, color, -1)
                cv2.circle(frame, center, 6, (255, 255, 255), 1)
                
                # 显示关键点索引 (可选)
                if keypoint.confidence > 0.8:
                    cv2.putText(frame, str(i), (center[0] + 8, center[1] - 8),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.3, (255, 255, 255), 1)
    
    def _draw_fall_status(self, frame: np.ndarray, pose_result):
        """绘制跌倒状态"""
        if pose_result.is_fall_detected:
            # 跌倒警报
            status_text = f"FALL DETECTED! (Confidence: {pose_result.fall_confidence:.2f})"
            color = self.colors['fall_alert']
            
            # 闪烁效果
            if int(time.time() * 4) % 2:  # 4Hz闪烁
                cv2.rectangle(frame, (0, 0), (frame.shape[1], 80), color, -1)
                cv2.putText(frame, status_text, (20, 50),
                           cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)
        else:
            # 正常状态
            status_text = "Normal Pose"
            color = self.colors['normal']
            cv2.putText(frame, status_text, (20, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        
        # 显示置信度条
        self._draw_confidence_bar(frame, pose_result.fall_confidence)
    
    def _draw_confidence_bar(self, frame: np.ndarray, confidence: float):
        """绘制置信度条"""
        bar_width = 200
        bar_height = 20
        bar_x = frame.shape[1] - bar_width - 20
        bar_y = 20
        
        # 背景
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                     (50, 50, 50), -1)
        
        # 置信度条
        fill_width = int(bar_width * confidence)
        color = (0, 255, 0) if confidence < 0.5 else (0, 255, 255) if confidence < 0.8 else (0, 0, 255)
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + fill_width, bar_y + bar_height), 
                     color, -1)
        
        # 边框和文字
        cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), 
                     (255, 255, 255), 1)
        cv2.putText(frame, f"Fall: {confidence:.2f}", (bar_x, bar_y - 5),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    
    def _draw_info_overlay(self, frame: np.ndarray, pose_result, fps: float):
        """绘制信息覆盖层"""
        info_y = frame.shape[0] - 100
        
        # 背景
        cv2.rectangle(frame, (10, info_y - 10), (400, frame.shape[0] - 10), 
                     (0, 0, 0, 128), -1)
        
        # 信息文本
        info_lines = [
            f"FPS: {fps:.1f}",
            f"Keypoints: {len(pose_result.keypoints)}",
            f"Timestamp: {pose_result.timestamp:.2f}",
            f"Frame ID: {pose_result.frame_id}"
        ]
        
        for i, line in enumerate(info_lines):
            cv2.putText(frame, line, (20, info_y + i * 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='MediaPipe Pose Analyzer Demo')
    parser.add_argument('--mode', choices=['webcam', 'image'], default='webcam',
                       help='Demo mode: webcam or image')
    parser.add_argument('--input', type=str, help='Input image path (for image mode)')
    parser.add_argument('--camera', type=int, default=0, help='Camera ID (for webcam mode)')
    
    args = parser.parse_args()
    
    demo = PoseAnalyzerDemo()
    
    if args.mode == 'webcam':
        demo.run_webcam_demo(args.camera)
    elif args.mode == 'image':
        if not args.input:
            print("Error: --input is required for image mode")
            return
        demo.run_image_demo(args.input)


if __name__ == "__main__":
    main()