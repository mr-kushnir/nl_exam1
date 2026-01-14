"""
Tests for Expense Management Commands
BDD Reference: NLE-A-19
"""
import pytest
import csv
import io
from datetime import datetime, timedelta
from src.bot.handlers import BotHandlers
from src.services.expense_storage import Expense


class TestExpenseManagement:
    """Feature: Expense Management"""

    @pytest.fixture
    def handlers(self):
        return BotHandlers(use_memory_db=True)

    def _add_expense(self, handlers, user_id, item, amount, category, days_ago=0):
        """Helper to add expense"""
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
    async def test_undo_last_expense(self, handlers):
        """Scenario: Undo last expense
        Given user has saved expenses
        When user sends /undo
        Then last expense is deleted
        """
        user_id = 12345

        self._add_expense(handlers, user_id, "first", 100, "Еда")
        self._add_expense(handlers, user_id, "last", 200, "Еда")

        result = await handlers.handle_undo(user_id)

        assert result["success"] is True
        assert "last" in result["message"].lower() or "200" in result["message"]
        assert "удален" in result["message"].lower()

        # Verify only first expense remains
        expenses = handlers.storage.get_expenses(user_id)
        assert len(expenses) == 1
        assert expenses[0].item == "first"

    @pytest.mark.asyncio
    async def test_undo_no_expenses(self, handlers):
        """Scenario: Undo with no expenses
        Given user has no expenses
        When user sends /undo
        Then bot shows appropriate message
        """
        user_id = 12345

        result = await handlers.handle_undo(user_id)

        assert result["success"] is False
        assert "нечего" in result["message"].lower() or "нет" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_export_to_csv(self, handlers):
        """Scenario: Export to CSV
        Given user has expenses for the month
        When user sends /export
        Then bot generates CSV data
        """
        user_id = 12345

        self._add_expense(handlers, user_id, "кофе", 300, "Еда")
        self._add_expense(handlers, user_id, "такси", 500, "Транспорт")

        result = await handlers.handle_export(user_id)

        assert result["success"] is True
        assert "csv_data" in result

        # Parse CSV and verify
        csv_file = io.StringIO(result["csv_data"])
        reader = csv.DictReader(csv_file)
        rows = list(reader)

        assert len(rows) == 2
        # Check columns exist
        assert "date" in rows[0] or "дата" in rows[0].keys().__str__().lower()

    @pytest.mark.asyncio
    async def test_export_no_expenses(self, handlers):
        """Scenario: Export with no expenses"""
        user_id = 12345

        result = await handlers.handle_export(user_id)

        assert result["success"] is False
        assert "нет" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_find_expenses_by_name(self, handlers):
        """Scenario: Search expenses by name
        Given user has multiple expenses
        When user sends /find кофе
        Then bot shows all matching expenses
        """
        user_id = 12345

        self._add_expense(handlers, user_id, "кофе", 300, "Еда")
        self._add_expense(handlers, user_id, "кофе латте", 400, "Еда")
        self._add_expense(handlers, user_id, "такси", 500, "Транспорт")

        result = await handlers.handle_find(user_id, "кофе")

        assert result["success"] is True
        assert "кофе" in result["message"].lower()
        # Total should be 700 (300 + 400)
        assert "700" in result["message"] or "2" in result["message"]  # Either total or count

    @pytest.mark.asyncio
    async def test_find_no_results(self, handlers):
        """Scenario: Search with no results
        Given user has expenses
        When user sends /find unknown
        Then bot shows not found message
        """
        user_id = 12345

        self._add_expense(handlers, user_id, "кофе", 300, "Еда")

        result = await handlers.handle_find(user_id, "пицца")

        assert result["success"] is True  # Search succeeded, just no results
        assert "не найден" in result["message"].lower() or "нет" in result["message"].lower()


class TestExportFormat:
    """Test CSV export format"""

    @pytest.fixture
    def handlers(self):
        return BotHandlers(use_memory_db=True)

    @pytest.mark.asyncio
    async def test_csv_has_required_columns(self, handlers):
        """Test that CSV has all required columns"""
        user_id = 12345

        expense = Expense(
            user_id=user_id,
            item="кофе",
            amount=300,
            category="Еда",
            created_at=datetime.now()
        )
        handlers.storage.save_expense(expense)

        result = await handlers.handle_export(user_id)

        csv_file = io.StringIO(result["csv_data"])
        reader = csv.DictReader(csv_file)
        rows = list(reader)

        # Check required columns (case-insensitive)
        headers = [h.lower() for h in rows[0].keys()]
        assert any("date" in h or "дата" in h for h in headers)
        assert any("item" in h or "название" in h for h in headers)
        assert any("amount" in h or "сумма" in h for h in headers)
        assert any("category" in h or "категория" in h for h in headers)
