#!/usr/bin/env python3
"""
性能优化和稳定性增强演示

演示厨房安全检测系统的异常处理、自动恢复和性能监控功能。
验证需求 8.2, 8.3, 8.4, 8.5 的实现。
"""

import time
import threading
import random
from typing import Dict, Any

from kitchen_safety_system.core.exception_handler import (
    exception_handler, ExceptionSeverity, RecoveryStrategy
)
from kitchen_safety_system.core.performance_monitor import (
    performance_monitor, PerformanceLevel
)
from kitchen_safety_system.utils.logger import get_logger

logger = get_logger(__name__)


class PerformanceStabilityDemo:
    """性能优化和稳定性增强演示类"""
    
    def __init__(self):
        """初始化演示"""
        self.is_running = False
        self.demo_thread = None
        self.stats = {
            'simulated_exceptions': 0,
            'recovered_exceptions': 0,
            'performance_optimizations': 0,
            'uptime_seconds': 0
        }
        
        # 设置异常处理和性能监控
        self._setup_exception_handling()
        self._setup_performance_monitoring()
    
    def _setup_exception_handling(self):
        """设置异常处理演示"""
        print("🔧 设置异常处理系统...")
        
        # 注册演示模块
        exception_handler.register_module('demo_module', self._demo_recovery_handler)
        
        # 设置恢复策略
        exception_handler.set_recovery_strategy('ConnectionError', RecoveryStrategy.RESTART_MODULE)
        exception_handler.set_recovery_strategy('TimeoutError', RecoveryStrategy.RETRY)
        exception_handler.set_recovery_strategy('MemoryError', RecoveryStrategy.RESTART_SYSTEM)
        exception_handler.set_recovery_strategy('RuntimeError', RecoveryStrategy.RESTART_MODULE)
        
        print("✅ 异常处理系统设置完成")
    
    def _setup_performance_monitoring(self):
        """设置性能监控演示"""
        print("📊 设置性能监控系统...")
        
        # 设置性能阈值
        performance_monitor.set_threshold('cpu_warning', 70.0)
        performance_monitor.set_threshold('cpu_critical', 80.0)
        performance_monitor.set_threshold('memory_warning', 60.0)
        performance_monitor.set_threshold('memory_critical', 70.0)
        performance_monitor.set_threshold('fps_warning', 10.0)
        performance_monitor.set_threshold('fps_critical', 5.0)
        
        # 注册优化回调
        performance_monitor.register_optimization_callback('cpu_critical', self._cpu_optimization_callback)
        performance_monitor.register_optimization_callback('memory_critical', self._memory_optimization_callback)
        performance_monitor.register_optimization_callback('fps_critical', self._fps_optimization_callback)
        
        print("✅ 性能监控系统设置完成")
    
    def _demo_recovery_handler(self) -> bool:
        """演示恢复处理器"""
        print("🔄 执行系统恢复...")
        time.sleep(0.5)  # 模拟恢复时间
        self.stats['recovered_exceptions'] += 1
        print("✅ 系统恢复成功")
        return True
    
    def _cpu_optimization_callback(self, alert):
        """CPU优化回调"""
        print(f"⚡ 触发CPU优化: {alert.message}")
        self.stats['performance_optimizations'] += 1
        # 模拟优化操作
        time.sleep(0.2)
        print("✅ CPU使用率优化完成")
    
    def _memory_optimization_callback(self, alert):
        """内存优化回调"""
        print(f"🧹 触发内存优化: {alert.message}")
        self.stats['performance_optimizations'] += 1
        # 模拟内存清理
        import gc
        gc.collect()
        print("✅ 内存使用率优化完成")
    
    def _fps_optimization_callback(self, alert):
        """FPS优化回调"""
        print(f"🚀 触发处理速度优化: {alert.message}")
        self.stats['performance_optimizations'] += 1
        # 模拟处理优化
        time.sleep(0.1)
        print("✅ 处理速度优化完成")
    
    def start_demo(self, duration: int = 30):
        """
        启动演示
        
        Args:
            duration: 演示持续时间（秒）
        """
        print("🎬 启动性能优化和稳定性增强演示")
        print("=" * 60)
        
        # 启动性能监控
        performance_monitor.start_monitoring()
        
        self.is_running = True
        start_time = time.time()
        
        try:
            # 启动演示线程
            self.demo_thread = threading.Thread(target=self._demo_loop, daemon=True)
            self.demo_thread.start()
            
            # 主演示循环
            while self.is_running and (time.time() - start_time) < duration:
                self._update_demo_status()
                time.sleep(2)
            
        except KeyboardInterrupt:
            print("\n⏹️  演示被用户中断")
        
        finally:
            self.is_running = False
            performance_monitor.stop_monitoring()
            
            # 等待演示线程结束
            if self.demo_thread and self.demo_thread.is_alive():
                self.demo_thread.join(timeout=2)
            
            self.stats['uptime_seconds'] = time.time() - start_time
            self._show_final_results()
    
    def _demo_loop(self):
        """演示循环"""
        while self.is_running:
            try:
                # 模拟正常处理
                self._simulate_processing()
                
                # 随机触发异常
                if random.random() < 0.1:  # 10%概率
                    self._simulate_exception()
                
                # 模拟性能变化
                self._simulate_performance_changes()
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"演示循环异常: {e}")
                break
    
    def _simulate_processing(self):
        """模拟正常处理"""
        # 模拟检测处理时间
        detection_time = random.uniform(20, 80)  # 20-80ms
        pose_time = random.uniform(10, 40)       # 10-40ms
        risk_time = random.uniform(5, 20)        # 5-20ms
        
        # 模拟FPS
        fps = random.uniform(12, 25)
        
        # 更新性能指标
        performance_monitor.update_processing_metrics(
            fps=fps,
            frame_processing_time=detection_time + pose_time + risk_time,
            detection_time=detection_time,
            pose_analysis_time=pose_time,
            queue_sizes={'frame_queue': random.randint(0, 10), 'result_queue': random.randint(0, 20)}
        )
    
    def _simulate_exception(self):
        """模拟异常情况"""
        exception_types = [
            (ConnectionError, "模拟网络连接异常"),
            (TimeoutError, "模拟处理超时异常"),
            (RuntimeError, "模拟运行时异常"),
            (ValueError, "模拟数据异常")
        ]
        
        exception_class, message = random.choice(exception_types)
        exception = exception_class(message)
        
        print(f"⚠️  模拟异常: {exception_class.__name__} - {message}")
        self.stats['simulated_exceptions'] += 1
        
        # 使用异常处理器处理
        exception_handler.handle_exception(exception, 'demo_module')
    
    def _simulate_performance_changes(self):
        """模拟性能变化"""
        # 随机模拟高负载情况
        if random.random() < 0.05:  # 5%概率
            # 模拟低FPS
            performance_monitor.update_processing_metrics(
                fps=random.uniform(3, 8),  # 低FPS
                frame_processing_time=random.uniform(150, 250),  # 高处理时间
                detection_time=random.uniform(80, 120),
                pose_analysis_time=random.uniform(50, 80)
            )
    
    def _update_demo_status(self):
        """更新演示状态"""
        # 获取当前性能指标
        current_metrics = performance_monitor.get_current_metrics()
        if current_metrics:
            print(f"📈 当前性能: CPU {current_metrics.cpu_percent:.1f}%, "
                  f"内存 {current_metrics.memory_percent:.1f}%, "
                  f"FPS {current_metrics.fps:.1f}")
        
        # 显示活跃警报
        active_alerts = performance_monitor.get_active_alerts()
        if active_alerts:
            print(f"🚨 活跃警报: {len(active_alerts)} 个")
            for alert in active_alerts[-3:]:  # 显示最近3个
                print(f"   - {alert['alert_type']}: {alert['message']}")
        
        # 显示异常统计
        exception_stats = exception_handler.get_exception_statistics()
        print(f"🛡️  异常处理: 总计 {exception_stats['total_exceptions']}, "
              f"已解决 {exception_stats['resolved_exceptions']}, "
              f"解决率 {exception_stats['resolution_rate']:.1%}")
        
        print("-" * 60)
    
    def _show_final_results(self):
        """显示最终结果"""
        print("\n🎯 演示结果总结")
        print("=" * 60)
        
        # 基本统计
        print(f"⏱️  运行时间: {self.stats['uptime_seconds']:.1f} 秒")
        print(f"⚠️  模拟异常: {self.stats['simulated_exceptions']} 次")
        print(f"🔄 成功恢复: {self.stats['recovered_exceptions']} 次")
        print(f"⚡ 性能优化: {self.stats['performance_optimizations']} 次")
        
        # 异常处理统计
        exception_stats = exception_handler.get_exception_statistics()
        print(f"\n📊 异常处理统计:")
        print(f"   总异常数: {exception_stats['total_exceptions']}")
        print(f"   已解决数: {exception_stats['resolved_exceptions']}")
        print(f"   解决率: {exception_stats['resolution_rate']:.1%}")
        print(f"   恢复成功率: {exception_stats['recovery_success_rate']:.1%}")
        
        # 性能监控统计
        perf_stats = performance_monitor.get_performance_statistics()
        print(f"\n📈 性能监控统计:")
        print(f"   监控时长: {perf_stats['monitoring_uptime_seconds']:.1f} 秒")
        print(f"   总警报数: {perf_stats['total_alerts']}")
        print(f"   已解决警报: {perf_stats['resolved_alerts']}")
        print(f"   数据点数: {perf_stats['metrics_collected']}")
        
        # 性能摘要
        perf_summary = performance_monitor.get_performance_summary(minutes=60)
        if perf_summary:
            current = perf_summary.get('current', {})
            averages = perf_summary.get('averages', {})
            print(f"\n🎯 性能摘要:")
            print(f"   当前CPU: {current.get('cpu_percent', 0):.1f}%")
            print(f"   当前内存: {current.get('memory_percent', 0):.1f}%")
            print(f"   当前FPS: {current.get('fps', 0):.1f}")
            print(f"   平均CPU: {averages.get('cpu_percent', 0):.1f}%")
            print(f"   平均内存: {averages.get('memory_percent', 0):.1f}%")
            print(f"   平均FPS: {averages.get('fps', 0):.1f}")
        
        # 模块健康状态
        module_health = exception_handler.get_module_health('demo_module')
        if module_health:
            print(f"\n🏥 模块健康状态:")
            print(f"   健康状态: {'✅ 健康' if module_health['is_healthy'] else '❌ 异常'}")
            print(f"   错误次数: {module_health['error_count']}")
            print(f"   恢复尝试: {module_health['recovery_attempts']}")
            print(f"   运行时长: {module_health['uptime_seconds']:.1f} 秒")
        
        print("\n✅ 演示完成！系统展示了以下能力:")
        print("   🛡️  自动异常检测和恢复")
        print("   📊 实时性能监控和警报")
        print("   ⚡ 自动性能优化")
        print("   📈 详细的统计和分析")
        print("   🔄 24/7 稳定运行支持")


def main():
    """主函数"""
    print("🏠 厨房安全检测系统 - 性能优化和稳定性增强演示")
    print("📋 本演示将展示以下功能:")
    print("   • 异常处理和自动恢复机制 (需求 8.2, 8.3)")
    print("   • 性能监控和优化 (需求 8.4, 8.5)")
    print("   • 24小时稳定运行能力")
    print("   • 实时资源使用率监控")
    print("   • 自动性能调优")
    print()
    
    # 创建演示实例
    demo = PerformanceStabilityDemo()
    
    try:
        # 询问演示时长
        duration_input = input("请输入演示时长（秒，默认30秒，按Enter确认）: ").strip()
        duration = int(duration_input) if duration_input else 30
        
        print(f"\n🚀 开始 {duration} 秒演示...")
        print("💡 提示: 按 Ctrl+C 可随时停止演示")
        print()
        
        # 启动演示
        demo.start_demo(duration)
        
    except KeyboardInterrupt:
        print("\n👋 演示被用户中断")
    except ValueError:
        print("❌ 输入的时长无效，使用默认30秒")
        demo.start_demo(30)
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
    
    print("\n👋 感谢使用厨房安全检测系统演示！")


if __name__ == '__main__':
    main()