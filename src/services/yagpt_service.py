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


# Available categories
CATEGORIES = [
    "Еда", "Транспорт", "Развлечения", "Подписки",
    "Здоровье", "Подарки", "Образование", "Одежда",
    "Переводы", "Дом", "Связь", "Другое"
]

CATEGORY_KEYWORDS = {
    "Еда": ["кофе", "обед", "завтрак", "ужин", "еда", "продукты", "ресторан", "кафе", "пицца", "суши", "бургер", "магазин", "пятерочка", "перекресток", "вкусвилл"],
    "Транспорт": ["такси", "метро", "автобус", "бензин", "парковка", "каршеринг", "uber", "яндекс", "болт", "ситимобил"],
    "Развлечения": ["бар", "кино", "театр", "концерт", "клуб", "игры", "netflix", "spotify", "пиво", "вино"],
    "Подписки": ["подписка", "netflix", "spotify", "youtube", "icloud", "premium", "плюс", "музыка"],
    "Здоровье": ["аптека", "врач", "спортзал", "фитнес", "лекарства", "анализы", "стоматолог", "массаж"],
    "Подарки": ["подарок", "цветы", "сюрприз", "букет"],
    "Образование": ["курсы", "книги", "обучение", "учеба", "репетитор"],
    "Одежда": ["одежда", "обувь", "кроссовки", "джинсы", "куртка", "футболка", "zara", "hm"],
    "Переводы": ["перевод", "маме", "папе", "другу", "отправил", "скинул", "долг"],
    "Дом": ["квартира", "аренда", "ремонт", "мебель", "икеа", "леруа"],
    "Связь": ["телефон", "интернет", "мтс", "билайн", "мегафон", "теле2"],
}


