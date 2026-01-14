"""Pytest configuration for BDD tests."""
import pytest


@pytest.fixture
def app_context():
    """Application context fixture."""
    return {}


@pytest.fixture
def yagpt_service():
    """YaGPT service fixture."""
    from src.services.yagpt_service import YaGPTService
    return YaGPTService()


@pytest.fixture
def expense_storage():
    """Expense storage fixture (in-memory)."""
    from src.services.expense_storage import ExpenseStorage
    return ExpenseStorage(use_memory=True)


@pytest.fixture
def bot_handlers():
    """Bot handlers fixture (in-memory mode)."""
    from src.bot.handlers import BotHandlers
    return BotHandlers(use_memory_db=True)
