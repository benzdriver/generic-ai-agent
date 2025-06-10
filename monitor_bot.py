#!/usr/bin/env python3
"""
Telegram Bot 实时监控脚本
"""

import time
import re
from pathlib import Path

def monitor_logs():
    """实时监控日志文件"""
    log_file = Path("logs/app.log")
    
    if not log_file.exists():
        print("❌ 日志文件不存在: logs/app.log")
        return
    
    print("🔍 开始监控 Telegram Bot 消息...")
    print("按 Ctrl+C 停止监控")
    print("-" * 60)
    
    # 移动到文件末尾
    with open(log_file, 'r', encoding='utf-8') as f:
        f.seek(0, 2)  # 移到文件末尾
        
        try:
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)
                    continue
                
                # 检查是否是用户消息
                if "Received message from" in line:
                    # 解析用户ID和消息内容
                    match = re.search(r'Received message from (\d+): (.+)', line)
                    if match:
                        user_id = match.group(1)
                        message = match.group(2)
                        timestamp = line.split(' - ')[0]
                        
                        print(f"📱 [{timestamp}] 用户 {user_id}: {message}")
                
                # 检查是否是回复发送
                elif "Response sent to" in line:
                    match = re.search(r'Response sent to (\d+)', line)
                    if match:
                        user_id = match.group(1)
                        timestamp = line.split(' - ')[0]
                        print(f"✅ [{timestamp}] 已回复用户 {user_id}")
                
                # 检查是否有错误
                elif "Error processing message" in line:
                    print(f"❌ [{line.split(' - ')[0]}] 处理消息时出错")
        
        except KeyboardInterrupt:
            print("\n👋 停止监控")

if __name__ == "__main__":
    monitor_logs() 