"""
配置管理模块

提供系统配置的加载、保存和管理功能。
"""

import os
import json
import yaml
from typing import Dict, Any, Optional
from pathlib import Path
from .models import SystemConfig


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_dir: str = "config"):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置文件目录
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.config_file = self.config_dir / "system_config.json"
        self.default_config_file = self.config_dir / "default_config.yaml"
        
        self._config = SystemConfig()
        self._load_config()
    
    def _load_config(self) -> None:
        """加载配置文件"""
        # 首先尝试加载用户配置
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                self._config = SystemConfig.from_dict(config_data)
                return
            except Exception as e:
                print(f"加载用户配置失败: {e}")
        
        # 如果用户配置不存在，尝试加载默认配置
        if self.default_config_file.exists():
            try:
                with open(self.default_config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                self._config = SystemConfig.from_dict(config_data)
                return
            except Exception as e:
                print(f"加载默认配置失败: {e}")
        
        # 如果都不存在，使用内置默认配置并保存
        self._save_config()
    
    def _save_config(self) -> None:
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置失败: {e}")
    
    def get_config(self, key: str = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键名，如果为None则返回整个配置对象
            
        Returns:
            配置值或配置对象
        """
        if key is None:
            return self._config
        
        return getattr(self._config, key, None)
    
    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置值
        
        Args:
            key: 配置键名
            value: 配置值
            
        Returns:
            是否设置成功
        """
        try:
            if hasattr(self._config, key):
                setattr(self._config, key, value)
                self._save_config()
                return True
            return False
        except Exception:
            return False
    
    def update_config(self, config_dict: Dict[str, Any]) -> bool:
        """
        批量更新配置
        
        Args:
            config_dict: 配置字典
            
        Returns:
            是否更新成功
        """
        try:
            for key, value in config_dict.items():
                if hasattr(self._config, key):
                    setattr(self._config, key, value)
            self._save_config()
            return True
        except Exception:
            return False
    
    def reload_config(self) -> bool:
        """
        重新加载配置
        
        Returns:
            是否重新加载成功
        """
        try:
            self._load_config()
            return True
        except Exception:
            return False
    
    def reset_to_default(self) -> bool:
        """
        重置为默认配置
        
        Returns:
            是否重置成功
        """
        try:
            self._config = SystemConfig()
            self._save_config()
            return True
        except Exception:
            return False
    
    def export_config(self, file_path: str) -> bool:
        """
        导出配置到文件
        
        Args:
            file_path: 导出文件路径
            
        Returns:
            是否导出成功
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def import_config(self, file_path: str) -> bool:
        """
        从文件导入配置
        
        Args:
            file_path: 导入文件路径
            
        Returns:
            是否导入成功
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            self._config = SystemConfig.from_dict(config_data)
            self._save_config()
            return True
        except Exception:
            return False


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config(key: str = None) -> Any:
    """获取配置值的便捷函数"""
    return config_manager.get_config(key)


def set_config(key: str, value: Any) -> bool:
    """设置配置值的便捷函数"""
    return config_manager.set_config(key, value)


# 环境变量配置映射
ENV_CONFIG_MAPPING = {
    'KITCHEN_SAFETY_CONFIDENCE_THRESHOLD': 'confidence_threshold',
    'KITCHEN_SAFETY_VIDEO_SOURCE': 'video_input_source',
    'KITCHEN_SAFETY_VIDEO_FPS': 'video_fps',
    'KITCHEN_SAFETY_DETECTION_FPS': 'detection_fps',
    'KITCHEN_SAFETY_STOVE_DISTANCE': 'stove_distance_threshold',
    'KITCHEN_SAFETY_UNATTENDED_TIME': 'unattended_time_threshold',
    'KITCHEN_SAFETY_ENABLE_EMAIL': 'enable_email_alert',
    'KITCHEN_SAFETY_ENABLE_SMS': 'enable_sms_alert',
    'KITCHEN_SAFETY_ENABLE_SOUND': 'enable_sound_alert'
}


def load_config_from_env() -> None:
    """从环境变量加载配置"""
    for env_key, config_key in ENV_CONFIG_MAPPING.items():
        env_value = os.getenv(env_key)
        if env_value is not None:
            # 类型转换
            if config_key in ['confidence_threshold', 'stove_distance_threshold', 'fall_confidence_threshold']:
                try:
                    env_value = float(env_value)
                except ValueError:
                    continue
            elif config_key in ['video_fps', 'detection_fps', 'unattended_time_threshold', 'alert_cooldown_time']:
                try:
                    env_value = int(env_value)
                except ValueError:
                    continue
            elif config_key in ['enable_email_alert', 'enable_sms_alert', 'enable_sound_alert']:
                env_value = env_value.lower() in ('true', '1', 'yes', 'on')
            
            config_manager.set_config(config_key, env_value)