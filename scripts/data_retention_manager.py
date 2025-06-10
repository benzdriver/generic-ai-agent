#!/usr/bin/env python3
"""
数据保留和清理管理脚本
确保符合PIPEDA、CCPA等法规的数据保留要求
"""

import json
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import yaml
import argparse
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_retention.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataRetentionManager:
    """数据保留管理器"""
    
    def __init__(self, config_path: str = "compliance_policy.yaml"):
        """初始化数据保留管理器"""
        self.config_path = config_path
        self.config = self._load_config()
        self.audit_logs_dir = Path("audit_logs")
        self.archive_dir = Path("audit_archive")
        self.archive_dir.mkdir(exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """加载合规配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {self.config_path} not found, using defaults")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'pii_handling': {
                'retention': {
                    'pii_logs_days': 2555,      # 7年
                    'audit_logs_days': 2555,    # 7年
                    'general_logs_days': 365    # 1年
                }
            },
            'retention_policy': {
                'automatic_deletion': True,
                'deletion_verification': True
            }
        }
    
    def scan_expired_data(self, dry_run: bool = True) -> Dict[str, List[str]]:
        """扫描过期数据"""
        logger.info("开始扫描过期数据...")
        
        expired_files = {
            'general_logs': [],
            'audit_logs': [],
            'pii_logs': []
        }
        
        current_time = datetime.now()
        
        # 检查审计日志目录
        if self.audit_logs_dir.exists():
            for log_file in self.audit_logs_dir.glob("*.jsonl"):
                file_age = current_time - datetime.fromtimestamp(log_file.stat().st_mtime)
                
                if "pii" in log_file.name.lower():
                    retention_days = self.config['pii_handling']['retention']['pii_logs_days']
                    category = 'pii_logs'
                elif "audit" in log_file.name.lower():
                    retention_days = self.config['pii_handling']['retention']['audit_logs_days']
                    category = 'audit_logs'
                else:
                    retention_days = self.config['pii_handling']['retention']['general_logs_days']
                    category = 'general_logs'
                
                if file_age.days > retention_days:
                    expired_files[category].append(str(log_file))
                    logger.info(f"发现过期文件: {log_file} (保留期: {retention_days}天, 实际: {file_age.days}天)")
        
        # 检查普通日志
        logs_dir = Path("logs")
        if logs_dir.exists():
            for log_file in logs_dir.glob("*.log"):
                file_age = current_time - datetime.fromtimestamp(log_file.stat().st_mtime)
                retention_days = self.config['pii_handling']['retention']['general_logs_days']
                
                if file_age.days > retention_days:
                    expired_files['general_logs'].append(str(log_file))
                    logger.info(f"发现过期日志文件: {log_file} (保留期: {retention_days}天, 实际: {file_age.days}天)")
        
        return expired_files
    
    def archive_expired_data(self, expired_files: Dict[str, List[str]]) -> bool:
        """归档过期数据"""
        logger.info("开始归档过期数据...")
        
        success = True
        archive_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for category, files in expired_files.items():
            if not files:
                continue
                
            category_archive_dir = self.archive_dir / category / archive_timestamp
            category_archive_dir.mkdir(parents=True, exist_ok=True)
            
            for file_path in files:
                try:
                    source_path = Path(file_path)
                    if source_path.exists():
                        # 复制到归档目录
                        archive_path = category_archive_dir / source_path.name
                        shutil.copy2(source_path, archive_path)
                        logger.info(f"已归档: {source_path} -> {archive_path}")
                        
                        # 压缩归档文件
                        self._compress_file(archive_path)
                        
                except Exception as e:
                    logger.error(f"归档文件失败 {file_path}: {e}")
                    success = False
        
        return success
    
    def _compress_file(self, file_path: Path):
        """压缩文件"""
        try:
            import gzip
            
            with open(file_path, 'rb') as f_in:
                with gzip.open(f"{file_path}.gz", 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # 删除原文件
            file_path.unlink()
            logger.info(f"已压缩: {file_path}")
            
        except Exception as e:
            logger.error(f"压缩文件失败 {file_path}: {e}")
    
    def delete_expired_data(self, expired_files: Dict[str, List[str]], force: bool = False) -> bool:
        """删除过期数据"""
        if not force:
            logger.warning("删除操作需要 --force 参数确认")
            return False
        
        logger.info("开始删除过期数据...")
        
        success = True
        deleted_count = 0
        
        for category, files in expired_files.items():
            for file_path in files:
                try:
                    source_path = Path(file_path)
                    if source_path.exists():
                        source_path.unlink()
                        deleted_count += 1
                        logger.info(f"已删除: {source_path}")
                        
                except Exception as e:
                    logger.error(f"删除文件失败 {file_path}: {e}")
                    success = False
        
        logger.info(f"删除操作完成，共删除 {deleted_count} 个文件")
        return success
    
    def generate_retention_report(self) -> Dict[str, Any]:
        """生成数据保留报告"""
        logger.info("生成数据保留报告...")
        
        report = {
            "report_id": f"retention_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "generated_at": datetime.now().isoformat(),
            "retention_policy": self.config.get('retention_policy', {}),
            "file_summary": {
                "audit_logs": 0,
                "pii_logs": 0,
                "general_logs": 0,
                "archived_files": 0
            },
            "compliance_status": "compliant"
        }
        
        # 统计现有文件
        if self.audit_logs_dir.exists():
            report["file_summary"]["audit_logs"] = len(list(self.audit_logs_dir.glob("audit*.jsonl")))
            report["file_summary"]["pii_logs"] = len(list(self.audit_logs_dir.glob("pii*.jsonl")))
            report["file_summary"]["general_logs"] = len(list(self.audit_logs_dir.glob("system*.jsonl")))
        
        # 统计归档文件
        if self.archive_dir.exists():
            report["file_summary"]["archived_files"] = len(list(self.archive_dir.rglob("*.gz")))
        
        # 保存报告
        report_path = Path(f"compliance_reports/retention_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        report_path.parent.mkdir(exist_ok=True)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"报告已保存到: {report_path}")
        return report
    
    def run_retention_job(self, dry_run: bool = True, force_delete: bool = False):
        """运行数据保留作业"""
        logger.info(f"开始运行数据保留作业 (dry_run={dry_run})")
        
        try:
            # 1. 扫描过期数据
            expired_files = self.scan_expired_data(dry_run=dry_run)
            
            total_expired = sum(len(files) for files in expired_files.values())
            if total_expired == 0:
                logger.info("没有发现过期数据")
                return
            
            logger.info(f"发现 {total_expired} 个过期文件")
            
            if not dry_run:
                # 2. 归档过期数据
                if self.config.get('retention_policy', {}).get('automatic_deletion', False):
                    archive_success = self.archive_expired_data(expired_files)
                    
                    if archive_success:
                        # 3. 删除原始过期数据
                        delete_success = self.delete_expired_data(expired_files, force=force_delete)
                        
                        if delete_success:
                            logger.info("数据保留作业成功完成")
                        else:
                            logger.error("删除过期数据时出现错误")
                    else:
                        logger.error("归档过期数据时出现错误")
            
            # 4. 生成报告
            self.generate_retention_report()
            
        except Exception as e:
            logger.error(f"数据保留作业失败: {e}")
            raise

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="数据保留和清理管理工具")
    parser.add_argument("--config", default="compliance_policy.yaml", help="合规配置文件路径")
    parser.add_argument("--dry-run", action="store_true", help="仅扫描，不执行实际操作")
    parser.add_argument("--force", action="store_true", help="强制删除过期数据")
    parser.add_argument("--report-only", action="store_true", help="仅生成报告")
    
    args = parser.parse_args()
    
    manager = DataRetentionManager(args.config)
    
    if args.report_only:
        manager.generate_retention_report()
    else:
        manager.run_retention_job(dry_run=args.dry_run, force_delete=args.force)

if __name__ == "__main__":
    main() 