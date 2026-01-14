"""
Telegram Bot Handlers.
Business logic for processing messages and commands.

BDD Reference: NLE-A-11
"""
from typing import Optional
from src.services.yagpt_service import YaGPTService, ParsedExpense
from src.services.elevenlabs_service import ElevenLabsService
from src.services.expense_storage import ExpenseStorage, Expense


class BotHandlers:
    """Telegram bot message handlers"""

    def __init__(self, use_memory_db: bool = True):
        self.yagpt = YaGPTService()
        self.elevenlabs = ElevenLabsService()
        self.storage = ExpenseStorage(use_memory=use_memory_db)

    async def handle_start(self, user_id: int) -> str:
        """Handle /start command"""
        return (
            "👋 Привет! Я бот для учёта расходов.\n\n"
            "📝 *Как записать расход:*\n"
            "Просто напиши что и сколько потратил:\n"
            "• `кофе 300` — запишу в категорию Еда\n"
            "• `такси 600` — запишу в Транспорт\n"
            "• `бар 5000` — запишу в Развлечения\n\n"
            "📊 *Как посмотреть статистику:*\n"
            "• `расходы` — отчёт за месяц\n"
            "• `кофе за месяц` — сколько потратил на кофе\n"
            "• `топ расходов` — топ категорий\n\n"
            "🎙 Можешь отправить голосовое сообщение!"
        )

    async def handle_help(self, user_id: int) -> str:
        """Handle /help command"""
        return (
            "📚 *Команды бота:*\n\n"
            "*Запись расходов:*\n"
            "• `кофе 300` — записать расход\n"
            "• 🎙 голосовое — записать голосом\n\n"
            "*Статистика:*\n"
            "• `расходы` — отчёт за месяц\n"
            "• `кофе за месяц` — траты на кофе\n"
            "• `топ расходов` — топ категорий\n\n"
            "*Пример:* `обед 500`"
        )

    async def handle_message(self, user_id: int, text: str) -> str:
        """Handle text message"""
        # Detect intent
        intent = self.yagpt.detect_intent(text)

        if intent.type == "report_monthly":
            return await self._handle_report(user_id)
        elif intent.type == "top_expenses":
            return await self._handle_top_expenses(user_id)
        elif intent.type == "item_total":
            return await self._handle_item_total(user_id, intent.item or text)
        else:
            return await self._handle_expense(user_id, text)

    async def handle_voice(self, user_id: int, audio_data: bytes) -> str:
        """Handle voice message"""
        # Transcribe audio
        result = self.elevenlabs.transcribe(audio_data)

        if not result.success:
            return self.elevenlabs.get_error_message()

        # Process as text message
        return await self.handle_message(user_id, result.text)

    async def _handle_expense(self, user_id: int, text: str) -> str:
        """Handle expense message"""
        # Parse expense
        parsed = self.yagpt.parse_expense(text)

        if not parsed:
            return (
                "🤔 Не понял, что записать.\n\n"
                "Напиши в формате: `кофе 300`\n"
                "Или отправь голосовое сообщение."
            )

        # Save expense
        expense = Expense(
            user_id=user_id,
            item=parsed.item,
            amount=parsed.amount,
            category=parsed.category
        )
        self.storage.save_expense(expense)

        # Generate confirmation
        return self.yagpt.generate_confirmation(parsed)

    async def _handle_report(self, user_id: int) -> str:
        """Handle monthly report request"""
        totals = self.storage.get_category_totals(user_id)
        total = self.storage.get_total(user_id)

        if not totals:
            return (
                "📊 Пока нет расходов за этот месяц.\n\n"
                "Напиши что-нибудь типа `кофе 300`"
            )

        return self.yagpt.generate_report(totals, total)

    async def _handle_top_expenses(self, user_id: int) -> str:
        """Handle top expenses request"""
        top = self.storage.get_top_categories(user_id)

        if not top:
            return "📊 Пока нет расходов за этот месяц."

        emoji_map = {
            "Еда": "🍕", "Транспорт": "🚕", "Развлечения": "🎉",
            "Подписки": "📱", "Здоровье": "💊", "Подарки": "🎁",
            "Образование": "📚", "Одежда": "👟", "Другое": "📝"
        }

        lines = ["🏆 *Топ расходов за месяц:*\n"]
        for i, (category, amount) in enumerate(top, 1):
            emoji = emoji_map.get(category, "📝")
            lines.append(f"{i}. {emoji} {category}: {amount:,}₽")

        return "\n".join(lines)

    async def _handle_item_total(self, user_id: int, item: str) -> str:
        """Handle item total request"""
        # Clean item name
        item_clean = item.replace("за месяц", "").replace("за неделю", "").strip()

        total = self.storage.get_item_total(user_id, item_clean)

        if total == 0:
            return f"🤷 Не нашёл расходов на «{item_clean}» за этот месяц."

        return f"☕ Ты потратил на *{item_clean}* — *{total:,}₽* за месяц"