class YaGPTService:
    """YaGPT service for expense parsing using LLM"""

    def __init__(self):
        self.oauth_token = os.getenv("YC_TOKEN", "")
        self.folder_id = os.getenv("YC_FOLDER_ID", "")
        self.api_url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
        self._iam_token = None
        self._iam_token_expires = 0

    def _get_iam_token(self) -> str:
        """Get IAM token from OAuth token"""
        import time

        # Check if we have a valid cached token
        if self._iam_token and time.time() < self._iam_token_expires:
            return self._iam_token

        if not self.oauth_token:
            return ""

        try:
            with httpx.Client(timeout=10) as client:
                response = client.post(
                    "https://iam.api.cloud.yandex.net/iam/v1/tokens",
                    json={"yandexPassportOauthToken": self.oauth_token}
                )
                response.raise_for_status()
                data = response.json()
                self._iam_token = data.get("iamToken", "")
                # Token valid for 12 hours, refresh after 11
                self._iam_token_expires = time.time() + 11 * 3600
                return self._iam_token
        except Exception as e:
            print(f"IAM token error: {e}")
            return ""

    def _call_yagpt(self, prompt: str, system_prompt: str = "") -> str:
        """Call YaGPT API"""
        iam_token = self._get_iam_token()
        if not iam_token or not self.folder_id:
            return ""

        headers = {
            "Authorization": f"Bearer {iam_token}",
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
                "temperature": 0.1,
                "maxTokens": 150,
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

    def _detect_category(self, item: str) -> str:
        """Detect category from item keywords (fallback)"""
        item_lower = item.lower()
        for category, keywords in CATEGORY_KEYWORDS.items():
            for keyword in keywords:
                if keyword in item_lower:
                    return category
        return "Другое"

    def _looks_like_expense(self, message: str) -> bool:
        """Check if message could possibly be an expense (has numbers or number words)"""
        text = message.lower()

        # Check for digits
        if re.search(r'\d+', text):
            return True

        # Check for number words
        number_words = [
            "тысяч", "тыщ", "сотн", "сотк", "рубл", "руб",
            "полтин", "косар", "штук", "кусок",
            "сто", "двести", "триста", "четыреста", "пятьсот",
            "шестьсот", "семьсот", "восемьсот", "девятьсот",
            "тысяча", "тысячу", "тыща", "тыщу",
            "один", "два", "три", "четыре", "пять",
            "шесть", "семь", "восемь", "девять", "десять",
        ]
        for word in number_words:
            if word in text:
                return True

        return False

    def parse_expense(self, message: str) -> Optional[ParsedExpense]:
        """Parse expense from user message using YaGPT"""

        # Pre-filter: if no numbers or number words, don't even try
        if not self._looks_like_expense(message):
            return None

        system_prompt = f"""Ты парсер расходов. Твоя задача - извлечь из сообщения пользователя информацию о расходе.

Извлеки:
1. item - на что потрачено (краткое описание, 1-3 слова)
2. amount - сумма в рублях (целое число)
3. category - категория из списка: {', '.join(CATEGORIES)}

Правила:
- Если сумма указана словами (тыща, сотка, пятихатка), преобразуй в число
- тыща/тысяча/штука/косарь = 1000
- сотка/сотня = 100
- полтинник/полтос = 50
- пятихатка = 500
- Если категория неясна, используй "Другое"
- Если это не расход или сумма не указана, верни null

Отвечай ТОЛЬКО валидным JSON без пояснений:
{{"item": "описание", "amount": число, "category": "категория"}}
или null если это не расход."""

        response = self._call_yagpt(message, system_prompt)

        if response:
            try:
                # Clean response - remove markdown code blocks if present
                response = response.strip()
                response = re.sub(r'^```json\s*', '', response)
                response = re.sub(r'\s*```$', '', response)
                response = response.strip()

                if response.lower() == "null":
                    return None

                # Extract JSON from response
                json_match = re.search(r'\{[^}]+\}', response)
                if json_match:
                    data = json.loads(json_match.group())
                    item = data.get("item", "")
                    amount = int(data.get("amount", 0))
                    category = data.get("category", "Другое")

                    if item and amount > 0:
                        # Validate category
                        if category not in CATEGORIES:
                            category = self._detect_category(item)
                        return ParsedExpense(item=item, amount=amount, category=category)
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"Parse error: {e}, response: {response}")

        # Fallback: simple regex for "item amount" or "amount item"
        return self._simple_parse(message)

    def _simple_parse(self, message: str) -> Optional[ParsedExpense]:
        """Simple fallback parser for basic formats"""
        text = message.strip()

        # Pattern: item amount (кофе 300)
        match = re.match(r'^(.+?)\s+(\d+)\s*р?$', text, re.IGNORECASE)
        if match:
            item = match.group(1).strip()
            amount = int(match.group(2))
            if amount > 0:
                return ParsedExpense(item=item, amount=amount, category=self._detect_category(item))

        # Pattern: amount item (300 кофе)
        match = re.match(r'^(\d+)\s*р?\s+(.+)$', text, re.IGNORECASE)
        if match:
            amount = int(match.group(1))
            item = match.group(2).strip()
            if amount > 0:
                return ParsedExpense(item=item, amount=amount, category=self._detect_category(item))

        return None

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

    def generate_confirmation(self, expense: ParsedExpense) -> str:
        """Generate confirmation response for saved expense"""
        emoji_map = {
            "Еда": "🍕", "Транспорт": "🚕", "Развлечения": "🎉",
            "Подписки": "📱", "Здоровье": "💊", "Подарки": "🎁",
            "Образование": "📚", "Одежда": "👟", "Переводы": "💸",
            "Дом": "🏠", "Связь": "📞", "Другое": "📝"
        }
        emoji = emoji_map.get(expense.category, "✅")
        return f"{emoji} Записал: {expense.item} — {expense.amount}₽ ({expense.category})"

    def generate_report(self, category_totals: dict, total: int) -> str:
        """Generate monthly report response"""
        emoji_map = {
            "Еда": "🍕", "Транспорт": "🚕", "Развлечения": "🎉",
            "Подписки": "📱", "Здоровье": "💊", "Подарки": "🎁",
            "Образование": "📚", "Одежда": "👟", "Переводы": "💸",
            "Дом": "🏠", "Связь": "📞", "Другое": "📝"
        }

        lines = ["📊 *Расходы за месяц:*\n"]

        for category, amount in sorted(category_totals.items(), key=lambda x: -x[1]):
            emoji = emoji_map.get(category, "📝")
            lines.append(f"{emoji} {category}: {amount:,}₽")

        lines.append(f"\n💰 *Итого: {total:,}₽*")
        return "\n".join(lines)
