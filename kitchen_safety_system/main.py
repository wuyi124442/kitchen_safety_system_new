"""
厨房安全检测系统主入口

提供系统启动、停止和管理功能。
"""

import sys
import signal
import argparse
from typing import Optional
from pathlib import Path

from .core.interfaces import IDetectionSystem
from .core.config import config_manager, load_config_from_env
from .core.configuration_manager import configuration_manager
from .core.system_recovery import system_recovery_manager
from .detection.detection_system import DetectionSystem
from .utils.logger import get_logger

logger = get_logger(__name__)


class KitchenSafetySystem:
    """厨房安全检测系统主控制器"""
    
    def __init__(self):
        """初始化系统"""
        self.detection_system: Optional[IDetectionSystem] = None
        self.is_running = False
        
        # 注册信号处理器
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理器"""
        logger.info(f"接收到信号 {signum}，正在关闭系统...")
        self.stop()
        sys.exit(0)
    
    def initialize(self) -> bool:
        """
        初始化系统
        
        Returns:
            是否初始化成功
        """
        try:
            logger.info("正在初始化厨房安全检测系统...")
            
            # 加载环境变量配置
            load_config_from_env()
            
            # 初始化配置管理器
            configuration_manager.reload_config()
            
            # 创建检测系统实例
            self.detection_system = DetectionSystem()
            
            # 启动系统恢复监控
            system_recovery_manager.start_monitoring()
            
            logger.info("系统初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"系统初始化失败: {e}")
            return False
    
    def start(self) -> bool:
        """
        启动系统
        
        Returns:
            是否启动成功
        """
        if not self.initialize():
            return False
        
        try:
            logger.info("正在启动厨房安全检测系统...")
            
            if self.detection_system:
                if self.detection_system.start_detection():
                    self.is_running = True
                    logger.info("系统启动成功")
                    return True
                else:
                    logger.error("检测系统启动失败")
                    return False
            else:
                logger.warning("检测系统未初始化，运行在演示模式")
                self.is_running = True
                return True
                
        except Exception as e:
            logger.error(f"系统启动失败: {e}")
            return False
    
    def stop(self) -> None:
        """停止系统"""
        if not self.is_running:
            return
        
        try:
            logger.info("正在停止厨房安全检测系统...")
            
            if self.detection_system:
                self.detection_system.stop_detection()
            
            self.is_running = False
            logger.info("系统已停止")
            
        except Exception as e:
            logger.error(f"系统停止时发生错误: {e}")
    
    def get_status(self) -> dict:
        """
        获取系统状态
        
        Returns:
            系统状态信息
        """
        status = {
            'is_running': self.is_running,
            'config': config_manager.get_config().to_dict()
        }
        
        if self.detection_system:
            # 使用增强的系统状态
            if hasattr(self.detection_system, 'get_enhanced_system_status'):
                enhanced_status = self.detection_system.get_enhanced_system_status()
                status.update(enhanced_status)
            else:
                status.update(self.detection_system.get_system_status())
        
        return status
    
    def run_demo(self) -> None:
        """运行演示模式"""
        logger.info("启动演示模式...")
        
        try:
            from .demo.demo_app import DemoApplication
            
            print("厨房安全检测系统 - 演示模式")
            print("=" * 50)
            print("系统功能:")
            print("1. 实时视频采集和处理")
            print("2. YOLO目标检测 (人员、灶台、火焰)")
            print("3. MediaPipe姿态识别和跌倒检测")
            print("4. 风险评估和报警管理")
            print("5. Django Web后台管理")
            print("6. 日志记录和查询系统")
            print("7. 演示模式和可视化功能")
            print("=" * 50)
            print("启动演示应用...")
            
            # 创建并启动演示应用
            demo_app = DemoApplication()
            
            # 初始化检测系统（如果可用）
            if self.detection_system:
                demo_app.detection_system = self.detection_system
            else:
                demo_app.initialize_detection_system()
            
            # 启动演示
            if demo_app.start_demo("comprehensive"):
                logger.info("演示模式启动成功")
            else:
                logger.error("演示模式启动失败")
                print("演示模式启动失败，请检查演示视频文件是否存在")
                
        except ImportError as e:
            logger.error(f"演示模块导入失败: {e}")
            print("演示功能不可用，请检查演示模块是否正确安装")
            
            # 回退到简单演示模式
            print("使用简单演示模式...")
            self._run_simple_demo()
            
        except Exception as e:
            logger.error(f"演示模式启动失败: {e}")
            print(f"演示模式启动失败: {e}")
    
    def _run_simple_demo(self) -> None:
        """运行简单演示模式（回退方案）"""
        print("简单演示模式已启动，按 Ctrl+C 退出")
        print("\n控制说明:")
        print("- 按 Enter 模拟检测事件")
        print("- 输入 'status' 查看系统状态")
        print("- 输入 'quit' 退出演示")
        
        try:
            while True:
                user_input = input("\n> ").strip().lower()
                
                if user_input == 'quit' or user_input == 'q':
                    break
                elif user_input == 'status':
                    status = self.get_status()
                    print("系统状态:")
                    for key, value in status.items():
                        print(f"  {key}: {value}")
                elif user_input == '' or user_input == 'demo':
                    print("模拟检测事件...")
                    print("- 检测到人员")
                    print("- 检测到灶台")
                    print("- 检测到火焰")
                    print("- 风险评估: 正常")
                else:
                    print("未知命令，输入 'quit' 退出")
                    
        except KeyboardInterrupt:
            print("\n简单演示模式已退出")


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="厨房安全检测系统",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s start                    # 启动系统
  %(prog)s stop                     # 停止系统
  %(prog)s status                   # 查看状态
  %(prog)s demo                     # 运行演示模式
  %(prog)s --config config.json    # 使用指定配置文件
        """
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'status', 'demo'],
        help='要执行的命令'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='配置文件路径'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别'
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='以守护进程模式运行'
    )
    
    return parser


def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()
    
    # 设置日志级别
    import logging
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # 加载指定的配置文件
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            config_manager.import_config(str(config_path))
        else:
            logger.error(f"配置文件不存在: {config_path}")
            sys.exit(1)
    
    # 创建系统实例
    system = KitchenSafetySystem()
    
    # 执行命令
    if args.command == 'start':
        if system.start():
            if args.daemon:
                # 守护进程模式
                import daemon
                with daemon.DaemonContext():
                    try:
                        while system.is_running:
                            import time
                            time.sleep(1)
                    except KeyboardInterrupt:
                        system.stop()
            else:
                # 前台模式
                try:
                    while system.is_running:
                        import time
                        time.sleep(1)
                except KeyboardInterrupt:
                    system.stop()
        else:
            sys.exit(1)
    
    elif args.command == 'stop':
        system.stop()
    
    elif args.command == 'status':
        status = system.get_status()
        print("系统状态:")
        for key, value in status.items():
            print(f"  {key}: {value}")
    
    elif args.command == 'demo':
        system.run_demo()


if __name__ == '__main__':
    main()