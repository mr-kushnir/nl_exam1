"""
YaGPT Service for expense parsing and response generation.
Uses Yandex GPT API for natural language processing.

BDD Reference: NLE-A-8
"""
import os
import re
import json
import httpx
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class ParsedExpense:
    """Parsed expense from user message"""
    item: str
    amount: int
    category: str


@dataclass
class Intent:
    """Detected user intent"""
    type: str  # add_expense, report_monthly, item_total, top_expenses
    item: Optional[str] = None


# Category keywords mapping
CATEGORY_KEYWORDS = {
    "Еда": ["кофе", "обед", "завтрак", "ужин", "еда", "продукты", "ресторан", "кафе", "пицца", "суши", "бургер"],
    "Транспорт": ["такси", "метро", "автобус", "бензин", "парковка", "каршеринг", "uber", "яндекс"],
    "Развлечения": ["бар", "кино", "театр", "концерт", "клуб", "игры", "netflix", "spotify"],
    "Подписки": ["подписка", "netflix", "spotify", "youtube", "icloud", "premium"],
    "Здоровье": ["аптека", "врач", "спортзал", "фитнес", "лекарства", "анализы"],
    "Подарки": ["подарок", "цветы", "сюрприз"],
    "Образование": ["курсы", "книги", "обучение", "учеба"],
    "Одежда": ["одежда", "обувь", "кроссовки", "джинсы", "куртка", "футболка"],
}


class YaGPTService:
    """YaGPT service for expense parsing and response generation"""

    def __init__(self):
        self.api_key = os.getenv("YC_TOKEN", "")
        self.folder_id = os.getenv("YC_FOLDER_ID", "")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"

    def _detect_category(self, item: str) -> str:
        """Detect category from item keywords"""
        item_lower = item.lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in item_lower:
                    return category
        return "Другое"

    def _parse_with_regex(self, message: str) -> Optional[ParsedExpense]:
        """Fallback regex parser for simple messages"""
        # Pattern: item amount[р]
        pattern = r"^(.+?)\s+(\d+)\s*р?$"
        match = re.match(pattern, message.strip(), re.IGNORECASE)
        if match:
            item = match.group(1).strip()
            amount = int(match.group(2))
            category = self._detect_category(item)
            return ParsedExpense(item=item, amount=amount, category=category)
        return None

    def _call_yagpt(self, prompt: str, system_prompt: str = "") -> str:
        """Call YaGPT API"""
        if not self.api_key or not self.folder_id:
            return ""

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "text": system_prompt})
        messages.append({"role": "user", "text": prompt})

        data = {
            "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
            "completionOptions": {
                "stream": False,
                "temperature": 0.3,
                "maxTokens": 200,
            },
            "messages": messages,
        }

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(self.api_url, headers=headers, json=data)
                response.raise_for_status()
                result = response.json()
                return result.get("result", {}).get("alternatives", [{}])[0].get("message", {}).get("text", "")
        except Exception as e:
            print(f"YaGPT API error: {e}")
            return ""

    def parse_expense(self, message: str) -> Optional[ParsedExpense]:
        """Parse expense from user message using YaGPT or fallback regex"""
        # Try regex first for simple messages
        result = self._parse_with_regex(message)
        if result:
            return result

        # For complex messages, try YaGPT
        system_prompt = """Ты парсер расходов. Извлеки из сообщения:
- item: что купили (без суммы)
- amount: сумма (число)
- category: категория (Еда, Транспорт, Развлечения, Подписки, Здоровье, Подарки, Образование, Одежда, Другое)

Ответь ТОЛЬКО в формате JSON: {"item": "...", "amount": 123, "category": "..."}"""

        response = self._call_yagpt(message, system_prompt)
        if response:
            try:
                # Extract JSON from response
                json_match = re.search(r'\{[^}]+\}', response)
                if json_match:
                    data = json.loads(json_match.group())
                    return ParsedExpense(
                        item=data.get("item", ""),
                        amount=int(data.get("amount", 0)),
                        category=data.get("category", "Другое"),
                    )
            except (json.JSONDecodeError, ValueError):
                pass

        return None

    def generate_confirmation(self, expense: ParsedExpense) -> str:
        """Generate confirmation response for saved expense"""
        system_prompt = """Ты дружелюбный бот учёта расходов.
Сгенерируй короткое подтверждение записи расхода.
Используй эмодзи. Будь кратким и позитивным."""

        prompt = f"Записан расход: {expense.item} на {expense.amount}р в категории {expense.category}"

        response = self._call_yagpt(prompt, system_prompt)
        if response:
            return response

        # Fallback response
        emoji_map = {
            "Еда": "🍕",
            "Транспорт": "🚕",
            "Развлечения": "🎉",
            "Подписки": "📱",
            "Здоровье": "💊",
            "Подарки": "🎁",
            "Образование": "📚",
            "Одежда": "👟",
            "Другое": "📝",
        }
        emoji = emoji_map.get(expense.category, "✅")
        return f"{emoji} Записал: {expense.item} — {expense.amount}₽ ({expense.category})"

    def detect_intent(self, message: str) -> Intent:
        """Detect user intent from message"""
        message_lower = message.lower().strip()

        # Check for report commands
        if message_lower in ["расходы", "отчет", "отчёт", "статистика"]:
            return Intent(type="report_monthly")

        if message_lower in ["топ расходов", "топ", "топ трат"]:
            return Intent(type="top_expenses")

        # Check for item query (item + "за месяц")
        if "за месяц" in message_lower or "за неделю" in message_lower:
            item = message_lower.replace("за месяц", "").replace("за неделю", "").strip()
            return Intent(type="item_total", item=item)

        # Default: assume it's an expense
        return Intent(type="add_expense")

    def generate_report(self, category_totals: dict, total: int) -> str:
        """Generate monthly report response"""
        system_prompt = """Ты дружелюбный бот учёта расходов.
Сформируй красивый отчёт о расходах за месяц.
Используй эмодзи для каждой категории.
Добавь ироничный комментарий о тратах."""

        prompt = f"Расходы за месяц: {json.dumps(category_totals, ensure_ascii=False)}. Итого: {total}₽"

        response = self._call_yagpt(prompt, system_prompt)
        if response:
            return response

        # Fallback report
        lines = ["📊 *Расходы за месяц:*\n"]
        emoji_map = {"Еда": "🍕", "Транспорт": "🚕", "Развлечения": "🎉", "Подписки": "📱",
                     "Здоровье": "💊", "Подарки": "🎁", "Образование": "📚", "Одежда": "👟", "Другое": "📝"}

        for category, amount in sorted(category_totals.items(), key=lambda x: -x[1]):
            emoji = emoji_map.get(category, "📝")
            lines.append(f"{emoji} {category}: {amount:,}₽")

        lines.append(f"\n💰 *Итого: {total:,}₽*")
        return "\n".join(lines)
