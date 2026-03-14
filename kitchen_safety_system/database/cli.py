#!/usr/bin/env python3
"""
数据库管理CLI工具

提供数据库和缓存系统的命令行管理功能。
"""

import click
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from kitchen_safety_system.database import (
    get_db_connection, get_cache_manager,
    alert_repo, log_repo, config_repo, stats_repo
)
from kitchen_safety_system.utils.logger import get_logger

logger = get_logger(__name__)


@click.group()
def cli():
    """厨房安全检测系统数据库管理工具"""
    pass


@cli.group()
def db():
    """数据库操作"""
    pass


@cli.group()
def cache():
    """缓存操作"""
    pass


@cli.group()
def config():
    """配置管理"""
    pass


# 数据库操作命令
@db.command()
def status():
    """检查数据库连接状态"""
    db_manager = get_db_connection()
    
    # 检查PostgreSQL连接
    pg_status = "✓ 连接成功" if db_manager.connect_postgresql() else "✗ 连接失败"
    click.echo(f"PostgreSQL: {pg_status}")
    
    # 检查Redis连接
    redis_status = "✓ 连接成功" if db_manager.connect_redis() else "✗ 连接失败"
    click.echo(f"Redis: {redis_status}")


@db.command()
@click.option('--days', default=7, help='统计天数')
def stats(days):
    """显示数据库统计信息"""
    try:
        # 报警统计
        alert_stats = alert_repo.get_statistics(days)
        click.echo(f"\n📊 最近 {days} 天报警统计:")
        click.echo(f"  总报警数: {alert_stats['total_alerts']}")
        click.echo(f"  已解决: {alert_stats['resolved_alerts']}")
        
        if alert_stats['by_type']:
            click.echo("\n  按类型分布:")
            for alert_type, counts in alert_stats['by_type'].items():
                click.echo(f"    {alert_type}: {counts['total']} (已解决: {counts['resolved']})")
        
        # 今日汇总
        today_summary = stats_repo.get_today_summary()
        click.echo(f"\n📅 今日汇总:")
        click.echo(f"  总报警: {today_summary['total_alerts']}")
        click.echo(f"  跌倒报警: {today_summary['fall_alerts']}")
        click.echo(f"  灶台报警: {today_summary['stove_alerts']}")
        click.echo(f"  已解决: {today_summary['resolved_alerts']}")
        
    except Exception as e:
        click.echo(f"❌ 获取统计信息失败: {e}", err=True)


@db.command()
@click.option('--limit', default=10, help='显示数量')
@click.option('--type', 'alert_type', help='报警类型过滤')
def alerts(limit, alert_type):
    """显示报警记录"""
    try:
        if alert_type:
            records = alert_repo.get_by_type(alert_type, limit)
        else:
            # 获取最近的报警记录
            end_date = datetime.now()
            start_date = end_date - timedelta(days=7)
            records = alert_repo.get_by_date_range(start_date, end_date)[:limit]
        
        if not records:
            click.echo("📭 没有找到报警记录")
            return
        
        click.echo(f"\n🚨 报警记录 (最近 {len(records)} 条):")
        for record in records:
            status = "✅ 已解决" if record.resolved else "⏳ 未解决"
            click.echo(f"  [{record.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] "
                      f"{record.alert_type} ({record.alert_level}) - {status}")
            if record.description:
                click.echo(f"    描述: {record.description}")
        
    except Exception as e:
        click.echo(f"❌ 获取报警记录失败: {e}", err=True)


