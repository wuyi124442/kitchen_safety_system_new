"""
报警管理器演示脚本

演示AlertManager的各种功能：多渠道通知、去重、频率控制等。
"""

import time
from typing import List

from ..core.interfaces import AlertEvent, AlertType, AlertLevel
from ..core.models import SystemConfig
from .alert_manager import AlertManager, DeduplicationRule, FrequencyLimit


def create_demo_alerts() -> List[AlertEvent]:
    """创建演示用的报警事件"""
    current_time = time.time()
    
    alerts = [
        # 跌倒检测报警
        AlertEvent(
            alert_type=AlertType.FALL_DETECTED,
            alert_level=AlertLevel.CRITICAL,
            timestamp=current_time,
            location=(150, 200),
            description="检测到人员跌倒，位置在厨房中央",
            additional_data={'confidence': 0.95, 'person_id': 'person_1'}
        ),
        
        # 无人看管灶台报警
        AlertEvent(
            alert_type=AlertType.UNATTENDED_STOVE,
            alert_level=AlertLevel.HIGH,
            timestamp=current_time + 1,
            location=(300, 100),
            description="灶台无人看管已超过5分钟",
            additional_data={'stove_id': 'stove_1', 'unattended_duration': 300}
        ),
        
        # 系统错误报警
        AlertEvent(
            alert_type=AlertType.SYSTEM_ERROR,
            alert_level=AlertLevel.MEDIUM,
            timestamp=current_time + 2,
            location=None,
            description="摄像头连接不稳定",
            additional_data={'error_code': 'CAM_001', 'retry_count': 3}
        ),
        
        # 重复的跌倒报警（应该被去重）
        AlertEvent(
            alert_type=AlertType.FALL_DETECTED,
            alert_level=AlertLevel.CRITICAL,
            timestamp=current_time + 3,
            location=(155, 205),  # 相近位置
            description="检测到人员跌倒，位置在厨房中央",
            additional_data={'confidence': 0.92, 'person_id': 'person_1'}
        ),
        
        # 另一个位置的跌倒报警（不应该被去重）
        AlertEvent(
            alert_type=AlertType.FALL_DETECTED,
            alert_level=AlertLevel.CRITICAL,
            timestamp=current_time + 4,
            location=(500, 400),  # 远距离位置
            description="检测到人员跌倒，位置在厨房角落",
            additional_data={'confidence': 0.88, 'person_id': 'person_2'}
        )
    ]
    
    return alerts


def demo_basic_alert_management():
    """演示基本的报警管理功能"""
    print("=== 基本报警管理演示 ===")
    
    # 创建配置
    config = SystemConfig()
    config.enable_sound_alert = False  # 演示时禁用声音
    config.enable_email_alert = False  # 演示时禁用邮件
    
    # 创建AlertManager
    alert_manager = AlertManager(config)
    
    # 创建演示报警
    alerts = create_demo_alerts()
    
    print(f"准备处理 {len(alerts)} 个报警事件...")
    print()
    
    # 逐个处理报警
    for i, alert in enumerate(alerts, 1):
        print(f"处理报警 {i}: {alert.alert_type.value} - {alert.description}")
        
        result = alert_manager.trigger_alert(alert)
        
        if result:
            print("✓ 报警处理成功")
        else:
            print("✗ 报警处理失败")
        
        print()
        time.sleep(0.5)  # 短暂延迟
    
    # 显示统计信息
    stats = alert_manager.get_alert_statistics()
    print("=== 处理统计 ===")
    print(f"总报警数: {stats['total_alerts']}")
    print(f"成功发送: {stats['sent_alerts']}")
    print(f"去重报警: {stats['deduplicated_alerts']}")
    print(f"频率限制: {stats['rate_limited_alerts']}")
    print(f"失败报警: {stats['failed_alerts']}")
    print(f"活跃报警: {stats['active_alerts']}")
    print()
    
    # 显示渠道统计
    print("=== 渠道统计 ===")
    for channel, channel_stats in stats['channel_stats'].items():
        print(f"{channel}: 发送 {channel_stats['sent']}, 失败 {channel_stats['failed']}")
    print()
    
    return alert_manager


