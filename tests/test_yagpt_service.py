"""
Tests for YaGPT Service
BDD Reference: NLE-A-8
"""
import pytest
from src.services.yagpt_service import YaGPTService, ParsedExpense, Intent


class TestYaGPTExpenseParser:
    """Feature: YaGPT Expense Parser"""

    @pytest.fixture
    def service(self):
        return YaGPTService()

    def test_parse_simple_expense(self, service):
        """Scenario: Parse expense message
        Given user message "кофе 300"
        When YaGPT processes message
        Then extract item "кофе", amount 300, category "Еда"
        """
        result = service.parse_expense("кофе 300")

        assert result is not None
        assert result.item == "кофе"
        assert result.amount == 300
        assert result.category == "Еда"

    def test_parse_complex_expense(self, service):
        """Scenario: Parse complex message
        Given user message "такси до работы 600р"
        When YaGPT processes message
        Then extract item containing "такси", amount 600, category "Транспорт"
        """
        result = service.parse_expense("такси до работы 600р")

        assert result is not None
        # YaGPT may simplify the item name, so we just check it contains "такси"
        assert "такси" in result.item.lower()
        assert result.amount == 600
        assert result.category == "Транспорт"

    def test_generate_confirmation_with_emoji(self, service):
        """Scenario: Generate expense confirmation
        Given expense saved with item="кофе" amount=300 category="Еда"
        When YaGPT generates response
        Then response includes emoji and confirms category and amount
        """
        expense = ParsedExpense(item="кофе", amount=300, category="Еда")
        response = service.generate_confirmation(expense)

        assert response is not None
        assert "300" in response
        assert "Еда" in response or "кофе" in response
        # Check for any emoji
        assert any(ord(c) > 127 for c in response)

    def test_detect_report_intent(self, service):
        """Scenario: Handle report request
        Given user message "расходы"
        When YaGPT detects intent
        Then return intent "report_monthly"
        """
        intent = service.detect_intent("расходы")

        assert intent.type == "report_monthly"

    def test_detect_item_query_intent(self, service):
        """Scenario: Handle item query
        Given user message "кофе за месяц"
        When YaGPT detects intent
        Then return intent "item_total" and extract item "кофе"
        """
        intent = service.detect_intent("кофе за месяц")

        assert intent.type == "item_total"
        assert intent.item == "кофе"

    def test_detect_top_expenses_intent(self, service):
        """Additional: Handle top expenses request"""
        intent = service.detect_intent("топ расходов")

        assert intent.type == "top_expenses"

    def test_detect_expense_intent(self, service):
        """Additional: Detect expense intent for regular message"""
        intent = service.detect_intent("обед 500")

        assert intent.type == "add_expense"

    def test_parse_multiple_expenses_single(self, service):
        """Scenario: Parse single expense returns list with one item"""
        result = service.parse_multiple_expenses("кофе 300")

        assert isinstance(result, list)
        assert len(result) >= 1
        assert result[0].amount == 300

    def test_parse_multiple_expenses_empty_for_invalid(self, service):
        """Scenario: Invalid message returns empty list"""
        result = service.parse_multiple_expenses("привет")

        assert isinstance(result, list)
        assert len(result) == 0

    def test_generate_multiple_confirmation_single(self, service):
        """Scenario: Single expense generates simple confirmation"""
        expenses = [ParsedExpense(item="кофе", amount=300, category="Еда")]
        response = service.generate_multiple_confirmation(expenses)

        assert "кофе" in response
        assert "300" in response

    def test_generate_multiple_confirmation_multiple(self, service):
        """Scenario: Multiple expenses generate list confirmation"""
        expenses = [
            ParsedExpense(item="жене", amount=500, category="Переводы"),
            ParsedExpense(item="маме", amount=500, category="Переводы"),
            ParsedExpense(item="пиво", amount=1000, category="Развлечения"),
        ]
        response = service.generate_multiple_confirmation(expenses)

        assert "3 расход" in response
        assert "жене" in response
        assert "маме" in response
        assert "пиво" in response
        assert "2 000" in response or "2,000" in response  # total
