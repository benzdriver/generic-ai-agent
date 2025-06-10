#!/usr/bin/env python3
# scripts/schedule_kb_updates.py

"""
定期知识库更新调度器
使用 generic_knowledge_manager 来执行更新
"""

import asyncio
import schedule
import time
from datetime import datetime
from pathlib import Path
import sys
import argparse
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from generic_knowledge_manager import GenericKnowledgeManager

class KnowledgeBaseScheduler:
    """知识库更新调度器"""
    
    def __init__(self, config_file: str = "config/domains.yaml"):
        """初始化调度器，指定配置文件路径"""
        self.manager = GenericKnowledgeManager(config_file=config_file)
        
    async def run_scheduled_update(self):
        """运行定期更新"""
        logger.info(f"⏰ 定期更新检查开始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        try:
            # force=False 会让管理器根据每个源的配置决定是否更新
            await self.manager.update_all_domains(force_update=False)
            logger.info(f"✅ 定期更新检查完成: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        except Exception as e:
            logger.error(f"❌ 定期更新失败: {e}", exc_info=True)
    
    def setup_schedule(self, interval_hours: int = 1):
        """设置更新调度"""
        logger.info(f"📅 调度设置完成: 每 {interval_hours} 小时检查一次更新。")
        schedule.every(interval_hours).hours.do(lambda: asyncio.run(self.run_scheduled_update()))
    
    def run_scheduler(self, interval_hours: int):
        """运行调度器"""
        self.setup_schedule(interval_hours)
        
        logger.info("🔄 知识库更新调度器启动... 按 Ctrl+C 停止。")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # 每分钟检查一次任务队列
        except KeyboardInterrupt:
            logger.info("\n🛑 调度器已停止")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='通用知识库更新调度器')
    parser.add_argument('--config', default='config/domains.yaml', help='领域配置文件路径')
    parser.add_argument('--now', action='store_true', help='立即运行一次更新检查')
    parser.add_argument('--schedule', action='store_true', help='启动定期调度器')
    parser.add_argument('--interval', type=int, default=1, help='调度器检查更新的间隔时间（小时）')
    
    args = parser.parse_args()
    
    scheduler = KnowledgeBaseScheduler(config_file=args.config)
    
    if args.now:
        logger.info("🚀 立即运行知识库更新检查...")
        asyncio.run(scheduler.run_scheduled_update())
    elif args.schedule:
        scheduler.run_scheduler(interval_hours=args.interval)
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 