#!/usr/bin/env python3
# src/scripts/schedule_crawler.py

"""
爬虫调度器：定期执行爬虫任务，更新知识库
"""

import sys
import os
import time
import logging
import schedule
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{project_root}/logs/scheduler_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 创建logs目录（如果不存在）
Path(f"{project_root}/logs").mkdir(exist_ok=True)

def run_crawler(sites_file=None):
    """运行爬虫脚本"""
    logger.info("开始执行爬虫任务...")
    
    crawler_script = Path(__file__).parent / "crawl_immigration_sites.py"
    
    cmd = [sys.executable, str(crawler_script)]
    if sites_file:
        cmd.extend(["--sites", sites_file])
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"爬虫任务执行成功: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"爬虫任务执行失败: {e.stderr}")
        return False

def main():
    """主函数"""
    print("=" * 70)
    print("⏰ 爬虫调度器")
    print("=" * 70)
    
    # 解析命令行参数
    import argparse
    parser = argparse.ArgumentParser(description='定期执行爬虫任务，更新知识库')
    parser.add_argument('--sites', help='网站列表JSON文件路径')
    parser.add_argument('--daily', action='store_true', help='每天执行一次')
    parser.add_argument('--weekly', action='store_true', help='每周执行一次')
    parser.add_argument('--interval', type=int, default=0, help='执行间隔（小时）')
    parser.add_argument('--now', action='store_true', help='立即执行一次')
    args = parser.parse_args()
    
    sites_file = args.sites
    
    # 立即执行一次
    if args.now:
        logger.info("立即执行爬虫任务...")
        run_crawler(sites_file)
    
    # 设置定期执行计划
    if args.daily:
        logger.info("设置每天执行爬虫任务...")
        schedule.every().day.at("02:00").do(run_crawler, sites_file)  # 凌晨2点执行
    
    if args.weekly:
        logger.info("设置每周执行爬虫任务...")
        schedule.every().monday.at("03:00").do(run_crawler, sites_file)  # 每周一凌晨3点执行
    
    if args.interval > 0:
        logger.info(f"设置每 {args.interval} 小时执行爬虫任务...")
        schedule.every(args.interval).hours.do(run_crawler, sites_file)
    
    # 如果没有设置任何调度，默认每周执行一次
    if not (args.daily or args.weekly or args.interval > 0):
        logger.info("使用默认设置：每周执行爬虫任务...")
        schedule.every().monday.at("03:00").do(run_crawler, sites_file)
    
    logger.info("爬虫调度器已启动，等待执行计划...")
    print("\n爬虫调度器已启动，按 Ctrl+C 停止")
    
    try:
        # 保持程序运行
        while True:
            schedule.run_pending()
            time.sleep(60)  # 每分钟检查一次
    except KeyboardInterrupt:
        logger.info("爬虫调度器已停止")
        print("\n爬虫调度器已停止")

if __name__ == "__main__":
    main() 