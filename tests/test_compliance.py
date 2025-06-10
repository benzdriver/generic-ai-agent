#!/usr/bin/env python3
"""
合规性测试脚本
测试PII检测、数据分类、审计日志等合规功能
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime
from src.infrastructure.audit import PIIDetector, ComplianceLogger, DataClassification, AuditEventType

class TestPIIDetector:
    """PII检测器测试"""
    
    def test_sin_canada_detection(self):
        """测试加拿大SIN检测"""
        text = "我的SIN是123-456-789"
        detected = PIIDetector.detect_pii(text)
        assert 'sin_canada' in detected
    
    def test_ssn_usa_detection(self):
        """测试美国SSN检测"""
        text = "My SSN is 123-45-6789"
        detected = PIIDetector.detect_pii(text)
        assert 'ssn_usa' in detected
    
    def test_phone_detection(self):
        """测试电话号码检测"""
        text = "Call me at (416) 123-4567"
        detected = PIIDetector.detect_pii(text)
        assert 'phone' in detected
    
    def test_email_detection(self):
        """测试邮箱检测"""
        text = "Email me at john.doe@example.com"
        detected = PIIDetector.detect_pii(text)
        assert 'email' in detected
    
    def test_postal_code_canada_detection(self):
        """测试加拿大邮编检测"""
        text = "I live in M5V 3A8"
        detected = PIIDetector.detect_pii(text)
        assert 'postal_code_ca' in detected
    
    def test_zip_code_usa_detection(self):
        """测试美国ZIP码检测"""
        text = "My ZIP is 90210"
        detected = PIIDetector.detect_pii(text)
        assert 'zip_code_usa' in detected
    
    def test_credit_card_detection(self):
        """测试信用卡号检测"""
        text = "My card number is 1234 5678 9012 3456"
        detected = PIIDetector.detect_pii(text)
        assert 'credit_card' in detected
    
    def test_passport_detection(self):
        """测试护照号检测"""
        text = "Passport: AB1234567"
        detected = PIIDetector.detect_pii(text)
        assert 'passport' in detected
    
    def test_pii_masking(self):
        """测试PII遮蔽"""
        text = "My email is john@example.com and phone is (416) 123-4567"
        masked = PIIDetector.mask_pii(text)
        assert 'EMAIL_MASKED' in masked
        assert 'PHONE_MASKED' in masked
        assert 'john@example.com' not in masked
        assert '(416) 123-4567' not in masked
    
    def test_no_pii_detection(self):
        """测试无PII文本"""
        text = "Hello, how are you today?"
        detected = PIIDetector.detect_pii(text)
        assert len(detected) == 0

class TestComplianceLogger:
    """合规日志记录器测试"""
    
    @pytest.fixture
    def temp_logger(self):
        """创建临时日志记录器"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ComplianceLogger(log_dir=temp_dir)
            yield logger, temp_dir
    
    def test_user_message_logging_without_pii(self, temp_logger):
        """测试无PII用户消息记录"""
        logger, temp_dir = temp_logger
        
        user_id = "test_user_123"
        message = "Hello, I need help with immigration"
        
        logger.log_user_message(user_id, message)
        
        # 检查审计日志
        audit_log = Path(temp_dir) / "audit.jsonl"
        assert audit_log.exists()
        
        with open(audit_log, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['event_type'] == 'user_message'
        assert log_entry['has_pii'] is False
        assert log_entry['message_masked'] == message
        assert log_entry['data_classification'] == 'internal'
    
    def test_user_message_logging_with_pii(self, temp_logger):
        """测试包含PII的用户消息记录"""
        logger, temp_dir = temp_logger
        
        user_id = "test_user_123"
        message = "My email is john@example.com and SIN is 123-456-789"
        
        logger.log_user_message(user_id, message)
        
        # 检查审计日志
        audit_log = Path(temp_dir) / "audit.jsonl"
        assert audit_log.exists()
        
        with open(audit_log, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['event_type'] == 'user_message'
        assert log_entry['has_pii'] is True
        assert 'email' in log_entry['pii_types']
        assert 'sin_canada' in log_entry['pii_types']
        assert log_entry['data_classification'] == 'confidential'
        assert 'EMAIL_MASKED' in log_entry['message_masked']
        assert 'SIN_CANADA_MASKED' in log_entry['message_masked']
        
        # 检查PII日志
        pii_log = Path(temp_dir) / "pii_access.jsonl"
        assert pii_log.exists()
        
        with open(pii_log, 'r', encoding='utf-8') as f:
            pii_entry = json.loads(f.readline())
        
        assert pii_entry['message_original'] == message
        assert pii_entry['access_reason'] == 'compliance_audit'
        assert 'retention_until' in pii_entry
    
    def test_bot_response_logging(self, temp_logger):
        """测试机器人响应记录"""
        logger, temp_dir = temp_logger
        
        user_id = "test_user_123"
        response = "Here is information about immigration processes"
        processing_time = 1500.5
        tokens_used = 150
        
        logger.log_bot_response(user_id, response, processing_time, tokens_used)
        
        # 检查审计日志
        audit_log = Path(temp_dir) / "audit.jsonl"
        assert audit_log.exists()
        
        with open(audit_log, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['event_type'] == 'bot_response'
        assert log_entry['processing_time_ms'] == processing_time
        assert log_entry['tokens_used'] == tokens_used
        assert log_entry['response_length'] == len(response)
    
    def test_error_logging(self, temp_logger):
        """测试错误记录"""
        logger, temp_dir = temp_logger
        
        user_id = "test_user_123"
        error_type = "ValidationError"
        error_message = "Invalid input format"
        
        logger.log_error(user_id, error_type, error_message)
        
        # 检查系统日志
        system_log = Path(temp_dir) / "system.jsonl"
        assert system_log.exists()
        
        with open(system_log, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['event_type'] == 'error_occurred'
        assert log_entry['error_type'] == error_type
        assert log_entry['error_message'] == error_message
    
    def test_system_event_logging(self, temp_logger):
        """测试系统事件记录"""
        logger, temp_dir = temp_logger
        
        description = "System startup"
        additional_data = {"version": "1.0.0", "environment": "test"}
        
        logger.log_system_event(description, additional_data)
        
        # 检查系统日志
        system_log = Path(temp_dir) / "system.jsonl"
        assert system_log.exists()
        
        with open(system_log, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        assert log_entry['event_type'] == 'system_event'
        assert log_entry['description'] == description
        assert log_entry['additional_data'] == additional_data
    
    def test_user_id_hashing(self, temp_logger):
        """测试用户ID哈希处理"""
        logger, temp_dir = temp_logger
        
        user_id = "test_user_123"
        message = "Test message"
        
        logger.log_user_message(user_id, message)
        
        audit_log = Path(temp_dir) / "audit.jsonl"
        with open(audit_log, 'r', encoding='utf-8') as f:
            log_entry = json.loads(f.readline())
        
        # 用户ID应该被哈希处理
        assert log_entry['user_hash'] != user_id
        assert len(log_entry['user_hash']) == 16  # SHA256[:16]
    
    def test_compliance_report_generation(self, temp_logger):
        """测试合规报告生成"""
        logger, temp_dir = temp_logger
        
        start_date = datetime(2024, 1, 1)
        end_date = datetime(2024, 12, 31)
        
        report = logger.generate_compliance_report(start_date, end_date)
        
        assert 'report_id' in report
        assert 'period' in report
        assert 'summary' in report
        assert 'retention_policy' in report
        assert report['period']['start'] == start_date.isoformat() + 'Z'
        assert report['period']['end'] == end_date.isoformat() + 'Z'

class TestComplianceIntegration:
    """合规性集成测试"""
    
    def test_full_conversation_flow(self):
        """测试完整对话流程的合规性"""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ComplianceLogger(log_dir=temp_dir)
            
            user_id = "integration_test_user"
            
            # 1. 用户发送包含PII的消息
            user_message = "Hi, my name is John Doe, email: john@example.com, phone: (416) 123-4567"
            logger.log_user_message(user_id, user_message)
            
            # 2. 机器人响应
            bot_response = "Hello John, I can help you with immigration. Please provide more details."
            logger.log_bot_response(user_id, bot_response, 1200.0, 80)
            
            # 3. 检查生成的日志
            audit_log = Path(temp_dir) / "audit.jsonl"
            pii_log = Path(temp_dir) / "pii_access.jsonl"
            
            assert audit_log.exists()
            assert pii_log.exists()
            
            # 检查审计日志内容
            with open(audit_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                assert len(lines) == 2  # 用户消息 + 机器人响应
                
                user_log = json.loads(lines[0])
                bot_log = json.loads(lines[1])
                
                # 用户消息日志
                assert user_log['has_pii'] is True
                assert 'email' in user_log['pii_types']
                assert 'phone' in user_log['pii_types']
                assert user_log['data_classification'] == 'confidential'
                
                # 机器人响应日志
                assert bot_log['event_type'] == 'bot_response'
                assert bot_log['response_length'] == len(bot_response)
            
            # 检查PII日志
            with open(pii_log, 'r', encoding='utf-8') as f:
                pii_entry = json.loads(f.readline())
                assert pii_entry['message_original'] == user_message
                assert pii_entry['access_reason'] == 'compliance_audit'

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 