"""
主程序入口：提供统一的调用接口
"""

import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
from config.env_manager import init_config
from agent_core.response_router import generate_response

# 初始化配置
config = init_config()

# 设置日志目录并初始化日志配置
log_dir = config['logging'].get('dir')
if log_dir:
    os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=config['logging']['level'],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"{log_dir}/app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

WELCOME = """
你好，我是智能移民问答助手。
请直接输入你的问题，例如：
"我在BC省工签满一年了，可以走PNP吗？"
"Express Entry 最低分是多少？"
"配偶担保在境内结婚可以吗？"
"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理 /start 命令"""
    logger.info(f"New user started: {update.effective_user.id}")
    await update.message.reply_text(WELCOME)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """处理用户消息"""
    user_id = update.effective_user.id
    user_input = update.message.text.strip()
    
    logger.info(f"Received message from {user_id}: {user_input}")
    
    try:
        response = generate_response(user_input)
        await update.message.reply_text(response)
        logger.info(f"Response sent to {user_id}")
    except Exception as e:
        error_msg = "抱歉，处理您的问题时出现了错误。请稍后再试。"
        await update.message.reply_text(error_msg)
        logger.error(f"Error processing message from {user_id}: {str(e)}", exc_info=True)

def main():
    """主程序入口"""
    try:
        logger.info("Starting Telegram bot...")
        app = ApplicationBuilder().token(config['telegram']['token']).build()
        
        # 添加处理器
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        logger.info("✅ Telegram bot is running...")
        app.run_polling()
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
