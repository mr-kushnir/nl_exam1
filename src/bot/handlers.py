"""
Telegram Bot Handlers.
Business logic for processing messages and commands.

BDD Reference: NLE-A-11, NLE-A-15 (Confirmation Flow)
"""
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from src.services.yagpt_service import YaGPTService, ParsedExpense, CATEGORY_KEYWORDS
from src.services.speech_service import SpeechService
from src.services.expense_storage import ExpenseStorage, Expense


# Available categories for selection
CATEGORIES = ["Еда", "Транспорт", "Развлечения", "Подписки", "Здоровье", "Подарки", "Образование", "Одежда", "Другое"]


class BotHandlers:
    """Telegram bot message handlers"""

    def __init__(self, use_memory_db: bool = True):
        self.yagpt = YaGPTService()
        self.speech = SpeechService()
        self.storage = ExpenseStorage(use_memory=use_memory_db)
        # Pending expenses awaiting confirmation (user_id -> {expense_id: PendingExpense})
        self._pending_expenses: Dict[int, Dict[str, dict]] = {}

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
        # Transcribe audio using Yandex SpeechKit
        result = self.speech.transcribe(audio_data)

        if not result.success:
            return self.speech.get_error_message()

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

    # ═══════════════════════════════════════════════════════════
    # Expense Confirmation Flow (NLE-A-15)
    # ═══════════════════════════════════════════════════════════

    async def create_pending_expense(
        self,
        user_id: int,
        item: str,
        amount: int,
        category: str
    ) -> Dict[str, Any]:
        """Create a pending expense awaiting confirmation"""
        expense_id = str(uuid.uuid4())[:8]

        pending = {
            "expense_id": expense_id,
            "item": item,
            "amount": amount,
            "category": category,
            "created_at": datetime.now().isoformat(),
        }

        if user_id not in self._pending_expenses:
            self._pending_expenses[user_id] = {}
        self._pending_expenses[user_id][expense_id] = pending

        return {
            "success": True,
            "expense_id": expense_id,
            "item": item,
            "amount": amount,
            "category": category,
            "message": f"📝 *Подтвердите расход:*\n\n"
                       f"• Что: {item}\n"
                       f"• Сумма: {amount}₽\n"
                       f"• Категория: {category}\n\n"
                       f"Всё верно?",
        }

    async def confirm_expense(self, user_id: int, expense_id: str) -> Dict[str, Any]:
        """Confirm and save pending expense"""
        if user_id not in self._pending_expenses:
            return {"success": False, "message": "Нет ожидающих подтверждения расходов"}

        if expense_id not in self._pending_expenses[user_id]:
            return {"success": False, "message": "Расход не найден или истёк"}

        pending = self._pending_expenses[user_id].pop(expense_id)

        # Save to database
        expense = Expense(
            user_id=user_id,
            item=pending["item"],
            amount=pending["amount"],
            category=pending["category"],
        )
        self.storage.save_expense(expense)

        emoji_map = {
            "Еда": "🍕", "Транспорт": "🚕", "Развлечения": "🎉",
            "Подписки": "📱", "Здоровье": "💊", "Подарки": "🎁",
            "Образование": "📚", "Одежда": "👟", "Другое": "📝"
        }
        emoji = emoji_map.get(pending["category"], "✅")

        return {
            "success": True,
            "message": f"{emoji} Записано: {pending['item']} — {pending['amount']}₽ ({pending['category']})",
        }

    async def cancel_expense(self, user_id: int, expense_id: str) -> Dict[str, Any]:
        """Cancel pending expense"""
        if user_id not in self._pending_expenses:
            return {"success": False, "message": "Нет ожидающих подтверждения расходов"}

        if expense_id not in self._pending_expenses[user_id]:
            return {"success": False, "message": "Расход не найден или истёк"}

        self._pending_expenses[user_id].pop(expense_id)

        return {
            "success": True,
            "message": "❌ Отменено",
        }

    async def edit_expense_category(self, user_id: int, expense_id: str) -> Dict[str, Any]:
        """Get category options for editing expense"""
        if user_id not in self._pending_expenses:
            return {"success": False, "message": "Нет ожидающих подтверждения расходов"}

        if expense_id not in self._pending_expenses[user_id]:
            return {"success": False, "message": "Расход не найден или истёк"}

        return {
            "success": True,
            "categories": CATEGORIES,
            "message": "Выберите категорию:",
        }

    async def update_expense_category(
        self,
        user_id: int,
        expense_id: str,
        new_category: str
    ) -> Dict[str, Any]:
        """Update category for pending expense"""
        if user_id not in self._pending_expenses:
            return {"success": False, "message": "Нет ожидающих подтверждения расходов"}

        if expense_id not in self._pending_expenses[user_id]:
            return {"success": False, "message": "Расход не найден или истёк"}

        if new_category not in CATEGORIES:
            return {"success": False, "message": f"Неизвестная категория: {new_category}"}

        self._pending_expenses[user_id][expense_id]["category"] = new_category

        return {
            "success": True,
            "message": f"Категория изменена на: {new_category}",
        }

    def get_pending_expense(self, user_id: int, expense_id: str) -> Optional[dict]:
        """Get pending expense by ID"""
        if user_id not in self._pending_expenses:
            return None
        return self._pending_expenses[user_id].get(expense_id)
