"""
Telegram Bot Handlers.
Business logic for processing messages and commands.

BDD Reference: NLE-A-11, NLE-A-15 (Confirmation Flow)
"""
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from src.services.yagpt_service import YaGPTService, ParsedExpense, CATEGORY_KEYWORDS, CATEGORIES
from src.services.speech_service import SpeechService
from src.services.expense_storage import ExpenseStorage, Expense


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
        """Handle expense message (supports multiple expenses)"""
        # Parse expenses (can be one or multiple)
        parsed_list = self.yagpt.parse_multiple_expenses(text)

        if not parsed_list:
            return (
                "🤔 Не понял, что записать.\n\n"
                "Напиши в формате: `кофе 300`\n"
                "Или отправь голосовое сообщение."
            )

        # Save all expenses
        for parsed in parsed_list:
            expense = Expense(
                user_id=user_id,
                item=parsed.item,
                amount=parsed.amount,
                category=parsed.category
            )
            self.storage.save_expense(expense)

        # Generate confirmation
        return self.yagpt.generate_multiple_confirmation(parsed_list)

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

    # ═══════════════════════════════════════════════════════════
    # Saved Expense Management (NLE-A-16)
    # ═══════════════════════════════════════════════════════════

    async def delete_expense(self, user_id: int, created_at: str) -> Dict[str, Any]:
        """Delete a saved expense by created_at timestamp"""
        expenses = self.storage.get_expenses(user_id)

        # Find expense with matching created_at
        target = None
        for exp in expenses:
            if exp.created_at.isoformat() == created_at:
                target = exp
                break

        if not target:
            return {"success": False, "message": "Расход не найден"}

        # Delete from storage
        success = self.storage.delete_expense(user_id, created_at)

        if success:
            return {
                "success": True,
                "message": f"🗑 Удалено: {target.item} — {target.amount}₽",
            }
        return {"success": False, "message": "Ошибка при удалении"}

    async def change_expense_category(
        self,
        user_id: int,
        created_at: str,
        new_category: str
    ) -> Dict[str, Any]:
        """Change category of a saved expense"""
        if new_category not in CATEGORIES:
            return {"success": False, "message": f"Неизвестная категория: {new_category}"}

        success = self.storage.update_expense_category(user_id, created_at, new_category)

        if success:
            return {
                "success": True,
                "message": f"📁 Категория изменена на: {new_category}",
            }
        return {"success": False, "message": "Расход не найден"}

    # ═══════════════════════════════════════════════════════════
    # Time-based Reports (NLE-A-17)
    # ═══════════════════════════════════════════════════════════

    async def handle_today(self, user_id: int) -> str:
        """Handle /today command - show today's expenses"""
        expenses = self.storage.get_today_expenses(user_id)

        if not expenses:
            return "📅 Сегодня расходов нет.\n\nНапиши что-нибудь типа `кофе 300`"

        lines = ["📅 *Расходы за сегодня:*\n"]
        total = 0

        emoji_map = {
            "Еда": "🍕", "Транспорт": "🚕", "Развлечения": "🎉",
            "Подписки": "📱", "Здоровье": "💊", "Подарки": "🎁",
            "Образование": "📚", "Одежда": "👟", "Другое": "📝"
        }

        for exp in expenses:
            emoji = emoji_map.get(exp.category, "📝")
            time_str = exp.created_at.strftime("%H:%M")
            lines.append(f"{emoji} {time_str} — {exp.item}: {exp.amount}₽")
            total += exp.amount

        lines.append(f"\n💰 *Итого: {total:,}₽*")
        return "\n".join(lines)

    async def handle_week(self, user_id: int) -> str:
        """Handle /week command - show weekly comparison"""
        this_week = self.storage.get_week_expenses(user_id, weeks_ago=0)
        last_week = self.storage.get_week_expenses(user_id, weeks_ago=1)

        this_week_total = sum(e.amount for e in this_week)
        last_week_total = sum(e.amount for e in last_week)

        lines = ["📊 *Расходы за неделю:*\n"]
        lines.append(f"Эта неделя: {this_week_total:,}₽")

        if last_week_total > 0:
            lines.append(f"Прошлая неделя: {last_week_total:,}₽")

            # Calculate percentage change
            if last_week_total != 0:
                change = ((this_week_total - last_week_total) / last_week_total) * 100

                if change > 0:
                    lines.append(f"\n📈 На {abs(change):.0f}% *больше* чем на прошлой неделе")
                elif change < 0:
                    lines.append(f"\n📉 На {abs(change):.0f}% *меньше* чем на прошлой неделе")
                else:
                    lines.append("\n➡️ Столько же, как на прошлой неделе")
        else:
            lines.append("\n_Данных за прошлую неделю нет_")

        return "\n".join(lines)

    # ═══════════════════════════════════════════════════════════
    # Budget Management (NLE-A-18)
    # ═══════════════════════════════════════════════════════════

    async def set_budget(self, user_id: int, amount: int) -> Dict[str, Any]:
        """Set monthly budget for user"""
        if amount <= 0:
            return {"success": False, "message": "Бюджет должен быть больше 0"}

        # Save budget to database
        self.storage.save_budget(user_id, amount)

        return {
            "success": True,
            "message": f"💰 Бюджет на месяц: {amount:,}₽\n\n"
                       f"Буду следить за расходами и предупреждать о превышении.",
        }

    def get_user_budget(self, user_id: int) -> Optional[int]:
        """Get user's budget from database"""
        return self.storage.get_budget(user_id)

    async def get_budget_status(self, user_id: int) -> Dict[str, Any]:
        """Get budget status with progress"""
        budget = self.get_user_budget(user_id)

        if not budget:
            return {
                "success": True,
                "message": "💰 Бюджет не установлен.\n\n"
                           "Установите бюджет: `/budget 50000`",
            }

        # Get current month total
        total_spent = self.storage.get_total(user_id)
        remaining = budget - total_spent
        percentage = min(100, (total_spent / budget) * 100)

        # Build progress bar
        bar_length = 10
        filled = int(bar_length * percentage / 100)
        bar = "█" * filled + "░" * (bar_length - filled)

        lines = ["💰 *Бюджет на месяц:*\n"]
        lines.append(f"[{bar}] {percentage:.0f}%\n")
        lines.append(f"Потрачено: {total_spent:,}₽ из {budget:,}₽")

        # Status messages based on percentage
        if percentage >= 100:
            overspent = total_spent - budget
            lines.append(f"\n🔴 *Бюджет превышен на {overspent:,}₽*")
        elif percentage >= 80:
            lines.append(f"\n⚠️ *Внимание!* Израсходовано {percentage:.0f}% бюджета")
            lines.append(f"Осталось: {remaining:,}₽")
        elif percentage >= 50:
            lines.append(f"\nОсталось: {remaining:,}₽")
        else:
            lines.append(f"\n✅ Осталось: {remaining:,}₽")

        return {
            "success": True,
            "message": "\n".join(lines),
            "percentage": percentage,
            "spent": total_spent,
            "budget": budget,
            "remaining": remaining,
        }

    async def check_budget_warning(self, user_id: int) -> Optional[str]:
        """Check if budget warning should be shown after adding expense"""
        budget = self.get_user_budget(user_id)
        if not budget:
            return None

        total = self.storage.get_total(user_id)
        percentage = (total / budget) * 100

        if percentage >= 100:
            overspent = total - budget
            return f"🔴 *Внимание!* Бюджет превышен на {overspent:,}₽"
        elif percentage >= 80:
            return f"⚠️ Израсходовано {percentage:.0f}% бюджета ({total:,}₽ из {budget:,}₽)"

        return None

    # ═══════════════════════════════════════════════════════════
    # Expense Management Commands (NLE-A-19)
    # ═══════════════════════════════════════════════════════════

    async def handle_undo(self, user_id: int) -> Dict[str, Any]:
        """Handle /undo command - delete last expense"""
        last_expense = self.storage.get_last_expense(user_id)

        if not last_expense:
            return {
                "success": False,
                "message": "🤷 Нечего отменять — расходов пока нет.",
            }

        # Delete the expense
        self.storage.delete_expense(user_id, last_expense.created_at.isoformat())

        return {
            "success": True,
            "message": f"↩️ Удалено: {last_expense.item} — {last_expense.amount}₽ ({last_expense.category})",
        }

    async def handle_export(self, user_id: int, period: str = "month") -> Dict[str, Any]:
        """Handle /export command - generate CSV export"""
        expenses = self.storage.get_monthly_expenses(user_id)

        if not expenses:
            return {
                "success": False,
                "message": "📤 Нет расходов для экспорта за этот период.",
            }

        # Generate CSV
        import io
        import csv

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(["Дата", "Время", "Название", "Сумма", "Категория"])

        # Data rows
        for exp in sorted(expenses, key=lambda e: e.created_at, reverse=True):
            writer.writerow([
                exp.created_at.strftime("%Y-%m-%d"),
                exp.created_at.strftime("%H:%M"),
                exp.item,
                exp.amount,
                exp.category,
            ])

        csv_data = output.getvalue()

        total = sum(e.amount for e in expenses)

        return {
            "success": True,
            "message": f"📤 Экспорт готов: {len(expenses)} записей, итого {total:,}₽",
            "csv_data": csv_data,
            "filename": f"expenses_{datetime.now().strftime('%Y%m')}.csv",
        }

    async def handle_find(self, user_id: int, query: str) -> Dict[str, Any]:
        """Handle /find command - search expenses"""
        expenses = self.storage.get_monthly_expenses(user_id)

        if not query:
            return {
                "success": False,
                "message": "🔍 Укажите что искать: `/find кофе`",
            }

        query_lower = query.lower()
        matches = [e for e in expenses if query_lower in e.item.lower()]

        if not matches:
            return {
                "success": True,
                "message": f"🔍 По запросу «{query}» ничего не найдено.",
            }

        total = sum(e.amount for e in matches)

        lines = [f"🔍 *Найдено по «{query}»:*\n"]

        for exp in matches[:10]:  # Limit to 10 results
            date_str = exp.created_at.strftime("%d.%m")
            lines.append(f"• {date_str}: {exp.item} — {exp.amount}₽")

        if len(matches) > 10:
            lines.append(f"\n_...и ещё {len(matches) - 10} записей_")

        lines.append(f"\n💰 *Итого: {total:,}₽* ({len(matches)} записей)")

        return {
            "success": True,
            "message": "\n".join(lines),
            "count": len(matches),
            "total": total,
        }

    # ═══════════════════════════════════════════════════════════
    # Analytics and Visualization (NLE-A-20)
    # ═══════════════════════════════════════════════════════════

    def generate_ascii_chart(self, user_id: int, max_bar_length: int = 15) -> str:
        """Generate ASCII bar chart for category totals"""
        totals = self.storage.get_category_totals(user_id)

        if not totals:
            return "📊 Нет данных для графика"

        # Find max value for scaling
        max_val = max(totals.values())
        if max_val == 0:
            return "📊 Нет данных для графика"

        emoji_map = {
            "Еда": "🍕", "Транспорт": "🚕", "Развлечения": "🎉",
            "Подписки": "📱", "Здоровье": "💊", "Подарки": "🎁",
            "Образование": "📚", "Одежда": "👟", "Другое": "📝"
        }

        lines = ["📊 *Распределение расходов:*\n"]

        # Sort by value descending
        sorted_totals = sorted(totals.items(), key=lambda x: -x[1])

        for category, amount in sorted_totals:
            # Calculate bar length
            bar_length = int((amount / max_val) * max_bar_length)
            bar = "█" * bar_length

            emoji = emoji_map.get(category, "📝")
            lines.append(f"{emoji} {category:<12} {bar} {amount:,}₽")

        return "\n".join(lines)

    async def handle_day_stats(self, user_id: int) -> Dict[str, Any]:
        """Handle day-of-week statistics command"""
        expenses = self.storage.get_monthly_expenses(user_id)

        if not expenses:
            return {
                "success": False,
                "message": "📊 Недостаточно данных для статистики по дням.",
            }

        # Group by day of week (0=Monday, 6=Sunday)
        day_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        day_totals = {i: 0 for i in range(7)}
        day_counts = {i: 0 for i in range(7)}

        for exp in expenses:
            dow = exp.created_at.weekday()
            day_totals[dow] += exp.amount
            day_counts[dow] += 1

        # Calculate averages
        day_averages = {}
        for dow in range(7):
            if day_counts[dow] > 0:
                day_averages[dow] = day_totals[dow] / day_counts[dow]
            else:
                day_averages[dow] = 0

        # Find max for scaling and peak day
        max_avg = max(day_averages.values()) if day_averages else 0
        peak_day = max(day_averages.keys(), key=lambda k: day_averages[k]) if day_averages else 0

        lines = ["📅 *Расходы по дням недели:*\n"]

        for dow in range(7):
            avg = day_averages.get(dow, 0)
            total = day_totals.get(dow, 0)

            # Bar length
            bar_length = int((avg / max_avg) * 10) if max_avg > 0 else 0
            bar = "█" * bar_length

            # Highlight peak day
            marker = " ▲ макс" if dow == peak_day and avg > 0 else ""

            lines.append(f"{day_names[dow]}: {bar:<10} {total:,}₽{marker}")

        # Summary
        if peak_day is not None:
            lines.append(f"\n📈 Больше всего тратишь в *{day_names[peak_day]}*")

        return {
            "success": True,
            "message": "\n".join(lines),
            "peak_day": day_names[peak_day] if peak_day is not None else None,
            "day_totals": {day_names[k]: v for k, v in day_totals.items()},
        }