def demo_deduplication_rules():
    """演示去重规则功能"""
    print("=== 去重规则演示 ===")
    
    config = SystemConfig()
    config.enable_sound_alert = False
    config.enable_email_alert = False
    
    alert_manager = AlertManager(config)
    
    # 添加严格的去重规则
    strict_rule = DeduplicationRule(
        alert_type=AlertType.FALL_DETECTED,
        time_window=60.0,  # 60秒内
        location_threshold=50.0,  # 50像素内
        description_similarity=0.7  # 70%相似度
    )
    
    alert_manager.add_deduplication_rule(strict_rule)
    print("已添加严格的跌倒报警去重规则（60秒内，50像素内，70%相似度）")
    
    # 创建相似的报警
    base_time = time.time()
    similar_alerts = [
        AlertEvent(
            alert_type=AlertType.FALL_DETECTED,
            alert_level=AlertLevel.HIGH,
            timestamp=base_time,
            location=(100, 100),
            description="厨房中央检测到跌倒"
        ),
        AlertEvent(
            alert_type=AlertType.FALL_DETECTED,
            alert_level=AlertLevel.HIGH,
            timestamp=base_time + 5,
            location=(120, 110),  # 相近位置
            description="厨房中央检测到跌倒"  # 相同描述
        ),
        AlertEvent(
            alert_type=AlertType.FALL_DETECTED,
            alert_level=AlertLevel.HIGH,
            timestamp=base_time + 10,
            location=(200, 200),  # 远距离
            description="厨房角落检测到跌倒"  # 不同描述
        )
    ]
    
    print("\n处理相似报警...")
    for i, alert in enumerate(similar_alerts, 1):
        print(f"报警 {i}: 位置 {alert.location}, 描述: {alert.description}")
        result = alert_manager.trigger_alert(alert)
        print(f"处理结果: {'成功' if result else '失败'}")
    
    stats = alert_manager.get_alert_statistics()
    print(f"\n结果: 总计 {stats['total_alerts']}, 发送 {stats['sent_alerts']}, 去重 {stats['deduplicated_alerts']}")
    print()
    
    return alert_manager


def demo_frequency_limiting():
    """演示频率限制功能"""
    print("=== 频率限制演示 ===")
    
    config = SystemConfig()
    config.enable_sound_alert = False
    config.enable_email_alert = False
    
    alert_manager = AlertManager(config)
    
    # 添加严格的频率限制
    strict_limit = FrequencyLimit(
        alert_type=AlertType.SYSTEM_ERROR,
        max_count=2,  # 最多2次
        time_window=30.0,  # 30秒内
        cooldown_time=10.0  # 冷却10秒
    )
    
    alert_manager.add_frequency_limit(strict_limit)
    print("已添加系统错误频率限制（30秒内最多2次，冷却10秒）")
    
    # 快速触发多个系统错误
    base_time = time.time()
    print("\n快速触发5个系统错误报警...")
    
    for i in range(5):
        alert = AlertEvent(
            alert_type=AlertType.SYSTEM_ERROR,
            alert_level=AlertLevel.MEDIUM,
            timestamp=base_time + i,
            location=None,
            description=f"系统错误 #{i+1}"
        )
        
        print(f"触发报警 {i+1}: {alert.description}")
        result = alert_manager.trigger_alert(alert)
        print(f"处理结果: {'成功' if result else '失败'}")
        
        time.sleep(0.2)
    
    stats = alert_manager.get_alert_statistics()
    print(f"\n结果: 总计 {stats['total_alerts']}, 发送 {stats['sent_alerts']}, 频率限制 {stats['rate_limited_alerts']}")
    print()
    
    return alert_manager


def demo_alert_history_management():
    """演示报警历史管理功能"""
    print("=== 报警历史管理演示 ===")
    
    config = SystemConfig()
    config.enable_sound_alert = False
    config.enable_email_alert = False
    
    alert_manager = AlertManager(config)
    
    # 触发一些报警
    alerts = create_demo_alerts()[:3]  # 只取前3个
    
    print("触发报警并查看历史记录...")
    for alert in alerts:
        alert_manager.trigger_alert(alert)
    
    # 获取最近报警
    recent_alerts = alert_manager.get_recent_alerts(5)
    print(f"\n最近 {len(recent_alerts)} 个报警:")
    
    for i, record in enumerate(recent_alerts, 1):
        print(f"{i}. [{record['alert_level'].upper()}] {record['alert_type']}")
        print(f"   时间: {time.strftime('%H:%M:%S', time.localtime(record['timestamp']))}")
        print(f"   描述: {record['description']}")
        print(f"   渠道: {', '.join(record['sent_channels'])}")
        print(f"   状态: {'已解决' if record['is_resolved'] else '未解决'}")
        print()
    
    # 解决第一个报警
    if recent_alerts:
        first_alert_id = recent_alerts[0]['alert_id']
        print(f"解决报警: {first_alert_id}")
        alert_manager.resolve_alert(first_alert_id)
        
        # 再次查看统计
        stats = alert_manager.get_alert_statistics()
        print(f"解决后活跃报警数: {stats['active_alerts']}")
    
    print()
    return alert_manager


def main():
    """主演示函数"""
    print("厨房安全系统 - 报警管理器演示")
    print("=" * 50)
    print()
    
    try:
        # 基本功能演示
        demo_basic_alert_management()
        
        # 去重功能演示
        demo_deduplication_rules()
        
        # 频率限制演示
        demo_frequency_limiting()
        
        # 历史管理演示
        demo_alert_history_management()
        
        print("演示完成！")
        
    except KeyboardInterrupt:
        print("\n演示被用户中断")
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")


if __name__ == "__main__":
    main()