@db.command()
@click.option('--limit', default=10, help='显示数量')
@click.option('--level', help='日志级别过滤')
def logs(limit, level):
    """显示日志记录"""
    try:
        if level:
            records = log_repo.get_by_level(level.upper(), limit)
        else:
            # 获取最近的日志记录
            end_date = datetime.now()
            start_date = end_date - timedelta(hours=1)
            records = log_repo.get_by_date_range(start_date, end_date)[:limit]
        
        if not records:
            click.echo("📭 没有找到日志记录")
            return
        
        click.echo(f"\n📝 日志记录 (最近 {len(records)} 条):")
        for record in records:
            level_icon = {
                'DEBUG': '🔍',
                'INFO': 'ℹ️',
                'WARNING': '⚠️',
                'ERROR': '❌',
                'CRITICAL': '🔥'
            }.get(record.level, '📝')
            
            click.echo(f"  {level_icon} [{record.timestamp.strftime('%H:%M:%S')}] "
                      f"{record.level}: {record.message}")
            if record.module:
                click.echo(f"    模块: {record.module}")
        
    except Exception as e:
        click.echo(f"❌ 获取日志记录失败: {e}", err=True)


# 缓存操作命令
@cache.command()
def info():
    """显示缓存信息"""
    try:
        cache_manager = get_cache_manager()
        info = cache_manager.get_cache_info()
        
        if not info:
            click.echo("❌ 无法获取缓存信息")
            return
        
        click.echo("\n💾 Redis 缓存信息:")
        redis_info = info.get('redis_info', {})
        click.echo(f"  内存使用: {redis_info.get('used_memory', 'N/A')}")
        click.echo(f"  连接客户端: {redis_info.get('connected_clients', 0)}")
        click.echo(f"  命令处理总数: {redis_info.get('total_commands_processed', 0)}")
        click.echo(f"  缓存命中: {redis_info.get('keyspace_hits', 0)}")
        click.echo(f"  缓存未命中: {redis_info.get('keyspace_misses', 0)}")
        
        click.echo(f"\n🔑 缓存键统计:")
        key_counts = info.get('key_counts', {})
        for prefix, count in key_counts.items():
            prefix_name = prefix.split(':')[-1]
            click.echo(f"  {prefix_name}: {count} 个键")
        
        click.echo(f"\n总键数: {info.get('total_keys', 0)}")
        
    except Exception as e:
        click.echo(f"❌ 获取缓存信息失败: {e}", err=True)


@cache.command()
@click.option('--prefix', help='缓存前缀')
@click.confirmation_option(prompt='确定要清理缓存吗？')
def clear(prefix):
    """清理缓存"""
    try:
        cache_manager = get_cache_manager()
        result = cache_manager.clear_cache(prefix)
        
        if result:
            scope = f"前缀 '{prefix}'" if prefix else "所有"
            click.echo(f"✅ 成功清理 {scope} 缓存")
        else:
            click.echo("❌ 清理缓存失败")
        
    except Exception as e:
        click.echo(f"❌ 清理缓存失败: {e}", err=True)


@cache.command()
@click.argument('data_type')
@click.option('--count', default=10, help='获取数量')
def realtime(data_type, count):
    """显示实时数据"""
    try:
        cache_manager = get_cache_manager()
        data = cache_manager.get_realtime_data(data_type, count)
        
        if not data:
            click.echo(f"📭 没有找到 '{data_type}' 类型的实时数据")
            return
        
        click.echo(f"\n⚡ 实时数据 '{data_type}' (最近 {len(data)} 条):")
        for item in data:
            timestamp = datetime.fromtimestamp(item.get('timestamp', 0))
            click.echo(f"  [{timestamp.strftime('%H:%M:%S')}] {json.dumps(item.get('data', {}), ensure_ascii=False, indent=2)}")
        
    except Exception as e:
        click.echo(f"❌ 获取实时数据失败: {e}", err=True)


# 配置管理命令
@config.command()
def list():
    """列出所有配置"""
    try:
        configs = config_repo.get_all()
        
        if not configs:
            click.echo("📭 没有找到配置")
            return
        
        click.echo("\n⚙️ 系统配置:")
        for key, value in configs.items():
            click.echo(f"\n  {key}:")
            click.echo(f"    {json.dumps(value, ensure_ascii=False, indent=4)}")
        
    except Exception as e:
        click.echo(f"❌ 获取配置失败: {e}", err=True)


