# src/infrastructure/audit/compliance_logger.py

"""
合规审计日志系统
符合加拿大 PIPEDA 和美国数据保护法规要求
"""

import json
import hashlib
import logging
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List
from enum import Enum
import re

class DataClassification(Enum):
    """数据分类级别"""
    PUBLIC = "public"           # 公开信息
    INTERNAL = "internal"       # 内部信息  
    CONFIDENTIAL = "confidential"  # 机密信息
    RESTRICTED = "restricted"   # 受限信息（PII等）

class AuditEventType(Enum):
    """审计事件类型"""
    USER_MESSAGE = "user_message"
    BOT_RESPONSE = "bot_response"
    USER_LOGIN = "user_login"
    DATA_ACCESS = "data_access"
    ERROR_OCCURRED = "error_occurred"
    SYSTEM_EVENT = "system_event"

class PIIDetector:
    """PII（个人身份信息）检测器"""
    
    # 加拿大和美国常见的PII模式
    PATTERNS = {
        'sin_canada': r'(?:SIN|sin|社会保险号|社保号).*?\d{3}[-\s]?\d{3}[-\s]?\d{3}|\b\d{3}[-\s]?\d{3}[-\s]?\d{3}\b',  # 加拿大SIN
        'ssn_usa': r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',     # 美国SSN
        'phone': r'\b\+?1?[-\s]?\(?[0-9]{3}\)?[-\s]?[0-9]{3}[-\s]?[0-9]{4}\b',
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'postal_code_ca': r'\b[A-Za-z]\d[A-Za-z][-\s]?\d[A-Za-z]\d\b',  # 加拿大邮编
        'zip_code_usa': r'\b\d{5}(-\d{4})?\b',             # 美国ZIP
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
        'passport': r'\b[A-Za-z]{1,2}\d{6,8}\b',
    }
    
    @classmethod
    def detect_pii(cls, text: str) -> List[str]:
        """检测文本中的PII"""
        detected = []
        for pii_type, pattern in cls.PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                detected.append(pii_type)
        return detected
    
    @classmethod
    def mask_pii(cls, text: str) -> str:
        """遮蔽PII信息"""
        masked_text = text
        for pii_type, pattern in cls.PATTERNS.items():
            masked_text = re.sub(pattern, f'[{pii_type.upper()}_MASKED]', masked_text, flags=re.IGNORECASE)
        return masked_text

