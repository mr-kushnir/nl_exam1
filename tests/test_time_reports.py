"""
Tests for Time-based Reports
BDD Reference: NLE-A-17
"""
import pytest
from datetime import datetime, timedelta
from src.bot.handlers import BotHandlers
from src.services.expense_storage import Expense


class TestTimeBasedReports:
    """Feature: Time-based Expense Reports"""

    @pytest.fixture
    def handlers(self):
        return BotHandlers(use_memory_db=True)

    def _add_expense(self, handlers, user_id, item, amount, category, days_ago=0):
        """Helper to add expense with specific date"""
        expense = Expense(
            user_id=user_id,
            item=item,
            amount=amount,
            category=category,
            created_at=datetime.now() - timedelta(days=days_ago)
        )
        handlers.storage.save_expense(expense)
        return expense

    @pytest.mark.asyncio
    async def test_today_expenses_with_data(self, handlers):
        """Scenario: Show today's expenses
        Given user has expenses for today
        When user sends /today command
        Then bot shows list of today's expenses with total
        """
        user_id = 12345

        # Add expenses for today
        self._add_expense(handlers, user_id, "кофе", 300, "Еда", days_ago=0)
        self._add_expense(handlers, user_id, "такси", 500, "Транспорт", days_ago=0)

        result = await handlers.handle_today(user_id)

        assert "сегодня" in result.lower()
        assert "кофе" in result.lower() or "300" in result
        assert "такси" in result.lower() or "500" in result
        assert "800" in result  # Total

    @pytest.mark.asyncio
    async def test_today_no_expenses(self, handlers):
        """Scenario: Today with no expenses
        Given user has no expenses for today
        When user sends /today command
        Then bot shows appropriate message
        """
        user_id = 12345

        # Add expense from yesterday only
        self._add_expense(handlers, user_id, "кофе", 300, "Еда", days_ago=1)

        result = await handlers.handle_today(user_id)

        assert "нет" in result.lower() or "пусто" in result.lower()

    @pytest.mark.asyncio
    async def test_week_comparison_increase(self, handlers):
        """Scenario: Weekly comparison with increase
        Given current week total is 5000
        And previous week total is 4000
        When user sends /week command
        Then bot shows increase percentage
        """
        user_id = 12345

        # Previous week expenses (7+ days ago, in previous Monday-Sunday)
        self._add_expense(handlers, user_id, "еда", 4000, "Еда", days_ago=8)

        # This week expenses (within current Mon-Sun)
        self._add_expense(handlers, user_id, "еда", 5000, "Еда", days_ago=0)

        result = await handlers.handle_week(user_id)

        assert "неделя" in result.lower() or "неделю" in result.lower()
        # Check for "5,000" with thousands separator
        assert "5,000" in result or "5000" in result
        assert "больше" in result.lower() or "+" in result or "25" in result

    @pytest.mark.asyncio
    async def test_week_comparison_decrease(self, handlers):
        """Scenario: Weekly comparison with decrease
        Given current week total is 3000
        And previous week total is 4000
        When user sends /week command
        Then bot shows decrease percentage
        """
        user_id = 12345

        # Previous week expenses
        self._add_expense(handlers, user_id, "еда", 4000, "Еда", days_ago=8)

        # This week expenses (less)
        self._add_expense(handlers, user_id, "еда", 3000, "Еда", days_ago=0)

        result = await handlers.handle_week(user_id)

        assert "меньше" in result.lower() or "-" in result or "25" in result

    @pytest.mark.asyncio
    async def test_week_no_previous_data(self, handlers):
        """Scenario: First week usage
        Given user has no previous week data
        When user sends /week command
        Then bot shows current week only
        """
        user_id = 12345

        # Only this week
        self._add_expense(handlers, user_id, "кофе", 1000, "Еда", days_ago=0)

        result = await handlers.handle_week(user_id)

        assert "1,000" in result or "1000" in result


class TestStorageTimeMethods:
    """Test storage methods for time-based queries"""

    @pytest.fixture
    def handlers(self):
        return BotHandlers(use_memory_db=True)

    def _add_expense(self, handlers, user_id, item, amount, category, days_ago=0):
        expense = Expense(
            user_id=user_id,
            item=item,
            amount=amount,
            category=category,
            created_at=datetime.now() - timedelta(days=days_ago)
        )
        handlers.storage.save_expense(expense)

    def test_get_today_expenses(self, handlers):
        """Test getting only today's expenses"""
        user_id = 12345

        self._add_expense(handlers, user_id, "today1", 100, "Еда", days_ago=0)
        self._add_expense(handlers, user_id, "yesterday", 200, "Еда", days_ago=1)

        today = handlers.storage.get_today_expenses(user_id)

        assert len(today) == 1
        assert today[0].item == "today1"

    def test_get_week_expenses(self, handlers):
        """Test getting current week expenses"""
        user_id = 12345

        # Use day 0 for this week (guaranteed to be in current week)
        self._add_expense(handlers, user_id, "this_week", 100, "Еда", days_ago=0)
        # Use day 8 for last week (guaranteed to be in previous week)
        self._add_expense(handlers, user_id, "last_week", 200, "Еда", days_ago=8)

        this_week = handlers.storage.get_week_expenses(user_id, weeks_ago=0)
        last_week = handlers.storage.get_week_expenses(user_id, weeks_ago=1)

        assert len(this_week) == 1
        assert this_week[0].item == "this_week"
        assert len(last_week) == 1
        assert last_week[0].item == "last_week"
