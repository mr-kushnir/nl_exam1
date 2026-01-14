"""
Telegram Keyboard Generators.
Creates Reply and Inline keyboards for the bot.

BDD Reference: NLE-A-16
"""
try:
    from telegram import (
        ReplyKeyboardMarkup,
        InlineKeyboardMarkup,
        InlineKeyboardButton,
        KeyboardButton,
    )
    HAS_TELEGRAM = True
except ImportError:
    # Mock classes for testing without telegram package
    HAS_TELEGRAM = False

    class KeyboardButton:
        def __init__(self, text):
            self.text = text

    class InlineKeyboardButton:
        def __init__(self, text, callback_data=None):
            self.text = text
            self.callback_data = callback_data

    class ReplyKeyboardMarkup:
        def __init__(self, keyboard, resize_keyboard=False, one_time_keyboard=False):
            self.keyboard = keyboard
            self.resize_keyboard = resize_keyboard
            self.one_time_keyboard = one_time_keyboard

    class InlineKeyboardMarkup:
        def __init__(self, inline_keyboard):
            self.inline_keyboard = inline_keyboard

# Main menu button labels
MAIN_MENU_BUTTONS = [
    ["📊 Отчёт", "📈 Статистика"],
    ["🏆 Топ", "📅 Сегодня"],
    ["💰 Бюджет", "📤 Экспорт"],
]


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Create main menu Reply keyboard"""
    keyboard = [
        [KeyboardButton(text=btn) for btn in row]
        for row in MAIN_MENU_BUTTONS
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_confirmation_keyboard(expense_id: str) -> InlineKeyboardMarkup:
    """Create confirmation Inline keyboard for pending expense"""
    buttons = [
        [
            InlineKeyboardButton("✅ Верно", callback_data=f"confirm:{expense_id}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"cancel:{expense_id}"),
        ],
        [
            InlineKeyboardButton("✏️ Изменить категорию", callback_data=f"edit:{expense_id}"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def get_category_keyboard(expense_id: str) -> InlineKeyboardMarkup:
    """Create category selection Inline keyboard"""
    from src.bot.handlers import CATEGORIES

    # Arrange categories in 3 columns
    buttons = []
    row = []
    for i, category in enumerate(CATEGORIES):
        row.append(InlineKeyboardButton(category, callback_data=f"cat:{expense_id}:{category}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    # Add cancel button
    buttons.append([InlineKeyboardButton("❌ Отмена", callback_data=f"cancel:{expense_id}")])

    return InlineKeyboardMarkup(buttons)


def get_expense_actions_keyboard(expense_id: str) -> InlineKeyboardMarkup:
    """Create Inline keyboard for saved expense actions"""
    buttons = [
        [
            InlineKeyboardButton("🗑 Удалить", callback_data=f"delete:{expense_id}"),
            InlineKeyboardButton("📁 Категория", callback_data=f"change_cat:{expense_id}"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)


def get_budget_keyboard() -> InlineKeyboardMarkup:
    """Create budget setting Inline keyboard"""
    presets = ["30000", "50000", "70000", "100000"]
    buttons = [
        [InlineKeyboardButton(f"{int(p)//1000}к ₽", callback_data=f"budget:{p}") for p in presets],
        [InlineKeyboardButton("Другая сумма", callback_data="budget:custom")],
    ]
    return InlineKeyboardMarkup(buttons)


def get_export_period_keyboard() -> InlineKeyboardMarkup:
    """Create export period selection keyboard"""
    buttons = [
        [
            InlineKeyboardButton("Этот месяц", callback_data="export:month"),
            InlineKeyboardButton("Прошлый месяц", callback_data="export:prev_month"),
        ],
        [
            InlineKeyboardButton("Этот год", callback_data="export:year"),
            InlineKeyboardButton("Всё время", callback_data="export:all"),
        ],
    ]
    return InlineKeyboardMarkup(buttons)
