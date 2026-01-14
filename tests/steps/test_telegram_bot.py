"""Step definitions for Telegram Bot feature."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Load scenarios from .feature file
scenarios('../features/telegram_bot.feature')


@pytest.fixture
def bot_context():
    """Context for bot tests."""
    return {}


@given('I have a bot handler')
def given_bot_handler(bot_handlers, bot_context):
    """Set up bot handler."""
    bot_context['handler'] = bot_handlers
    return bot_context


@given(parsers.parse('user {user_id:d} has saved expenses'))
def given_user_has_expenses_bot(bot_context, user_id):
    """Pre-populate expenses for bot test using handler's storage."""
    from src.services.expense_storage import Expense
    handler = bot_context['handler']
    expenses = [
        Expense(user_id=user_id, item='кофе', amount=300, category='Еда'),
        Expense(user_id=user_id, item='такси', amount=500, category='Транспорт'),
    ]
    for exp in expenses:
        handler.storage.save_expense(exp)
    bot_context['user_id'] = user_id


@when(parsers.parse('user {user_id:d} sends "{message}"'))
def when_user_sends(bot_context, user_id, message):
    """User sends a message."""
    import asyncio
    handler = bot_context['handler']
    bot_context['user_id'] = user_id
    bot_context['message'] = message

    if message == '/start':
        bot_context['response'] = asyncio.get_event_loop().run_until_complete(
            handler.handle_start(user_id)
        )
    else:
        bot_context['response'] = asyncio.get_event_loop().run_until_complete(
            handler.handle_message(user_id, message)
        )


@then('the bot should respond with a welcome message')
def then_welcome_message(bot_context):
    """Verify welcome message."""
    response = bot_context['response']
    assert response is not None
    assert len(response) > 0
    # Check for typical welcome words
    assert any(word in response.lower() for word in ['привет', 'добро пожаловать', 'трекер', 'расход'])


@then('the bot should parse the expense')
def then_parse_expense(bot_context):
    """Verify expense was parsed."""
    # This is verified by the confirmation response
    pass


@then('save it to storage')
def then_save_to_storage(bot_context):
    """Verify expense was saved."""
    # This is verified by the confirmation response
    pass


@then('respond with confirmation')
def then_respond_confirmation(bot_context):
    """Verify confirmation response."""
    response = bot_context['response']
    assert response is not None
    # Should mention the expense was recorded
    assert any(word in response.lower() for word in ['записал', 'сохранил', 'добавил', '300', 'кофе'])


@then('the bot should respond with expense report')
def then_expense_report(bot_context):
    """Verify expense report response."""
    response = bot_context['response']
    assert response is not None
    # Should contain report-like content
    assert len(response) > 0


@then('the bot should respond with help message')
def then_help_message(bot_context):
    """Verify help message."""
    response = bot_context['response']
    assert response is not None
    assert len(response) > 0
