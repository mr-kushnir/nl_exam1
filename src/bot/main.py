"""
Telegram Bot Main Entry Point.
Expense tracker bot with YaGPT and ElevenLabs integration.
"""
import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv

from src.bot.handlers import BotHandlers

load_dotenv()

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize handlers
bot_handlers = BotHandlers(use_memory_db=False)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user_id = update.effective_user.id
    response = await bot_handlers.handle_start(user_id)
    await update.message.reply_text(response, parse_mode="Markdown")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user_id = update.effective_user.id
    response = await bot_handlers.handle_help(user_id)
    await update.message.reply_text(response, parse_mode="Markdown")


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_id = update.effective_user.id
    text = update.message.text

    response = await bot_handlers.handle_message(user_id, text)
    await update.message.reply_text(response, parse_mode="Markdown")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice messages"""
    user_id = update.effective_user.id

    # Download voice file
    voice = update.message.voice
    file = await context.bot.get_file(voice.file_id)

    # Get audio data
    audio_bytes = await file.download_as_bytearray()

    response = await bot_handlers.handle_voice(user_id, bytes(audio_bytes))
    await update.message.reply_text(response, parse_mode="Markdown")


def main():
    """Start the bot"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN not set in environment")
        return

    # Create application
    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    # Start polling
    logger.info("Starting expense tracker bot...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
