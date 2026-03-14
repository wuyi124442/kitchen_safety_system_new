"""
日志管理模块

提供统一的日志记录功能，支持loguru和标准logging。
"""

import os
import sys
import logging
from typing import Optional
from pathlib import Path

# 尝试导入loguru，如果不可用则使用标准logging
try:
    from loguru import logger as loguru_logger
    LOGURU_AVAILABLE = True
except ImportError:
    LOGURU_AVAILABLE = False


class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        """初始化日志管理器"""
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        if LOGURU_AVAILABLE:
            self._setup_loguru()
        else:
            self._setup_standard_logging()
    
    def _setup_loguru(self):
        """配置loguru日志"""
        # 移除默认处理器
        loguru_logger.remove()
        
        # 控制台输出
        loguru_logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
                   "<level>{message}</level>",
            level="INFO"
        )
        
        # 文件输出
        loguru_logger.add(
            self.log_dir / "kitchen_safety_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            encoding="utf-8"
        )
        
        # 错误日志单独文件
        loguru_logger.add(
            self.log_dir / "errors_{time:YYYY-MM-DD}.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            encoding="utf-8"
        )
    
    def _setup_standard_logging(self):
        """配置标准logging"""
        # 创建根日志记录器
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # 清除现有处理器
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # 文件处理器
        file_handler = logging.FileHandler(
            self.log_dir / "kitchen_safety.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # 错误文件处理器
        error_handler = logging.FileHandler(
            self.log_dir / "errors.log",
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        获取指定名称的日志记录器
        
        Args:
            name: 日志记录器名称
            
        Returns:
            日志记录器实例
        """
        if LOGURU_AVAILABLE:
            # loguru使用全局logger，通过bind添加上下文
            return LoguruAdapter(name)
        else:
            return logging.getLogger(name)


class LoguruAdapter:
    """Loguru适配器，提供与标准logging兼容的接口"""
    
    def __init__(self, name: str):
        self.name = name
        self.logger = loguru_logger.bind(name=name)
    
    def debug(self, message: str, *args, **kwargs):
        """调试日志"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """信息日志"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """警告日志"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """错误日志"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """严重错误日志"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """异常日志"""
        self.logger.exception(message, *args, **kwargs)


# 全局日志管理器实例
logger_manager = LoggerManager()


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    获取日志记录器的便捷函数
    
    Args:
        name: 日志记录器名称，默认使用调用模块名
        
    Returns:
        日志记录器实例
    """
    if name is None:
        # 获取调用者的模块名
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return logger_manager.get_logger(name)


# 设置环境变量日志级别
def set_log_level_from_env():
    """从环境变量设置日志级别"""
    log_level = os.getenv('KITCHEN_SAFETY_LOG_LEVEL', 'INFO').upper()
    
    if LOGURU_AVAILABLE:
        loguru_logger.remove()
        loguru_logger.add(sys.stderr, level=log_level)
    else:
        logging.getLogger().setLevel(getattr(logging, log_level, logging.INFO))


# 初始化时设置日志级别
set_log_level_from_env()