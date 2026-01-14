"""
Tests for Budget Management
BDD Reference: NLE-A-18
"""
import pytest
from datetime import datetime, timedelta
from src.bot.handlers import BotHandlers
from src.services.expense_storage import Expense


class TestBudgetManagement:
    """Feature: Monthly Budget Management"""

    @pytest.fixture
    def handlers(self):
        return BotHandlers(use_memory_db=True)

    def _add_expense(self, handlers, user_id, item, amount, category):
        """Helper to add expense"""
        expense = Expense(
            user_id=user_id,
            item=item,
            amount=amount,
            category=category,
            created_at=datetime.now()
        )
        handlers.storage.save_expense(expense)

    @pytest.mark.asyncio
    async def test_set_monthly_budget(self, handlers):
        """Scenario: Set monthly budget
        Given user sends /budget 50000
        When command is processed
        Then budget is saved and confirmed
        """
        user_id = 12345

        result = await handlers.set_budget(user_id, 50000)

        assert result["success"] is True
        assert "50" in result["message"]  # 50,000 or 50000
        assert "бюджет" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_show_budget_progress(self, handlers):
        """Scenario: Show budget progress
        Given user has budget 50000
        And current month expenses total 30000
        When user sends /budget
        Then bot shows progress with percentage
        """
        user_id = 12345

        # Set budget
        await handlers.set_budget(user_id, 50000)

        # Add expenses
        self._add_expense(handlers, user_id, "еда", 30000, "Еда")

        result = await handlers.get_budget_status(user_id)

        assert "30" in result["message"]  # 30,000 spent
        assert "50" in result["message"]  # 50,000 budget
        assert "60" in result["message"] or "%" in result["message"]  # 60%

    @pytest.mark.asyncio
    async def test_budget_warning_at_80_percent(self, handlers):
        """Scenario: Budget warning at 80%
        Given user has budget 50000
        And current month expenses total 40000
        When checking budget
        Then warning is shown
        """
        user_id = 12345

        await handlers.set_budget(user_id, 50000)
        self._add_expense(handlers, user_id, "еда", 40000, "Еда")

        result = await handlers.get_budget_status(user_id)

        # Should show warning (80% spent)
        assert "80" in result["message"] or "⚠" in result["message"] or "внимание" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_budget_exceeded(self, handlers):
        """Scenario: Budget exceeded
        Given user has budget 50000
        And current month expenses total 52000
        When user sends /budget
        Then bot shows exceeded message
        """
        user_id = 12345

        await handlers.set_budget(user_id, 50000)
        self._add_expense(handlers, user_id, "еда", 52000, "Еда")

        result = await handlers.get_budget_status(user_id)

        # Should show exceeded
        assert "превышен" in result["message"].lower() or "🔴" in result["message"]

    @pytest.mark.asyncio
    async def test_no_budget_set(self, handlers):
        """Scenario: No budget configured
        Given user has not set a budget
        When user sends /budget
        Then bot prompts to set budget
        """
        user_id = 12345

        result = await handlers.get_budget_status(user_id)

        assert "не установлен" in result["message"].lower() or "установить" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_budget_progress_bar(self, handlers):
        """Scenario: Visual progress bar
        Given user has budget and expenses
        When showing status
        Then progress bar is included
        """
        user_id = 12345

        await handlers.set_budget(user_id, 10000)
        self._add_expense(handlers, user_id, "еда", 5000, "Еда")

        result = await handlers.get_budget_status(user_id)

        # Should have some visual representation (█, ▓, ░, or similar)
        assert any(c in result["message"] for c in ["█", "▓", "░", "■", "□", "[", "="])


class TestBudgetStorage:
    """Test budget storage operations"""

    @pytest.fixture
    def handlers(self):
        return BotHandlers(use_memory_db=True)

    @pytest.mark.asyncio
    async def test_budget_persists(self, handlers):
        """Test that budget is stored and retrieved"""
        user_id = 12345

        await handlers.set_budget(user_id, 75000)

        budget = handlers.get_user_budget(user_id)
        assert budget == 75000

    @pytest.mark.asyncio
    async def test_budget_update(self, handlers):
        """Test that budget can be updated"""
        user_id = 12345

        await handlers.set_budget(user_id, 50000)
        await handlers.set_budget(user_id, 60000)

        budget = handlers.get_user_budget(user_id)
        assert budget == 60000
