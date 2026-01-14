"""
Tests for Main Menu and Keyboards
BDD Reference: NLE-A-16
"""
import pytest
from src.bot.handlers import BotHandlers, CATEGORIES
from src.bot.keyboards import (
    get_main_menu_keyboard,
    get_confirmation_keyboard,
    get_category_keyboard,
    get_expense_actions_keyboard,
    MAIN_MENU_BUTTONS,
)


class TestMainMenuKeyboards:
    """Feature: Main Menu and Keyboards"""

    def test_main_menu_keyboard_structure(self):
        """Scenario: Main menu has correct buttons"""
        keyboard = get_main_menu_keyboard()

        # Should have buttons arranged in rows
        assert keyboard is not None
        assert hasattr(keyboard, 'keyboard')

        # Flatten all buttons
        all_buttons = []
        for row in keyboard.keyboard:
            for btn in row:
                all_buttons.append(btn.text)

        # Check for expected buttons
        assert "📊 Отчёт" in all_buttons
        assert "📅 Сегодня" in all_buttons

    def test_confirmation_keyboard_has_buttons(self):
        """Scenario: Confirmation keyboard has confirm/cancel/edit"""
        expense_id = "abc123"
        keyboard = get_confirmation_keyboard(expense_id)

        assert keyboard is not None
        assert hasattr(keyboard, 'inline_keyboard')

        # Flatten callback data
        all_callbacks = []
        for row in keyboard.inline_keyboard:
            for btn in row:
                all_callbacks.append(btn.callback_data)

        assert f"confirm:{expense_id}" in all_callbacks
        assert f"cancel:{expense_id}" in all_callbacks
        assert f"edit:{expense_id}" in all_callbacks

    def test_category_keyboard_has_all_categories(self):
        """Scenario: Category keyboard shows all categories"""
        expense_id = "abc123"
        keyboard = get_category_keyboard(expense_id)

        assert keyboard is not None

        # Flatten button texts
        all_texts = []
        for row in keyboard.inline_keyboard:
            for btn in row:
                all_texts.append(btn.text)

        # Check that categories are present
        for category in CATEGORIES:
            assert category in all_texts

    def test_expense_actions_keyboard(self):
        """Scenario: Saved expense has delete and category change buttons"""
        expense_id = "abc123"
        keyboard = get_expense_actions_keyboard(expense_id)

        assert keyboard is not None

        # Flatten callbacks
        all_callbacks = []
        for row in keyboard.inline_keyboard:
            for btn in row:
                all_callbacks.append(btn.callback_data)

        assert f"delete:{expense_id}" in all_callbacks
        assert f"change_cat:{expense_id}" in all_callbacks


class TestHandlersWithKeyboards:
    """Test handlers return correct keyboard types"""

    @pytest.fixture
    def handlers(self):
        return BotHandlers(use_memory_db=True)

    @pytest.mark.asyncio
    async def test_start_returns_keyboard_data(self, handlers):
        """Scenario: /start should indicate main menu should be shown"""
        user_id = 12345
        result = await handlers.handle_start(user_id)

        # Result is text, keyboard is handled by main.py
        assert isinstance(result, str)
        assert "привет" in result.lower()

    @pytest.mark.asyncio
    async def test_delete_saved_expense(self, handlers):
        """Scenario: Delete expense via callback"""
        user_id = 12345

        # First create and confirm expense
        pending = await handlers.create_pending_expense(user_id, "кофе", 300, "Еда")
        await handlers.confirm_expense(user_id, pending["expense_id"])

        # Verify expense exists
        expenses = handlers.storage.get_expenses(user_id)
        assert len(expenses) == 1

        # Delete it
        result = await handlers.delete_expense(user_id, expenses[0].created_at.isoformat())

        assert result["success"] is True
        assert "удалено" in result["message"].lower()

        # Verify expense is gone
        expenses = handlers.storage.get_expenses(user_id)
        assert len(expenses) == 0

    @pytest.mark.asyncio
    async def test_change_saved_expense_category(self, handlers):
        """Scenario: Change category of saved expense"""
        user_id = 12345

        # First create and confirm expense
        pending = await handlers.create_pending_expense(user_id, "кофе", 300, "Еда")
        await handlers.confirm_expense(user_id, pending["expense_id"])

        # Get expense
        expenses = handlers.storage.get_expenses(user_id)
        assert expenses[0].category == "Еда"

        # Change category
        result = await handlers.change_expense_category(
            user_id,
            expenses[0].created_at.isoformat(),
            "Развлечения"
        )

        assert result["success"] is True

        # Verify category changed
        expenses = handlers.storage.get_expenses(user_id)
        assert expenses[0].category == "Развлечения"
