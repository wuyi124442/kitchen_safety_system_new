"""
通知渠道实现

实现各种通知渠道：声音、邮件、短信、控制台等。
"""

import os
import time
import smtplib
import requests
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..core.interfaces import AlertEvent, AlertType, AlertLevel
from ..utils.logger import get_logger


@dataclass
class NotificationConfig:
    """通知配置数据结构"""
    enabled: bool = True
    priority_levels: List[AlertLevel] = None
    retry_attempts: int = 3
    retry_delay: float = 1.0
    additional_settings: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.priority_levels is None:
            self.priority_levels = [AlertLevel.HIGH, AlertLevel.CRITICAL]
        if self.additional_settings is None:
            self.additional_settings = {}


class NotificationChannel(ABC):
    """通知渠道抽象基类"""
    
    def __init__(self, config: NotificationConfig):
        """
        初始化通知渠道
        
        Args:
            config: 通知配置
        """
        self.config = config
        self.logger = get_logger(f"{__name__}.{self.__class__.__name__}")
        self.is_initialized = False
        
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化通知渠道
        
        Returns:
            bool: 是否初始化成功
        """
        pass
    
    @abstractmethod
    def send_notification(self, alert_event: AlertEvent) -> bool:
        """
        发送通知
        
        Args:
            alert_event: 报警事件
            
        Returns:
            bool: 是否发送成功
        """
        pass
    
    def should_notify(self, alert_event: AlertEvent) -> bool:
        """
        判断是否应该发送通知
        
        Args:
            alert_event: 报警事件
            
        Returns:
            bool: 是否应该通知
        """
        if not self.config.enabled:
            return False
            
        return alert_event.alert_level in self.config.priority_levels
    
    def send_with_retry(self, alert_event: AlertEvent) -> bool:
        """
        带重试机制的发送通知
        
        Args:
            alert_event: 报警事件
            
        Returns:
            bool: 是否发送成功
        """
        if not self.should_notify(alert_event):
            return True  # 不需要发送，视为成功
            
        if not self.is_initialized and not self.initialize():
            self.logger.error("通知渠道未初始化")
            return False
        
        for attempt in range(self.config.retry_attempts):
            try:
                if self.send_notification(alert_event):
                    return True
                    
            except Exception as e:
                self.logger.warning(f"发送通知失败 (尝试 {attempt + 1}/{self.config.retry_attempts}): {e}")
                
            if attempt < self.config.retry_attempts - 1:
                time.sleep(self.config.retry_delay)
        
        self.logger.error(f"发送通知最终失败，已重试 {self.config.retry_attempts} 次")
        return False


class SoundNotificationChannel(NotificationChannel):
    """声音通知渠道"""
    
    def __init__(self, config: NotificationConfig):
        super().__init__(config)
        self.sound_files = self.config.additional_settings.get('sound_files', {})
        self.default_sound = self.config.additional_settings.get('default_sound', 'beep')
        self.volume = self.config.additional_settings.get('volume', 0.8)
        
    def initialize(self) -> bool:
        """初始化声音系统"""
        try:
            # 检查系统声音支持
            if os.name == 'nt':  # Windows
                self.sound_method = 'windows'
            elif os.name == 'posix':  # Linux/Mac
                # 检查可用的音频播放器
                for player in ['aplay', 'paplay', 'afplay', 'play']:
                    if subprocess.run(['which', player], capture_output=True).returncode == 0:
                        self.sound_method = player
                        break
                else:
                    self.sound_method = 'beep'
            else:
                self.sound_method = 'beep'
            
            self.is_initialized = True
            self.logger.info(f"声音通知渠道已初始化，使用方法: {self.sound_method}")
            return True
            
        except Exception as e:
            self.logger.error(f"声音通知渠道初始化失败: {e}")
            return False
    
    def send_notification(self, alert_event: AlertEvent) -> bool:
        """发送声音通知"""
        try:
            # 根据报警类型选择声音
            sound_key = alert_event.alert_type.value
            sound_file = self.sound_files.get(sound_key)
            
            if sound_file and os.path.exists(sound_file):
                return self._play_sound_file(sound_file)
            else:
                return self._play_system_beep(alert_event.alert_level)
                
        except Exception as e:
            self.logger.error(f"发送声音通知失败: {e}")
            return False
    
    def _play_sound_file(self, sound_file: str) -> bool:
        """播放声音文件"""
        try:
            if self.sound_method == 'windows':
                import winsound
                winsound.PlaySound(sound_file, winsound.SND_FILENAME)
            elif self.sound_method in ['aplay', 'paplay', 'afplay', 'play']:
                subprocess.run([self.sound_method, sound_file], check=True, capture_output=True)
            else:
                self.logger.warning(f"不支持的声音播放方法: {self.sound_method}")
                return False
                
            return True
            
        except Exception as e:
            self.logger.error(f"播放声音文件失败: {e}")
            return False
    
    def _play_system_beep(self, alert_level: AlertLevel) -> bool:
        """播放系统提示音"""
        try:
            # 根据报警级别确定提示音次数
            beep_count = {
                AlertLevel.LOW: 1,
                AlertLevel.MEDIUM: 2,
                AlertLevel.HIGH: 3,
                AlertLevel.CRITICAL: 5
            }.get(alert_level, 1)
            
            if self.sound_method == 'windows':
                import winsound
                for _ in range(beep_count):
                    winsound.Beep(1000, 500)  # 1000Hz, 500ms
                    time.sleep(0.2)
            else:
                for _ in range(beep_count):
                    print('\a', end='', flush=True)  # ASCII bell character
                    time.sleep(0.3)
            
            return True
            
        except Exception as e:
            self.logger.error(f"播放系统提示音失败: {e}")
            return False


class EmailNotificationChannel(NotificationChannel):
    """邮件通知渠道"""
    
    def __init__(self, config: NotificationConfig):
        super().__init__(config)
        self.smtp_server = self.config.additional_settings.get('smtp_server', 'smtp.gmail.com')
        self.smtp_port = self.config.additional_settings.get('smtp_port', 587)
        self.username = self.config.additional_settings.get('username', '')
        self.password = self.config.additional_settings.get('password', '')
        self.from_email = self.config.additional_settings.get('from_email', self.username)
        self.to_emails = self.config.additional_settings.get('to_emails', [])
        self.use_tls = self.config.additional_settings.get('use_tls', True)
        
    def initialize(self) -> bool:
        """初始化邮件系统"""
        try:
            if not self.username or not self.password:
                self.logger.error("邮件用户名或密码未配置")
                return False
                
            if not self.to_emails:
                self.logger.error("收件人邮箱未配置")
                return False
            
            # 测试SMTP连接
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
            
            self.is_initialized = True
            self.logger.info("邮件通知渠道已初始化")
            return True
            
        except Exception as e:
            self.logger.error(f"邮件通知渠道初始化失败: {e}")
            return False
    
    def send_notification(self, alert_event: AlertEvent) -> bool:
        """发送邮件通知"""
        try:
            # 简化的邮件发送实现
            subject = self._create_subject(alert_event)
            body = self._create_email_body(alert_event)
            
            # 创建简单的邮件消息
            message = f"Subject: {subject}\r\n\r\n{body}"
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.username, self.password)
                
                for to_email in self.to_emails:
                    server.sendmail(self.from_email, to_email, message.encode('utf-8'))
            
            self.logger.info(f"邮件通知已发送: {alert_event.alert_type.value}")
            return True
            
        except Exception as e:
            self.logger.error(f"发送邮件通知失败: {e}")
            return False
    
    def _create_subject(self, alert_event: AlertEvent) -> str:
        """创建邮件主题"""
        level_text = {
            AlertLevel.LOW: "低级",
            AlertLevel.MEDIUM: "中级", 
            AlertLevel.HIGH: "高级",
            AlertLevel.CRITICAL: "紧急"
        }.get(alert_event.alert_level, "未知")
        
        type_text = {
            AlertType.FALL_DETECTED: "跌倒检测",
            AlertType.UNATTENDED_STOVE: "灶台无人看管",
            AlertType.SYSTEM_ERROR: "系统错误"
        }.get(alert_event.alert_type, "未知报警")
        
        return f"【厨房安全系统】{level_text}报警 - {type_text}"
    
    def _create_email_body(self, alert_event: AlertEvent) -> str:
        """创建邮件正文"""
        timestamp_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(alert_event.timestamp))
        
        body = f"""厨房安全系统报警通知

