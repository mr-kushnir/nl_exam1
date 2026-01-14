"""
Tests for Expense Storage Service
BDD Reference: NLE-A-10
"""
import pytest
from datetime import datetime, timedelta
from src.services.expense_storage import ExpenseStorage, Expense


class TestExpenseStorage:
    """Feature: Expense Data Storage"""

    @pytest.fixture
    def storage(self):
        return ExpenseStorage(use_memory=True)

    @pytest.fixture
    def sample_expense(self):
        return Expense(
            user_id=12345,
            item="кофе",
            amount=300,
            category="Еда"
        )

    def test_save_expense(self, storage, sample_expense):
        """Scenario: Save expense
        Given user_id=12345, item="кофе", amount=300, category="Еда"
        When save_expense is called
        Then expense stored with timestamp
        And return success
        """
        result = storage.save_expense(sample_expense)

        assert result is True

        # Verify it was saved
        expenses = storage.get_expenses(user_id=12345)
        assert len(expenses) == 1
        assert expenses[0].item == "кофе"
        assert expenses[0].amount == 300
        assert expenses[0].created_at is not None

    def test_get_monthly_expenses(self, storage):
        """Scenario: Get monthly expenses
        Given user has expenses in current month
        When get_monthly_expenses(user_id) called
        Then return list of expenses for current month
        """
        # Add expenses
        storage.save_expense(Expense(user_id=12345, item="кофе", amount=300, category="Еда"))
        storage.save_expense(Expense(user_id=12345, item="такси", amount=500, category="Транспорт"))

        expenses = storage.get_monthly_expenses(user_id=12345)

        assert len(expenses) == 2

    def test_get_expenses_by_category(self, storage):
        """Scenario: Get expenses by category
        Given user has 3 Еда expenses
        When get_by_category(user_id, "Еда") called
        Then return 3 expenses
        """
        storage.save_expense(Expense(user_id=12345, item="кофе", amount=300, category="Еда"))
        storage.save_expense(Expense(user_id=12345, item="обед", amount=500, category="Еда"))
        storage.save_expense(Expense(user_id=12345, item="ужин", amount=700, category="Еда"))
        storage.save_expense(Expense(user_id=12345, item="такси", amount=400, category="Транспорт"))

        expenses = storage.get_by_category(user_id=12345, category="Еда")

        assert len(expenses) == 3
        assert all(e.category == "Еда" for e in expenses)

    def test_get_item_total(self, storage):
        """Scenario: Get item total
        Given user spent 300+400+500 on кофе
        When get_item_total(user_id, "кофе") called
        Then return 1200
        """
        storage.save_expense(Expense(user_id=12345, item="кофе", amount=300, category="Еда"))
        storage.save_expense(Expense(user_id=12345, item="кофе", amount=400, category="Еда"))
        storage.save_expense(Expense(user_id=12345, item="кофе", amount=500, category="Еда"))

        total = storage.get_item_total(user_id=12345, item="кофе")

        assert total == 1200

    def test_get_category_totals(self, storage):
        """Scenario: Get category totals
        Given user has expenses in multiple categories
        When get_category_totals(user_id) called
        Then return dict with category sums
        """
        storage.save_expense(Expense(user_id=12345, item="кофе", amount=300, category="Еда"))
        storage.save_expense(Expense(user_id=12345, item="обед", amount=500, category="Еда"))
        storage.save_expense(Expense(user_id=12345, item="такси", amount=600, category="Транспорт"))

        totals = storage.get_category_totals(user_id=12345)

        assert totals["Еда"] == 800
        assert totals["Транспорт"] == 600

    def test_get_total(self, storage):
        """Additional: Get total expenses"""
        storage.save_expense(Expense(user_id=12345, item="кофе", amount=300, category="Еда"))
        storage.save_expense(Expense(user_id=12345, item="такси", amount=500, category="Транспорт"))

        total = storage.get_total(user_id=12345)

        assert total == 800
