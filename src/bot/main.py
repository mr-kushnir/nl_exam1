"""
Telegram Bot Main Entry Point.
Expense tracker bot with YaGPT and ElevenLabs integration.

Supports both webhook mode (for production) and polling mode (for local dev).
"""
import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
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

# Telegram application (initialized later)
ptb_app: Application = None


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


def create_ptb_application() -> Application:
    """Create and configure the python-telegram-bot Application"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN not set in environment")

    application = Application.builder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    return application


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan handler - initialize and cleanup PTB"""
    global ptb_app
    ptb_app = create_ptb_application()
    await ptb_app.initialize()
    await ptb_app.start()
    logger.info("Bot started in webhook mode")
    yield
    await ptb_app.stop()
    await ptb_app.shutdown()
    logger.info("Bot stopped")


# FastAPI app for webhook mode
app = FastAPI(lifespan=lifespan)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "bot": "nlexam expense tracker"}


@app.get("/health")
async def health():
    """Health check for container orchestration"""
    return {"status": "healthy"}


@app.post("/webhook")
async def webhook(request: Request) -> Response:
    """Handle incoming Telegram webhook updates"""
    try:
        data = await request.json()
        update = Update.de_json(data, ptb_app.bot)
        await ptb_app.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return Response(status_code=200)  # Always return 200 to avoid retries


def main():
    """Start the bot in polling mode (for local development)"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN not set in environment")
        return

    application = create_ptb_application()

    logger.info("Starting expense tracker bot in polling mode...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
