"""
Tests for Analytics and Visualization
BDD Reference: NLE-A-20
"""
import pytest
from datetime import datetime, timedelta
from src.bot.handlers import BotHandlers
from src.services.expense_storage import Expense


class TestAnalytics:
    """Feature: Analytics and Visualization"""

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

    def test_ascii_chart_in_report(self, handlers):
        """Scenario: ASCII chart in monthly report
        Given user has expenses in multiple categories
        When generating report
        Then ASCII bar chart is included
        """
        user_id = 12345

        self._add_expense(handlers, user_id, "еда", 15000, "Еда")
        self._add_expense(handlers, user_id, "такси", 5000, "Транспорт")
        self._add_expense(handlers, user_id, "кино", 3000, "Развлечения")

        chart = handlers.generate_ascii_chart(user_id)

        # Should have bar characters
        assert "█" in chart or "▓" in chart or "■" in chart
        # Should show categories
        assert "еда" in chart.lower() or "транспорт" in chart.lower()

    @pytest.mark.asyncio
    async def test_day_of_week_statistics(self, handlers):
        """Scenario: Day-of-week statistics
        Given user has expenses across multiple weeks
        When requesting day stats
        Then shows average by day of week
        """
        user_id = 12345

        # Add expenses on different days
        for i in range(14):
            self._add_expense(handlers, user_id, f"expense_{i}", 1000, "Еда", days_ago=i)

        result = await handlers.handle_day_stats(user_id)

        assert result["success"] is True
        # Should mention day names
        days = ["понедельник", "вторник", "среда", "четверг", "пятница", "суббота", "воскресенье",
                "пн", "вт", "ср", "чт", "пт", "сб", "вс"]
        assert any(day in result["message"].lower() for day in days)

    @pytest.mark.asyncio
    async def test_day_stats_highlights_peak(self, handlers):
        """Scenario: Day stats highlights peak spending day"""
        user_id = 12345

        # Add more expenses on one specific day
        # Create expenses such that today has more
        for i in range(7):
            amount = 5000 if i == 0 else 1000  # Today gets more
            self._add_expense(handlers, user_id, f"expense_{i}", amount, "Еда", days_ago=i)

        result = await handlers.handle_day_stats(user_id)

        # Should highlight something about max day
        assert "больше" in result["message"].lower() or "максимум" in result["message"].lower() or "▲" in result["message"]


class TestAsciiChartGeneration:
    """Test ASCII chart rendering"""

    @pytest.fixture
    def handlers(self):
        return BotHandlers(use_memory_db=True)

    def test_chart_proportional_bars(self, handlers):
        """Test that bars are proportional to values"""
        user_id = 12345

        # Add expenses with known proportions
        expense1 = Expense(user_id=user_id, item="еда", amount=10000, category="Еда", created_at=datetime.now())
        expense2 = Expense(user_id=user_id, item="такси", amount=5000, category="Транспорт", created_at=datetime.now())
        handlers.storage.save_expense(expense1)
        handlers.storage.save_expense(expense2)

        chart = handlers.generate_ascii_chart(user_id)

        # Count bar characters for each category
        lines = chart.split("\n")
        еда_bar = ""
        транспорт_bar = ""

        for line in lines:
            line_lower = line.lower()
            if "еда" in line_lower:
                еда_bar = line
            elif "транспорт" in line_lower:
                транспорт_bar = line

        # Еда should have more bar characters than Транспорт
        assert еда_bar.count("█") >= транспорт_bar.count("█")

    def test_chart_empty_data(self, handlers):
        """Test chart generation with no data"""
        user_id = 12345

        chart = handlers.generate_ascii_chart(user_id)

        assert "нет" in chart.lower() or chart == ""


class TestEnhancedReport:
    """Test enhanced report with chart"""

    @pytest.fixture
    def handlers(self):
        return BotHandlers(use_memory_db=True)

    @pytest.mark.asyncio
    async def test_report_includes_chart(self, handlers):
        """Test that monthly report includes ASCII chart"""
        user_id = 12345

        expense = Expense(user_id=user_id, item="еда", amount=5000, category="Еда", created_at=datetime.now())
        handlers.storage.save_expense(expense)

        # Use existing _handle_report method
        result = await handlers._handle_report(user_id)

        # Report should have visual elements
        assert "₽" in result
        assert "еда" in result.lower() or "📊" in result
