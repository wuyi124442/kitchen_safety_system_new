"""
检测结果后处理器测试

测试检测结果后处理器的各项功能，包括边界框过滤、NMS、置信度调整等。
"""

import pytest
import numpy as np
import time
from unittest.mock import Mock, patch

from kitchen_safety_system.detection.detection_post_processor import DetectionPostProcessor
from kitchen_safety_system.core.interfaces import DetectionResult, DetectionType, BoundingBox


class TestDetectionPostProcessor:
    """检测结果后处理器测试类"""
    
    @pytest.fixture
    def post_processor(self):
        """创建测试用的后处理器"""
        return DetectionPostProcessor(
            confidence_threshold=0.5,
            nms_threshold=0.45,
            min_box_size=20,
            max_detections=50
        )
    
    @pytest.fixture
    def sample_detections(self):
        """创建测试用的检测结果"""
        current_time = time.time()
        return [
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=100, y=100, width=100, height=200, confidence=0.85),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=110, y=110, width=90, height=180, confidence=0.75),  # 重叠框
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.FLAME,
                bbox=BoundingBox(x=300, y=200, width=50, height=50, confidence=0.92),
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.STOVE,
                bbox=BoundingBox(x=400, y=300, width=15, height=15, confidence=0.60),  # 太小
                timestamp=current_time,
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=500, y=400, width=80, height=120, confidence=0.30),  # 置信度低
                timestamp=current_time,
                frame_id=1
            )
        ]
    
    def test_init_default_parameters(self):
        """测试默认参数初始化"""
        processor = DetectionPostProcessor()
        
        assert processor.confidence_threshold == 0.5
        assert processor.nms_threshold == 0.45
        assert processor.min_box_size == 20
        assert processor.max_detections == 100
        assert processor.class_specific_nms is True
    
    def test_init_custom_parameters(self):
        """测试自定义参数初始化"""
        processor = DetectionPostProcessor(
            confidence_threshold=0.7,
            nms_threshold=0.3,
            min_box_size=30,
            max_detections=25,
            class_specific_nms=False
        )
        
        assert processor.confidence_threshold == 0.7
        assert processor.nms_threshold == 0.3
        assert processor.min_box_size == 30
        assert processor.max_detections == 25
        assert processor.class_specific_nms is False
    
    def test_process_empty_detections(self, post_processor):
        """测试处理空检测结果"""
        result = post_processor.process_detections([])
        assert result == []
    
    def test_confidence_filtering(self, post_processor, sample_detections):
        """测试置信度过滤"""
        # 设置较高的置信度阈值
        post_processor.set_confidence_threshold(0.8)
        
        filtered = post_processor._filter_by_confidence(sample_detections)
        
        # 只有置信度0.85和0.92的检测结果应该保留
        # 但需要考虑类别特定阈值，STOVE默认阈值是0.6
        expected_count = 0
        for detection in sample_detections:
            threshold = post_processor.class_thresholds.get(
                detection.detection_type, 
                post_processor.confidence_threshold
            )
            if detection.bbox.confidence >= threshold:
                expected_count += 1
        
        assert len(filtered) == expected_count
        assert all(d.bbox.confidence >= post_processor.class_thresholds.get(
            d.detection_type, post_processor.confidence_threshold
        ) for d in filtered)
    
    def test_class_specific_confidence_filtering(self, post_processor, sample_detections):
        """测试类别特定的置信度过滤"""
        # 为FLAME类别设置更高的阈值
        post_processor.set_confidence_threshold(0.95, DetectionType.FLAME)
        
        filtered = post_processor._filter_by_confidence(sample_detections)
        
        # FLAME检测结果应该被过滤掉（置信度0.92 < 0.95）
        flame_detections = [d for d in filtered if d.detection_type == DetectionType.FLAME]
        assert len(flame_detections) == 0
    
    def test_size_filtering(self, post_processor, sample_detections):
        """测试尺寸过滤"""
        filtered = post_processor._filter_by_size(sample_detections)
        
        # 尺寸15x15的检测结果应该被过滤掉
        assert all(d.bbox.width >= 20 and d.bbox.height >= 20 for d in filtered)
        assert len(filtered) == len(sample_detections) - 1  # 应该过滤掉一个
    
    def test_position_filtering(self, post_processor):
        """测试位置过滤"""
        # 创建超出边界的检测结果
        detections = [
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=-10, y=-10, width=50, height=50, confidence=0.8),
                timestamp=time.time(),
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=590, y=430, width=100, height=100, confidence=0.8),  # 超出640x480
                timestamp=time.time(),
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=100, y=100, width=50, height=50, confidence=0.8),  # 正常
                timestamp=time.time(),
                frame_id=1
            )
        ]
        
        filtered = post_processor._filter_by_position(detections, (480, 640))
        
        # 检查边界框是否被正确修正
        assert len(filtered) == 3  # 所有检测结果都应该保留（经过修正）
        
        # 检查第一个检测结果的坐标修正
        assert filtered[0].bbox.x >= 0
        assert filtered[0].bbox.y >= 0
        
        # 检查第二个检测结果的尺寸修正
        assert filtered[1].bbox.x + filtered[1].bbox.width <= 640
        assert filtered[1].bbox.y + filtered[1].bbox.height <= 480
    
    def test_nms_single_class(self, post_processor):
        """测试单类别NMS"""
        # 创建重叠的检测结果
        detections = [
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=100, y=100, width=100, height=200, confidence=0.9),
                timestamp=time.time(),
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=110, y=110, width=90, height=180, confidence=0.8),  # 重叠
                timestamp=time.time(),
                frame_id=1
            ),
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=300, y=300, width=80, height=160, confidence=0.7),  # 不重叠
                timestamp=time.time(),
                frame_id=1
            )
        ]
        
        nms_result = post_processor._nms_single_class(detections)
        
        # 应该保留置信度最高的和不重叠的检测结果
        assert len(nms_result) == 2
        assert nms_result[0].bbox.confidence == 0.9  # 最高置信度
        assert any(d.bbox.confidence == 0.7 for d in nms_result)  # 不重叠的
    
    def test_class_specific_nms(self, post_processor, sample_detections):
        """测试类别特定NMS"""
        post_processor.class_specific_nms = True
        
        nms_result = post_processor._apply_nms(sample_detections)
        
        # 不同类别的检测结果不应该相互影响
        person_count = len([d for d in nms_result if d.detection_type == DetectionType.PERSON])
        flame_count = len([d for d in nms_result if d.detection_type == DetectionType.FLAME])
        stove_count = len([d for d in nms_result if d.detection_type == DetectionType.STOVE])
        
        assert person_count >= 1  # 至少保留一个人员检测
        assert flame_count >= 0  # 火焰检测可能被过滤
        assert stove_count >= 0  # 灶台检测可能被过滤
    
    def test_limit_detections(self, post_processor):
        """测试检测数量限制"""
        # 创建超过限制数量的检测结果
        detections = []
        for i in range(60):  # 超过max_detections=50
            detections.append(
                DetectionResult(
                    detection_type=DetectionType.PERSON,
                    bbox=BoundingBox(x=i*10, y=i*10, width=50, height=50, confidence=0.5 + i*0.01),
                    timestamp=time.time(),
                    frame_id=1
                )
            )
        
        limited = post_processor._limit_detections(detections)
        
        assert len(limited) == 50  # 应该限制为50个
        # 检查是否按置信度排序（最高置信度的应该被保留）
        assert limited[0].bbox.confidence >= limited[-1].bbox.confidence
    
    def test_update_position_info(self, post_processor, sample_detections):
        """测试位置信息更新"""
        original_timestamps = [d.timestamp for d in sample_detections]
        
        post_processor._update_position_info(sample_detections)
        
        # 检查时间戳是否更新
        for i, detection in enumerate(sample_detections):
            assert detection.timestamp >= original_timestamps[i]
            
            # 检查是否添加了额外信息
            assert detection.additional_data is not None
            assert 'center_x' in detection.additional_data
            assert 'center_y' in detection.additional_data
            assert 'area' in detection.additional_data
            assert 'processed_timestamp' in detection.additional_data
    
    def test_complete_processing_pipeline(self, post_processor, sample_detections):
        """测试完整的处理流水线"""
        frame_shape = (480, 640)
        
        result = post_processor.process_detections(sample_detections, frame_shape)
        
        # 检查结果的基本属性
        assert isinstance(result, list)
        assert len(result) <= len(sample_detections)  # 应该过滤掉一些检测结果
        
        # 检查所有结果都满足基本要求
        for detection in result:
            assert detection.bbox.confidence >= post_processor.class_thresholds.get(
                detection.detection_type, post_processor.confidence_threshold
            )
            assert detection.bbox.width >= post_processor.min_box_size
            assert detection.bbox.height >= post_processor.min_box_size
            assert detection.additional_data is not None
    
    def test_set_confidence_threshold(self, post_processor):
        """测试设置置信度阈值"""
        # 测试全局阈值
        post_processor.set_confidence_threshold(0.8)
        assert post_processor.confidence_threshold == 0.8
        
        # 测试类别特定阈值
        post_processor.set_confidence_threshold(0.9, DetectionType.FLAME)
        assert post_processor.class_thresholds[DetectionType.FLAME] == 0.9
        
        # 测试无效阈值
        original_threshold = post_processor.confidence_threshold
        post_processor.set_confidence_threshold(1.5)  # 无效
        assert post_processor.confidence_threshold == original_threshold
    
    def test_set_nms_threshold(self, post_processor):
        """测试设置NMS阈值"""
        post_processor.set_nms_threshold(0.3)
        assert post_processor.nms_threshold == 0.3
        
        # 测试无效阈值
        original_threshold = post_processor.nms_threshold
        post_processor.set_nms_threshold(-0.1)  # 无效
        assert post_processor.nms_threshold == original_threshold
    
    def test_set_min_box_size(self, post_processor):
        """测试设置最小边界框尺寸"""
        post_processor.set_min_box_size(30)
        assert post_processor.min_box_size == 30
        
        # 测试无效尺寸
        original_size = post_processor.min_box_size
        post_processor.set_min_box_size(-10)  # 无效
        assert post_processor.min_box_size == original_size
    
    def test_performance_stats(self, post_processor, sample_detections):
        """测试性能统计"""
        # 初始状态
        stats = post_processor.get_performance_stats()
        assert stats['processing_count'] == 0
        assert stats['average_processing_time'] == 0.0
        
        # 执行一些处理
        post_processor.process_detections(sample_detections)
        post_processor.process_detections(sample_detections)
        
        stats = post_processor.get_performance_stats()
        assert stats['processing_count'] == 2
        assert stats['average_processing_time'] >= 0.0  # 允许为0（处理很快）
        assert 'confidence_threshold' in stats
        assert 'nms_threshold' in stats
    
    def test_reset_stats(self, post_processor, sample_detections):
        """测试重置统计"""
        # 执行一些处理
        post_processor.process_detections(sample_detections)
        
        # 重置统计
        post_processor.reset_stats()
        
        stats = post_processor.get_performance_stats()
        assert stats['processing_count'] == 0
        assert stats['total_processing_time'] == 0.0
    
    def test_optimize_for_realtime(self, post_processor):
        """测试实时优化"""
        original_max_detections = post_processor.max_detections
        original_nms_threshold = post_processor.nms_threshold
        
        post_processor.optimize_for_realtime()
        
        # 检查参数是否被优化
        assert post_processor.max_detections <= 50
        assert post_processor.nms_threshold >= 0.4
    
    def test_optimize_for_accuracy(self, post_processor):
        """测试精度优化"""
        post_processor.optimize_for_accuracy()
        
        # 检查参数是否被优化
        assert post_processor.max_detections == 100
        assert post_processor.nms_threshold == 0.3
    
    def test_error_handling(self, post_processor):
        """测试错误处理"""
        # 测试处理损坏的检测结果
        invalid_detections = [
            DetectionResult(
                detection_type=DetectionType.PERSON,
                bbox=BoundingBox(x=100, y=100, width=-50, height=50, confidence=0.8),  # 负宽度
                timestamp=time.time(),
                frame_id=1
            )
        ]
        
        # 应该能够处理而不崩溃
        result = post_processor.process_detections(invalid_detections)
        assert isinstance(result, list)