报警类型: {alert_event.alert_type.value}
报警级别: {alert_event.alert_level.value}
发生时间: {timestamp_str}
描述: {alert_event.description}
"""
        
        if alert_event.location:
            body += f"位置: ({alert_event.location[0]}, {alert_event.location[1]})\n"
        
        if alert_event.additional_data:
            body += "\n附加信息:\n"
            for key, value in alert_event.additional_data.items():
                body += f"{key}: {value}\n"
        
        body += "\n此邮件由厨房安全检测系统自动发送，请及时处理相关安全事件。"
        
        return body


class SMSNotificationChannel(NotificationChannel):
    """短信通知渠道"""
    
    def __init__(self, config: NotificationConfig):
        super().__init__(config)
        self.api_url = self.config.additional_settings.get('api_url', '')
        self.api_key = self.config.additional_settings.get('api_key', '')
        self.api_secret = self.config.additional_settings.get('api_secret', '')
        self.phone_numbers = self.config.additional_settings.get('phone_numbers', [])
        self.sender_id = self.config.additional_settings.get('sender_id', 'KitchenSafety')
        
    def initialize(self) -> bool:
        """初始化短信系统"""
        try:
            if not self.api_url or not self.api_key:
                self.logger.error("短信API配置不完整")
                return False
                
            if not self.phone_numbers:
                self.logger.error("接收短信的手机号码未配置")
                return False
            
            # 测试API连接（可选）
            # 这里可以添加API连接测试逻辑
            
            self.is_initialized = True
            self.logger.info("短信通知渠道已初始化")
            return True
            
        except Exception as e:
            self.logger.error(f"短信通知渠道初始化失败: {e}")
            return False
    
    def send_notification(self, alert_event: AlertEvent) -> bool:
        """发送短信通知"""
        try:
            message = self._create_sms_message(alert_event)
            
            success_count = 0
            for phone_number in self.phone_numbers:
                if self._send_sms_to_number(phone_number, message):
                    success_count += 1
            
            # 如果至少有一个号码发送成功，视为成功
            success = success_count > 0
            
            if success:
                self.logger.info(f"短信通知已发送到 {success_count}/{len(self.phone_numbers)} 个号码")
            else:
                self.logger.error("所有短信发送均失败")
                
            return success
            
        except Exception as e:
            self.logger.error(f"发送短信通知失败: {e}")
            return False
    
    def _create_sms_message(self, alert_event: AlertEvent) -> str:
        """创建短信内容"""
        timestamp_str = time.strftime('%H:%M:%S', time.localtime(alert_event.timestamp))
        
        type_text = {
            AlertType.FALL_DETECTED: "跌倒",
            AlertType.UNATTENDED_STOVE: "灶台无人看管", 
            AlertType.SYSTEM_ERROR: "系统错误"
        }.get(alert_event.alert_type, "未知")
        
        level_text = {
            AlertLevel.LOW: "低级",
            AlertLevel.MEDIUM: "中级",
            AlertLevel.HIGH: "高级", 
            AlertLevel.CRITICAL: "紧急"
        }.get(alert_event.alert_level, "")
        
        message = f"【厨房安全】{level_text}报警 {timestamp_str}\n{type_text}: {alert_event.description}"
        
        # 限制短信长度
        if len(message) > 160:
            message = message[:157] + "..."
            
        return message
    
    def _send_sms_to_number(self, phone_number: str, message: str) -> bool:
        """发送短信到指定号码"""
        try:
            # 这里实现具体的短信API调用
            # 示例使用通用REST API格式
            payload = {
                'api_key': self.api_key,
                'api_secret': self.api_secret,
                'to': phone_number,
                'from': self.sender_id,
                'text': message
            }
            
            response = requests.post(
                self.api_url,
                json=payload,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                # 根据具体API响应格式判断成功
                if result.get('status') == 'success' or result.get('code') == 0:
                    return True
                else:
                    self.logger.warning(f"短信API返回错误: {result}")
                    return False
            else:
                self.logger.warning(f"短信API请求失败: {response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"发送短信到 {phone_number} 失败: {e}")
            return False


class ConsoleNotificationChannel(NotificationChannel):
    """控制台通知渠道"""
    
    def __init__(self, config: NotificationConfig):
        super().__init__(config)
        self.use_colors = self.config.additional_settings.get('use_colors', True)
        self.show_timestamp = self.config.additional_settings.get('show_timestamp', True)
        
    def initialize(self) -> bool:
        """初始化控制台通知"""
        self.is_initialized = True
        self.logger.info("控制台通知渠道已初始化")
        return True
    
    def send_notification(self, alert_event: AlertEvent) -> bool:
        """发送控制台通知"""
        try:
            message = self._format_console_message(alert_event)
            print(message)
            return True
            
        except Exception as e:
            self.logger.error(f"发送控制台通知失败: {e}")
            return False
    
    def _format_console_message(self, alert_event: AlertEvent) -> str:
        """格式化控制台消息"""
        # 颜色代码
        colors = {
            AlertLevel.LOW: '\033[92m',      # 绿色
            AlertLevel.MEDIUM: '\033[93m',   # 黄色
            AlertLevel.HIGH: '\033[91m',     # 红色
            AlertLevel.CRITICAL: '\033[95m'  # 紫色
        } if self.use_colors else {}
        
        reset_color = '\033[0m' if self.use_colors else ''
        
        # 时间戳
        timestamp_str = ""
        if self.show_timestamp:
            timestamp_str = time.strftime('[%Y-%m-%d %H:%M:%S] ', time.localtime(alert_event.timestamp))
        
        # 报警级别颜色
        level_color = colors.get(alert_event.alert_level, '')
        
        # 构建消息
        message = f"{timestamp_str}{level_color}[{alert_event.alert_level.value.upper()}] "
        message += f"{alert_event.alert_type.value}: {alert_event.description}{reset_color}"
        
        if alert_event.location:
            message += f" (位置: {alert_event.location[0]}, {alert_event.location[1]})"
        
        return message