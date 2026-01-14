"""
Telegram Bot Main Entry Point.
Expense tracker bot with YaGPT and Yandex SpeechKit integration.

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
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from dotenv import load_dotenv

from src.bot.handlers import BotHandlers
from src.bot.keyboards import (
    get_main_menu_keyboard,
    get_confirmation_keyboard,
    get_category_keyboard,
    get_expense_actions_keyboard,
)

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


# ═══════════════════════════════════════════════════════════
# Command Handlers
# ═══════════════════════════════════════════════════════════

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - show welcome and main menu"""
    user_id = update.effective_user.id
    response = await bot_handlers.handle_start(user_id)
    await update.message.reply_text(
        response,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    user_id = update.effective_user.id
    response = await bot_handlers.handle_help(user_id)
    await update.message.reply_text(response, parse_mode="Markdown")


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /today command - show today's expenses"""
    user_id = update.effective_user.id
    response = await bot_handlers.handle_today(user_id)
    await update.message.reply_text(response, parse_mode="Markdown")


async def week_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /week command - show weekly comparison"""
    user_id = update.effective_user.id
    response = await bot_handlers.handle_week(user_id)
    await update.message.reply_text(response, parse_mode="Markdown")


async def budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /budget command - show or set budget"""
    user_id = update.effective_user.id
    args = context.args

    if args and args[0].isdigit():
        # Set budget
        amount = int(args[0])
        result = await bot_handlers.set_budget(user_id, amount)
        await update.message.reply_text(result["message"], parse_mode="Markdown")
    else:
        # Show budget status
        result = await bot_handlers.get_budget_status(user_id)
        await update.message.reply_text(result["message"], parse_mode="Markdown")


async def undo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /undo command - delete last expense"""
    user_id = update.effective_user.id
    result = await bot_handlers.handle_undo(user_id)
    await update.message.reply_text(result["message"], parse_mode="Markdown")


async def export_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /export command - export expenses to CSV"""
    user_id = update.effective_user.id
    result = await bot_handlers.handle_export(user_id)

    if result["success"]:
        # Send CSV file
        from io import BytesIO
        csv_bytes = result["csv_data"].encode("utf-8")
        await update.message.reply_document(
            document=BytesIO(csv_bytes),
            filename=result["filename"],
            caption=result["message"]
        )
    else:
        await update.message.reply_text(result["message"], parse_mode="Markdown")


async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /find command - search expenses"""
    user_id = update.effective_user.id
    query = " ".join(context.args) if context.args else ""
    result = await bot_handlers.handle_find(user_id, query)
    await update.message.reply_text(result["message"], parse_mode="Markdown")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - show day-of-week statistics"""
    user_id = update.effective_user.id
    result = await bot_handlers.handle_day_stats(user_id)
    await update.message.reply_text(result["message"], parse_mode="Markdown")


# ═══════════════════════════════════════════════════════════
# Message Handlers
# ═══════════════════════════════════════════════════════════

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages"""
    user_id = update.effective_user.id
    text = update.message.text

    # Handle menu button presses
    if text == "📊 Отчёт":
        response = await bot_handlers._handle_report(user_id)
        await update.message.reply_text(response, parse_mode="Markdown")
        return
    elif text == "📈 Статистика":
        result = await bot_handlers.handle_day_stats(user_id)
        await update.message.reply_text(result["message"], parse_mode="Markdown")
        return
    elif text == "🏆 Топ":
        response = await bot_handlers._handle_top_expenses(user_id)
        await update.message.reply_text(response, parse_mode="Markdown")
        return
    elif text == "📅 Сегодня":
        response = await bot_handlers.handle_today(user_id)
        await update.message.reply_text(response, parse_mode="Markdown")
        return
    elif text == "💰 Бюджет":
        result = await bot_handlers.get_budget_status(user_id)
        await update.message.reply_text(result["message"], parse_mode="Markdown")
        return
    elif text == "📤 Экспорт":
        result = await bot_handlers.handle_export(user_id)
        if result["success"]:
            from io import BytesIO
            csv_bytes = result["csv_data"].encode("utf-8")
            await update.message.reply_document(
                document=BytesIO(csv_bytes),
                filename=result["filename"],
                caption=result["message"]
            )
        else:
            await update.message.reply_text(result["message"], parse_mode="Markdown")
        return

    # Check if it's an expense message
    intent = bot_handlers.yagpt.detect_intent(text)

    if intent.type == "add_expense":
        # Parse expense and ask for confirmation
        parsed = bot_handlers.yagpt.parse_expense(text)
        if parsed:
            result = await bot_handlers.create_pending_expense(
                user_id, parsed.item, parsed.amount, parsed.category
            )
            await update.message.reply_text(
                result["message"],
                parse_mode="Markdown",
                reply_markup=get_confirmation_keyboard(result["expense_id"])
            )
        else:
            await update.message.reply_text(
                "🤔 Не понял, что записать.\n\nНапиши в формате: `кофе 300`",
                parse_mode="Markdown"
            )
    else:
        # Handle other intents
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

    # Transcribe
    result = bot_handlers.speech.transcribe(bytes(audio_bytes))

    if not result.success:
        await update.message.reply_text(
            bot_handlers.speech.get_error_message(),
            parse_mode="Markdown"
        )
        return

    # Show transcription and ask for confirmation
    text = result.text
    parsed = bot_handlers.yagpt.parse_expense(text)

    if parsed:
        pending = await bot_handlers.create_pending_expense(
            user_id, parsed.item, parsed.amount, parsed.category
        )
        await update.message.reply_text(
            f"🎙 Распознано: _{text}_\n\n{pending['message']}",
            parse_mode="Markdown",
            reply_markup=get_confirmation_keyboard(pending["expense_id"])
        )
    else:
        # Try to process as command
        response = await bot_handlers.handle_message(user_id, text)
        await update.message.reply_text(
            f"🎙 Распознано: _{text}_\n\n{response}",
            parse_mode="Markdown"
        )


# ═══════════════════════════════════════════════════════════
# Callback Query Handlers (Inline Buttons)
# ═══════════════════════════════════════════════════════════

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if data.startswith("confirm:"):
        expense_id = data.split(":")[1]
        result = await bot_handlers.confirm_expense(user_id, expense_id)

        # Check budget warning
        warning = await bot_handlers.check_budget_warning(user_id)
        message = result["message"]
        if warning:
            message += f"\n\n{warning}"

        await query.edit_message_text(message, parse_mode="Markdown")

    elif data.startswith("cancel:"):
        expense_id = data.split(":")[1]
        result = await bot_handlers.cancel_expense(user_id, expense_id)
        await query.edit_message_text(result["message"], parse_mode="Markdown")

    elif data.startswith("edit:"):
        expense_id = data.split(":")[1]
        result = await bot_handlers.edit_expense_category(user_id, expense_id)
        if result["success"]:
            await query.edit_message_text(
                "Выберите категорию:",
                reply_markup=get_category_keyboard(expense_id)
            )
        else:
            await query.edit_message_text(result["message"], parse_mode="Markdown")

    elif data.startswith("cat:"):
        parts = data.split(":")
        expense_id = parts[1]
        category = parts[2]
        await bot_handlers.update_expense_category(user_id, expense_id, category)
        result = await bot_handlers.confirm_expense(user_id, expense_id)
        await query.edit_message_text(result["message"], parse_mode="Markdown")

    elif data.startswith("delete:"):
        expense_id = data.split(":")[1]
        result = await bot_handlers.delete_expense(user_id, expense_id)
        await query.edit_message_text(result["message"], parse_mode="Markdown")

    elif data.startswith("change_cat:"):
        expense_id = data.split(":")[1]
        await query.edit_message_text(
            "Выберите новую категорию:",
            reply_markup=get_category_keyboard(expense_id)
        )


# ═══════════════════════════════════════════════════════════
# Application Setup
# ═══════════════════════════════════════════════════════════

def create_ptb_application() -> Application:
    """Create and configure the python-telegram-bot Application"""
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN not set in environment")

    application = Application.builder().token(token).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("today", today_command))
    application.add_handler(CommandHandler("week", week_command))
    application.add_handler(CommandHandler("budget", budget_command))
    application.add_handler(CommandHandler("undo", undo_command))
    application.add_handler(CommandHandler("export", export_command))
    application.add_handler(CommandHandler("find", find_command))
    application.add_handler(CommandHandler("stats", stats_command))

    # Callback query handler (inline buttons)
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Message handlers
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
    return {"status": "ok", "bot": "nlexam expense tracker v3"}


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
