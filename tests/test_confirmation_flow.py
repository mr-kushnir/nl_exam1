"""
Tests for Expense Confirmation Flow
BDD Reference: NLE-A-15
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.bot.handlers import BotHandlers


class TestExpenseConfirmationFlow:
    """Feature: Expense Confirmation Flow"""

    @pytest.fixture
    def handlers(self):
        return BotHandlers(use_memory_db=True)

    @pytest.mark.asyncio
    async def test_show_confirmation_after_expense_input(self, handlers):
        """Scenario: Show confirmation after expense input
        Given user sends message "кофе 300"
        When YaGPT parses the expense
        Then bot can create pending expense with confirmation request
        """
        user_id = 12345

        # Using the new confirmation flow
        result = await handlers.create_pending_expense(
            user_id=user_id,
            item="кофе",
            amount=300,
            category="Еда"
        )

        # Should return a confirmation request
        assert result["success"] is True
        assert "кофе" in result["message"] or result["item"] == "кофе"
        assert "300" in result["message"] or result["amount"] == 300
        assert "подтвердите" in result["message"].lower() or "верно" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_confirm_expense_saves_to_database(self, handlers):
        """Scenario: Confirm expense saves to database
        Given user sees confirmation with pending expense
        When user confirms with callback
        Then expense is saved to database
        """
        user_id = 12345

        # First create pending expense
        pending_result = await handlers.create_pending_expense(
            user_id=user_id,
            item="кофе",
            amount=300,
            category="Еда"
        )

        # Then confirm it
        result = await handlers.confirm_expense(user_id, pending_result["expense_id"])

        assert result["success"] is True
        assert "записано" in result["message"].lower()

        # Verify expense is saved
        expenses = handlers.storage.get_expenses(user_id)
        assert len(expenses) == 1
        assert expenses[0].item == "кофе"
        assert expenses[0].amount == 300

    @pytest.mark.asyncio
    async def test_cancel_expense_discards_data(self, handlers):
        """Scenario: Cancel expense discards data
        Given user sees confirmation with pending expense
        When user clicks cancel
        Then expense is NOT saved
        """
        user_id = 12345

        # Create pending expense
        pending_result = await handlers.create_pending_expense(
            user_id=user_id,
            item="кофе",
            amount=300,
            category="Еда"
        )

        # Cancel it
        result = await handlers.cancel_expense(user_id, pending_result["expense_id"])

        assert result["success"] is True
        assert "отменено" in result["message"].lower()

        # Verify expense is NOT saved
        expenses = handlers.storage.get_expenses(user_id)
        assert len(expenses) == 0

    @pytest.mark.asyncio
    async def test_edit_opens_category_selection(self, handlers):
        """Scenario: Edit opens category selection
        Given user sees confirmation with pending expense
        When user clicks edit
        Then bot returns category options
        """
        user_id = 12345

        # Create pending expense
        pending_result = await handlers.create_pending_expense(
            user_id=user_id,
            item="кофе",
            amount=300,
            category="Еда"
        )

        # Request edit
        result = await handlers.edit_expense_category(user_id, pending_result["expense_id"])

        assert result["success"] is True
        assert "categories" in result
        assert len(result["categories"]) > 0
        assert "Еда" in result["categories"]
        assert "Транспорт" in result["categories"]

    @pytest.mark.asyncio
    async def test_update_category_and_save(self, handlers):
        """Scenario: User selects new category and confirms
        Given user is editing expense category
        When user selects new category
        Then expense is updated and saved
        """
        user_id = 12345

        # Create pending expense
        pending_result = await handlers.create_pending_expense(
            user_id=user_id,
            item="кофе",
            amount=300,
            category="Еда"
        )

        # Update category
        result = await handlers.update_expense_category(
            user_id,
            pending_result["expense_id"],
            "Развлечения"
        )

        assert result["success"] is True

        # Confirm after category update
        confirm_result = await handlers.confirm_expense(user_id, pending_result["expense_id"])

        # Verify saved with new category
        expenses = handlers.storage.get_expenses(user_id)
        assert len(expenses) == 1
        assert expenses[0].category == "Развлечения"
