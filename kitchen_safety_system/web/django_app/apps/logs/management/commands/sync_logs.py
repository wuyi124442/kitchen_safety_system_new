"""
同步核心日志系统到Django数据库的管理命令
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from ...services import LogService


class Command(BaseCommand):
    help = '从核心日志系统同步日志到Django数据库'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=1000,
            help='同步的日志数量限制 (默认: 1000)'
        )
        
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='同步后清理30天前的旧日志'
        )
    
    def handle(self, *args, **options):
        limit = options['limit']
        cleanup = options['cleanup']
        
        self.stdout.write(
            self.style.SUCCESS(f'开始同步日志，限制数量: {limit}')
        )
        
        try:
            # 同步日志
            synced_count = LogService.sync_from_core_logs(limit=limit)
            
            self.stdout.write(
                self.style.SUCCESS(f'成功同步 {synced_count} 条日志')
            )
            
            # 清理旧日志
            if cleanup:
                self.stdout.write('开始清理旧日志...')
                deleted_count = LogService.cleanup_old_logs(days=30)
                self.stdout.write(
                    self.style.SUCCESS(f'清理了 {deleted_count} 条旧日志')
                )
            
            # 显示统计信息
            stats = LogService.get_log_statistics(days=7)
            self.stdout.write('\n=== 最近7天日志统计 ===')
            self.stdout.write(f'总日志数: {stats["total_logs"]}')
            
            self.stdout.write('\n按级别统计:')
            for level, count in stats['level_statistics'].items():
                self.stdout.write(f'  {level}: {count}')
            
            self.stdout.write('\n按类型统计:')
            for log_type, count in stats['type_statistics'].items():
                self.stdout.write(f'  {log_type}: {count}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'同步日志失败: {str(e)}')
            )
            raise