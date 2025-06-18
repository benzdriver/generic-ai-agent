"""
主程序入口：提供统一的调用接口
"""

import logging
import time

from dependency_injector.wiring import Provide, inject
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.app.agent.response_router import generate_response
from src.app.user.user_manager import UserManager
from src.containers import Container
from src.infrastructure.audit import get_compliance_logger
from src.infrastructure.config.env_manager import get_config
from src.infrastructure.llm.base import BaseLLM
from src.infrastructure.vector_store.base import BaseVectorStore

# 初始化配置
config = get_config()
# 初始化合规日志记录器
audit_logger = get_compliance_logger()

# 设置日志
logging.basicConfig(
    level=config.logging.level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"{config.logging.dir}/app.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

# 优化后的欢迎信息
WELCOME_NEW = """
👋 您好！我是Thinkforward AI移民咨询的AI助手小思

我可以帮您解答关于加拿大移民的各种问题：
• 移民项目介绍和要求
• 申请流程和时间线
• 政策解读和注意事项
• 个人情况评估建议

💡 直接问我问题就可以，比如：
"Express Entry需要什么条件？"
"我在BC省工作，可以申请PNP吗？"

🏢 关于我们：
Thinkforward AI移民咨询 | 加拿大IRCC持牌顾问
CEO Yansi He：10+年法律事务所咨询经验
专业、可靠、值得信赖

📞 需要人工咨询请联系：contact@thinkforward.ai
"""

WELCOME_RETURNING = """
👋 欢迎回来！

我记得您之前咨询过移民相关问题。有什么新的问题需要我帮助解答吗？

💡 您可以继续询问任何加拿大移民相关的问题，我会根据您的情况提供个性化建议。

📞 如需深度咨询，欢迎联系我们的持牌顾问：contact@thinkforward.ai
"""


@inject
async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    user_manager: UserManager = Provide[Container.user_manager],
):
    """处理 /start 命令"""
    user_id = str(update.effective_user.id)
    user_first_name = update.effective_user.first_name or ""

    logger.info(f"New user started: {user_id}")

    # 检查是否是新用户
    user_profile = user_manager.get_user_profile(user_id)

    if user_profile is None:
        # 新用户
        user_manager.create_user_profile(
            user_id=user_id, platform="telegram", first_name=user_first_name
        )
        welcome_msg = WELCOME_NEW
        if user_first_name:
            welcome_msg = f"👋 {user_first_name}，" + welcome_msg[4:]  # 个性化问候
    else:
        # 老用户
        user_manager.update_user_profile(user_id)  # 更新最后互动时间
        welcome_msg = WELCOME_RETURNING
        if user_profile.first_name:
            welcome_msg = (
                f"👋 {user_profile.first_name}，欢迎回来！\n\n"
                + WELCOME_RETURNING.split("\n\n", 1)[1]
            )

    await update.message.reply_text(welcome_msg)


@inject
async def handle_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    llm: BaseLLM = Provide[Container.llm],
    vector_store: BaseVectorStore = Provide[Container.vector_store],
    user_manager: UserManager = Provide[Container.user_manager],
):
    """处理用户消息"""
    user_id = str(update.effective_user.id)
    user_input = update.message.text.strip()
    user_first_name = update.effective_user.first_name or ""
    start_time = time.time()

    # 更新用户档案
    user_profile = user_manager.get_user_profile(user_id)
    if user_profile is None:
        # 创建新用户档案
        user_manager.create_user_profile(
            user_id=user_id, platform="telegram", first_name=user_first_name
        )
    else:
        # 更新现有用户的互动信息
        user_manager.update_user_profile(user_id, first_name=user_first_name)

    # 合规日志：记录用户消息
    audit_logger.log_user_message(user_id, user_input, "telegram")

    # 传统日志：不记录消息内容，只记录元数据
    logger.info(f"Processing message from user {user_id}, length: {len(user_input)}")

    try:
        # 获取用户摘要信息
        user_summary = user_manager.get_user_summary(user_id)
        logger.info(f"User context: {user_summary}")

        response = generate_response(
            user_input, llm=llm, vector_store=vector_store, user_id=user_id
        )

        processing_time = (time.time() - start_time) * 1000  # 转换为毫秒

        # 为回答添加个性化元素
        if user_profile and user_profile.first_name and len(response) > 200:
            # 只对长回答添加个性化问候
            response = (
                f"{response}\n\n💬 {user_profile.first_name}，如有其他问题随时询问！"
            )

        # 发送回复
        await update.message.reply_text(response)

        # 合规日志：记录机器人响应
        audit_logger.log_bot_response(
            user_id, response, processing_time, len(response)
        )

        # 传统日志：只记录成功信息
        logger.info(
            f"Response sent to user {user_id}, processing time: {processing_time:.1f}ms"
        )

    except Exception as e:
        error_msg = (
            "抱歉，处理您的问题时出现了错误。请稍后再试，或联系我们的客服：contact@thinkforward.ai"
        )
        await update.message.reply_text(error_msg)

        # 合规日志：记录错误
        audit_logger.log_error(user_id, type(e).__name__, str(e))

        # 传统日志：记录错误
        logger.error(
            f"Error processing message from {user_id}: {str(e)}", exc_info=True
        )


def main():
    """主程序入口"""
    try:
        logger.info("Starting Telegram bot...")

        # 初始化并连接DI容器
        container = Container()
        container.wire(modules=[__name__])

        app = ApplicationBuilder().token(config.telegram.token).build()

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