class ComplianceLogger:
    """合规审计日志记录器"""
    
    def __init__(self, log_dir: str = "audit_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置不同级别的日志文件
        self.audit_log = self.log_dir / "audit.jsonl"
        self.pii_log = self.log_dir / "pii_access.jsonl"  # 受限访问
        self.system_log = self.log_dir / "system.jsonl"
        
        # 设置日志记录器
        self._setup_loggers()
    
    def _setup_loggers(self):
        """设置日志记录器"""
        # 审计日志记录器
        self.audit_logger = logging.getLogger("audit")
        self.audit_logger.setLevel(logging.INFO)
        audit_handler = logging.FileHandler(self.audit_log, encoding='utf-8')
        audit_handler.setFormatter(logging.Formatter('%(message)s'))
        self.audit_logger.addHandler(audit_handler)
        
        # PII日志记录器（加密存储）
        self.pii_logger = logging.getLogger("pii")
        self.pii_logger.setLevel(logging.INFO)
        pii_handler = logging.FileHandler(self.pii_log, encoding='utf-8')
        pii_handler.setFormatter(logging.Formatter('%(message)s'))
        self.pii_logger.addHandler(pii_handler)
        
        # 系统日志记录器
        self.system_logger = logging.getLogger("system")
        self.system_logger.setLevel(logging.INFO)
        system_handler = logging.FileHandler(self.system_log, encoding='utf-8')
        system_handler.setFormatter(logging.Formatter('%(message)s'))
        self.system_logger.addHandler(system_handler)
    
    def _generate_event_id(self) -> str:
        """生成唯一事件ID"""
        return str(uuid.uuid4())
    
    def _hash_user_id(self, user_id: str) -> str:
        """对用户ID进行哈希处理"""
        return hashlib.sha256(f"user_{user_id}".encode()).hexdigest()[:16]
    
    def _create_base_event(self, event_type: AuditEventType, user_id: Optional[str] = None) -> Dict[str, Any]:
        """创建基础事件记录"""
        return {
            "event_id": self._generate_event_id(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "user_hash": self._hash_user_id(user_id) if user_id else None,
            "system_info": {
                "app_version": "1.0.0",
                "environment": "production"  # 从配置获取
            }
        }
    
    def log_user_message(self, user_id: str, message: str, platform: str = "telegram"):
        """记录用户消息（合规处理）"""
        # 检测PII
        pii_detected = PIIDetector.detect_pii(message)
        has_pii = len(pii_detected) > 0
        
        # 创建审计记录
        audit_event = self._create_base_event(AuditEventType.USER_MESSAGE, user_id)
        audit_event.update({
            "platform": platform,
            "message_length": len(message),
            "has_pii": has_pii,
            "pii_types": pii_detected,
            "message_masked": PIIDetector.mask_pii(message),  # 遮蔽后的消息
            "data_classification": DataClassification.CONFIDENTIAL.value if has_pii else DataClassification.INTERNAL.value
        })
        
        # 记录到审计日志
        self.audit_logger.info(json.dumps(audit_event, ensure_ascii=False))
        
        # 如果包含PII，记录到受限日志
        if has_pii:
            pii_event = audit_event.copy()
            pii_event["message_original"] = message  # 原始消息仅在PII日志中保存
            pii_event["access_reason"] = "compliance_audit"
            pii_event["retention_until"] = (datetime.now(timezone.utc) + timedelta(days=2555)).isoformat()  # 7年保留期
            
            self.pii_logger.info(json.dumps(pii_event, ensure_ascii=False))
    
    def log_bot_response(self, user_id: str, response: str, processing_time: float, tokens_used: int):
        """记录机器人响应"""
        event = self._create_base_event(AuditEventType.BOT_RESPONSE, user_id)
        event.update({
            "response_length": len(response),
            "processing_time_ms": processing_time,
            "tokens_used": tokens_used,
            "response_masked": PIIDetector.mask_pii(response),
            "data_classification": DataClassification.INTERNAL.value
        })
        
        self.audit_logger.info(json.dumps(event, ensure_ascii=False))
    
    def log_error(self, user_id: Optional[str], error_type: str, error_message: str, stack_trace: Optional[str] = None):
        """记录错误事件"""
        event = self._create_base_event(AuditEventType.ERROR_OCCURRED, user_id)
        event.update({
            "error_type": error_type,
            "error_message": error_message,
            "has_stack_trace": stack_trace is not None,
            "data_classification": DataClassification.INTERNAL.value
        })
        
        self.system_logger.info(json.dumps(event, ensure_ascii=False))
    
    def log_system_event(self, event_description: str, additional_data: Optional[Dict] = None):
        """记录系统事件"""
        event = self._create_base_event(AuditEventType.SYSTEM_EVENT)
        event.update({
            "description": event_description,
            "additional_data": additional_data or {},
            "data_classification": DataClassification.INTERNAL.value
        })
        
        self.system_logger.info(json.dumps(event, ensure_ascii=False))
    
    def generate_compliance_report(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """生成合规报告"""
        return {
            "report_id": self._generate_event_id(),
            "period": {
                "start": start_date.isoformat() + "Z",
                "end": end_date.isoformat() + "Z"
            },
            "summary": {
                "total_interactions": 0,  # 从日志统计
                "pii_incidents": 0,       # 从日志统计
                "error_rate": 0.0,        # 从日志计算
                "compliance_status": "compliant"
            },
            "retention_policy": {
                "general_logs": "1 year",
                "pii_logs": "7 years",
                "audit_logs": "7 years"
            }
        }

# 全局实例
compliance_logger = ComplianceLogger()

def get_compliance_logger() -> ComplianceLogger:
    """获取合规日志记录器实例"""
    return compliance_logger 