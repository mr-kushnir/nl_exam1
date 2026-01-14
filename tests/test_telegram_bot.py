"""
Tests for Telegram Bot
BDD Reference: NLE-A-11
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from src.bot.handlers import BotHandlers


class TestTelegramBot:
    """Feature: Telegram Bot Interface"""

    @pytest.fixture
    def handlers(self):
        return BotHandlers()

    @pytest.mark.asyncio
    async def test_handle_start_command(self, handlers):
        """Scenario: Handle /start
        Given user sends /start
        When bot processes command
        Then send welcome message and show usage examples
        """
        response = await handlers.handle_start(user_id=12345)

        assert response is not None
        assert "привет" in response.lower() or "добро" in response.lower()
        assert "кофе" in response.lower() or "пример" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_expense_message(self, handlers):
        """Scenario: Handle expense message
        Given user sends "кофе 300"
        When bot processes message
        Then save expense and reply with confirmation
        """
        response = await handlers.handle_message(user_id=12345, text="кофе 300")

        assert response is not None
        assert "300" in response or "кофе" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_report_command(self, handlers):
        """Scenario: Handle report command
        Given user sends "расходы"
        When bot processes message
        Then send report
        """
        # First add some expenses
        await handlers.handle_message(user_id=12345, text="кофе 300")
        await handlers.handle_message(user_id=12345, text="такси 500")

        response = await handlers.handle_message(user_id=12345, text="расходы")

        assert response is not None
        # Should contain totals or categories
        assert "₽" in response or "руб" in response.lower() or "итого" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_item_query(self, handlers):
        """Scenario: Handle item query
        Given user sends "кофе за месяц"
        When bot processes message
        Then send total for item
        """
        await handlers.handle_message(user_id=12345, text="кофе 300")
        await handlers.handle_message(user_id=12345, text="кофе 400")

        response = await handlers.handle_message(user_id=12345, text="кофе за месяц")

        assert response is not None
        assert "700" in response or "кофе" in response.lower()

    @pytest.mark.asyncio
    async def test_handle_top_expenses(self, handlers):
        """Scenario: Handle top expenses
        Given user sends "топ расходов"
        When bot processes message
        Then send top categories
        """
        await handlers.handle_message(user_id=12345, text="кофе 300")
        await handlers.handle_message(user_id=12345, text="такси 500")

        response = await handlers.handle_message(user_id=12345, text="топ расходов")

        assert response is not None

    @pytest.mark.asyncio
    async def test_handle_help_command(self, handlers):
        """Scenario: Handle /help"""
        response = await handlers.handle_help(user_id=12345)

        assert response is not None
        assert "пример" in response.lower() or "команд" in response.lower()