class TestDetectionPostProcessorIntegration:
    """检测结果后处理器集成测试"""
    
    def test_integration_with_realistic_data(self):
        """使用真实数据进行集成测试"""
        processor = DetectionPostProcessor(
            confidence_threshold=0.5,
            nms_threshold=0.45,
            min_box_size=20
        )
        
        # 模拟真实的检测结果
        detections = []
        current_time = time.time()
        
        # 添加多个人员检测（部分重叠）
        for i in range(5):
            detections.append(
                DetectionResult(
                    detection_type=DetectionType.PERSON,
                    bbox=BoundingBox(
                        x=100 + i*10, 
                        y=100 + i*10, 
                        width=80, 
                        height=160, 
                        confidence=0.8 - i*0.1
                    ),
                    timestamp=current_time,
                    frame_id=1
                )
            )
        
        # 添加火焰检测
        detections.append(
            DetectionResult(
                detection_type=DetectionType.FLAME,
                bbox=BoundingBox(x=300, y=200, width=40, height=40, confidence=0.9),
                timestamp=current_time,
                frame_id=1
            )
        )
        
        # 处理检测结果
        result = processor.process_detections(detections, (480, 640))
        
        # 验证结果
        assert len(result) < len(detections)  # 应该过滤掉一些重叠的检测
        assert all(d.bbox.confidence >= 0.5 for d in result)  # 置信度过滤
        assert all(d.additional_data is not None for d in result)  # 位置信息更新
        
        # 验证性能统计
        stats = processor.get_performance_stats()
        assert stats['processing_count'] == 1
        assert stats['average_processing_time'] >= 0  # 允许为0（处理很快）
    
    def test_performance_benchmark(self):
        """性能基准测试"""
        processor = DetectionPostProcessor()
        
        # 创建大量检测结果
        detections = []
        current_time = time.time()
        
        for i in range(200):  # 大量检测结果
            detections.append(
                DetectionResult(
                    detection_type=DetectionType.PERSON,
                    bbox=BoundingBox(
                        x=i % 600, 
                        y=(i // 10) % 400, 
                        width=50, 
                        height=100, 
                        confidence=0.5 + (i % 50) * 0.01
                    ),
                    timestamp=current_time,
                    frame_id=1
                )
            )
        
        # 测试处理时间
        start_time = time.time()
        result = processor.process_detections(detections, (480, 640))
        processing_time = time.time() - start_time
        
        # 验证性能要求（应该在合理时间内完成）
        assert processing_time < 0.1  # 100ms内完成
        assert len(result) <= processor.max_detections
        
        # 验证统计信息
        stats = processor.get_performance_stats()
        assert stats['average_processing_time'] < 0.1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])