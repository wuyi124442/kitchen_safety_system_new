"""
配置管理器

提供统一的配置文件管理和运行时配置热更新功能。
"""

import json
import yaml
import os
import threading
import time
from typing import Dict, Any, Optional, Callable, List
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import copy

from .interfaces import IConfigurationManager
from .models import SystemConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)


class ConfigChangeHandler(FileSystemEventHandler):
    """配置文件变化处理器"""
    
    def __init__(self, config_manager: 'ConfigurationManager'):
        self.config_manager = config_manager
        self.logger = get_logger(__name__)
    
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return
        
        # 检查是否是配置文件
        if event.src_path in self.config_manager.watched_files:
            self.logger.info(f"检测到配置文件变化: {event.src_path}")
            # 延迟一点时间确保文件写入完成
            threading.Timer(0.5, self.config_manager._reload_config_file, 
                          args=[event.src_path]).start()


class ConfigurationManager(IConfigurationManager):
    """配置管理器实现"""
    
    def __init__(self, config_dir: str = "config", enable_hot_reload: bool = True):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
            enable_hot_reload: 是否启用热重载
        """
        self.config_dir = Path(config_dir)
        self.enable_hot_reload = enable_hot_reload
        self.logger = get_logger(__name__)
        
        # 配置存储
        self._config_data: Dict[str, Any] = {}
        self._config_lock = threading.RLock()
        
        # 配置变更回调
        self._change_callbacks: List[Callable[[str, Any, Any], None]] = []
        
        # 文件监控
        self.watched_files: Dict[str, str] = {}  # 文件路径 -> 配置键
        self.observer: Optional[Observer] = None
        
        # 默认配置文件
        self.default_config_files = {
            'system': 'system_config.json',
            'yolo': 'yolo_config.yaml',
            'default': 'default_config.yaml'
        }
        
        # 初始化
        self._initialize()
    
    def _initialize(self) -> None:
        """初始化配置管理器"""
        try:
            # 确保配置目录存在
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # 加载所有配置文件
            self._load_all_configs()
            
            # 启动文件监控
            if self.enable_hot_reload:
                self._start_file_watcher()
            
            self.logger.info("配置管理器初始化完成")
            
        except Exception as e:
            self.logger.error(f"配置管理器初始化失败: {e}")
            raise
    
    def get_config(self, key: str = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键，如 'detection.confidence_threshold'
                如果为None，返回所有配置
        
        Returns:
            配置值
        """
        with self._config_lock:
            if key is None:
                return copy.deepcopy(self._config_data)
            
            # 支持嵌套键访问
            keys = key.split('.')
            value = self._config_data
            
            try:
                for k in keys:
                    value = value[k]
                return copy.deepcopy(value)
            except (KeyError, TypeError):
                self.logger.warning(f"配置键不存在: {key}")
                return None
    
    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键，支持点分隔的嵌套键
            value: 配置值
        
        Returns:
            是否设置成功
        """
        try:
            with self._config_lock:
                # 获取旧值用于回调
                old_value = self.get_config(key)
                
                # 设置新值
                keys = key.split('.')
                config_dict = self._config_data
                
                # 导航到父级字典
                for k in keys[:-1]:
                    if k not in config_dict:
                        config_dict[k] = {}
                    config_dict = config_dict[k]
                
                # 设置值
                config_dict[keys[-1]] = value
                
                # 触发变更回调
                self._notify_config_change(key, old_value, value)
                
                self.logger.info(f"配置已更新: {key} = {value}")
                return True
                
        except Exception as e:
            self.logger.error(f"设置配置失败: {key} = {value}, 错误: {e}")
            return False
    
    def reload_config(self) -> bool:
        """
        重新加载所有配置
        
        Returns:
            是否重新加载成功
        """
        try:
            self.logger.info("重新加载所有配置...")
            self._load_all_configs()
            self.logger.info("配置重新加载完成")
            return True
        except Exception as e:
            self.logger.error(f"重新加载配置失败: {e}")
            return False
    
    def get_all_configs(self) -> Dict[str, Any]:
        """
        获取所有配置
        
        Returns:
            所有配置的字典
        """
        return self.get_config()
    
    def add_config_file(self, config_name: str, file_path: str) -> bool:
        """
        添加配置文件
        
        Args:
            config_name: 配置名称
            file_path: 文件路径（相对于配置目录）
        
        Returns:
            是否添加成功
        """
        try:
            full_path = self.config_dir / file_path
            if not full_path.exists():
                self.logger.warning(f"配置文件不存在: {full_path}")
                return False
            
            # 加载配置文件
            config_data = self._load_config_file(full_path)
            if config_data is not None:
                with self._config_lock:
                    self._config_data[config_name] = config_data
                
                # 添加到监控列表
                if self.enable_hot_reload:
                    self.watched_files[str(full_path)] = config_name
                
                self.logger.info(f"配置文件已添加: {config_name} -> {file_path}")
                return True
            
        except Exception as e:
            self.logger.error(f"添加配置文件失败: {e}")
        
        return False
    
    def save_config_to_file(self, config_name: str, file_path: str = None) -> bool:
        """
        保存配置到文件
        
        Args:
            config_name: 配置名称
            file_path: 文件路径，如果为None则使用默认路径
        
        Returns:
            是否保存成功
        """
        try:
            if file_path is None:
                file_path = self.default_config_files.get(config_name, f"{config_name}.json")
            
            full_path = self.config_dir / file_path
            config_data = self.get_config(config_name)
            
            if config_data is None:
                self.logger.error(f"配置不存在: {config_name}")
                return False
            
            # 根据文件扩展名选择格式
            if full_path.suffix.lower() in ['.yaml', '.yml']:
                with open(full_path, 'w', encoding='utf-8') as f:
                    yaml.dump(config_data, f, default_flow_style=False, 
                             allow_unicode=True, indent=2)
            else:
                with open(full_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置已保存: {config_name} -> {full_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False
    
    def add_change_callback(self, callback: Callable[[str, Any, Any], None]) -> None:
        """
        添加配置变更回调
        
        Args:
            callback: 回调函数，参数为 (key, old_value, new_value)
        """
        self._change_callbacks.append(callback)
    
    def remove_change_callback(self, callback: Callable[[str, Any, Any], None]) -> None:
        """
        移除配置变更回调
        
        Args:
            callback: 要移除的回调函数
        """
        if callback in self._change_callbacks:
            self._change_callbacks.remove(callback)
    
    def _load_all_configs(self) -> None:
        """加载所有配置文件"""
        with self._config_lock:
            self._config_data.clear()
            self.watched_files.clear()
            
            # 加载默认配置文件
            for config_name, file_name in self.default_config_files.items():
                file_path = self.config_dir / file_name
                if file_path.exists():
                    config_data = self._load_config_file(file_path)
                    if config_data is not None:
                        self._config_data[config_name] = config_data
                        if self.enable_hot_reload:
                            self.watched_files[str(file_path)] = config_name
            
            # 扫描配置目录中的其他配置文件
            for file_path in self.config_dir.glob('*.json'):
                if file_path.name not in self.default_config_files.values():
                    config_name = file_path.stem
                    config_data = self._load_config_file(file_path)
                    if config_data is not None:
                        self._config_data[config_name] = config_data
                        if self.enable_hot_reload:
                            self.watched_files[str(file_path)] = config_name
            
            for file_path in self.config_dir.glob('*.yaml'):
                if file_path.name not in self.default_config_files.values():
                    config_name = file_path.stem
                    config_data = self._load_config_file(file_path)
                    if config_data is not None:
                        self._config_data[config_name] = config_data
                        if self.enable_hot_reload:
                            self.watched_files[str(file_path)] = config_name
    
    def _load_config_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        加载单个配置文件
        
        Args:
            file_path: 配置文件路径
        
        Returns:
            配置数据，加载失败返回None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    return yaml.safe_load(f)
                else:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {file_path}, 错误: {e}")
            return None
    
    def _reload_config_file(self, file_path: str) -> None:
        """
        重新加载单个配置文件
        
        Args:
            file_path: 配置文件路径
        """
        try:
            if file_path not in self.watched_files:
                return
            
            config_name = self.watched_files[file_path]
            config_data = self._load_config_file(Path(file_path))
            
            if config_data is not None:
                with self._config_lock:
                    old_config = self._config_data.get(config_name)
                    self._config_data[config_name] = config_data
                
                # 触发变更回调
                self._notify_config_change(config_name, old_config, config_data)
                
                self.logger.info(f"配置文件已重新加载: {config_name}")
            
        except Exception as e:
            self.logger.error(f"重新加载配置文件失败: {file_path}, 错误: {e}")
    
    def _start_file_watcher(self) -> None:
        """启动文件监控"""
        try:
            if self.observer is not None:
                self.observer.stop()
            
            self.observer = Observer()
            event_handler = ConfigChangeHandler(self)
            self.observer.schedule(event_handler, str(self.config_dir), recursive=False)
            self.observer.start()
            
            self.logger.info("配置文件监控已启动")
            
        except Exception as e:
            self.logger.error(f"启动文件监控失败: {e}")
    
    def _notify_config_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """
        通知配置变更
        
        Args:
            key: 配置键
            old_value: 旧值
            new_value: 新值
        """
        for callback in self._change_callbacks:
            try:
                callback(key, old_value, new_value)
            except Exception as e:
                self.logger.error(f"配置变更回调执行失败: {e}")
    
    def __del__(self):
        """析构函数"""
        if hasattr(self, 'observer') and self.observer is not None:
            self.observer.stop()
            self.observer.join()


# 全局配置管理器实例
configuration_manager = ConfigurationManager()