@config.command()
@click.argument('key')
def get(key):
    """获取指定配置"""
    try:
        value = config_repo.get(key)
        
        if value is None:
            click.echo(f"❌ 配置 '{key}' 不存在")
            return
        
        click.echo(f"\n⚙️ 配置 '{key}':")
        click.echo(json.dumps(value, ensure_ascii=False, indent=2))
        
    except Exception as e:
        click.echo(f"❌ 获取配置失败: {e}", err=True)


@config.command()
@click.argument('key')
@click.argument('value')
@click.option('--user', default='cli', help='更新者')
def set(key, value, user):
    """设置配置"""
    try:
        # 尝试解析JSON
        try:
            parsed_value = json.loads(value)
        except json.JSONDecodeError:
            # 如果不是JSON，作为字符串处理
            parsed_value = {"value": value}
        
        result = config_repo.set(key, parsed_value, user)
        
        if result:
            click.echo(f"✅ 配置 '{key}' 设置成功")
            
            # 清理相关缓存
            cache_manager = get_cache_manager()
            cache_manager.invalidate_config_cache(key)
            click.echo("🗑️ 相关缓存已清理")
        else:
            click.echo(f"❌ 配置 '{key}' 设置失败")
        
    except Exception as e:
        click.echo(f"❌ 设置配置失败: {e}", err=True)


@config.command()
@click.argument('key')
@click.confirmation_option(prompt='确定要删除这个配置吗？')
def delete(key):
    """删除配置"""
    try:
        # 这里需要实现删除配置的逻辑
        # 当前的仓库接口没有删除方法，可以设置为null或空值
        result = config_repo.set(key, {}, 'cli_delete')
        
        if result:
            click.echo(f"✅ 配置 '{key}' 删除成功")
            
            # 清理相关缓存
            cache_manager = get_cache_manager()
            cache_manager.invalidate_config_cache(key)
            click.echo("🗑️ 相关缓存已清理")
        else:
            click.echo(f"❌ 配置 '{key}' 删除失败")
        
    except Exception as e:
        click.echo(f"❌ 删除配置失败: {e}", err=True)


# 维护命令
@cli.command()
def maintenance():
    """执行数据库维护任务"""
    try:
        click.echo("🔧 开始数据库维护...")
        
        # 清理过期的检测统计数据（保留30天）
        cutoff_date = datetime.now() - timedelta(days=30)
        db_manager = get_db_connection()
        
        with db_manager.get_pg_cursor() as cursor:
            cursor.execute(
                "DELETE FROM detection_stats WHERE timestamp < %s",
                (cutoff_date,)
            )
            deleted_stats = cursor.rowcount
            click.echo(f"  清理过期统计数据: {deleted_stats} 条")
            
            # 清理过期的日志记录（保留7天）
            log_cutoff = datetime.now() - timedelta(days=7)
            cursor.execute(
                "DELETE FROM log_records WHERE timestamp < %s AND level IN ('DEBUG', 'INFO')",
                (log_cutoff,)
            )
            deleted_logs = cursor.rowcount
            click.echo(f"  清理过期日志记录: {deleted_logs} 条")
        
        # 清理过期缓存
        cache_manager = get_cache_manager()
        cache_manager.clear_cache()
        click.echo("  清理过期缓存: 完成")
        
        click.echo("✅ 数据库维护完成")
        
    except Exception as e:
        click.echo(f"❌ 数据库维护失败: {e}", err=True)


@cli.command()
def backup():
    """备份数据库"""
    try:
        import subprocess
        from datetime import datetime
        
        # 生成备份文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"kitchen_safety_backup_{timestamp}.sql"
        
        # 执行pg_dump
        cmd = [
            'pg_dump',
            '-h', 'localhost',
            '-p', '5432',
            '-U', 'kitchen_user',
            '-d', 'kitchen_safety',
            '-f', backup_file
        ]
        
        click.echo(f"🗄️ 开始备份数据库到 {backup_file}...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            click.echo(f"✅ 数据库备份成功: {backup_file}")
        else:
            click.echo(f"❌ 数据库备份失败: {result.stderr}")
        
    except Exception as e:
        click.echo(f"❌ 数据库备份失败: {e}", err=True)


if __name__ == '__main__':
    cli()