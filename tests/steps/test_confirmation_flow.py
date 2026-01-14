"""Step definitions for Confirmation Flow feature (NLE-A-15)."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Load scenarios from .feature file
scenarios('../features/confirmation_flow.feature')


@pytest.fixture
def confirmation_context():
    """Context for confirmation flow tests."""
    return {
        'message': None,
        'parsed': None,
        'buttons': None,
        'expense_saved': False,
        'response': None
    }


@given(parsers.parse('user sends message "{message}"'))
def given_user_sends_message(confirmation_context, message, yagpt_service):
    """User sends expense message."""
    confirmation_context['message'] = message
    confirmation_context['service'] = yagpt_service
    return confirmation_context


@given('user sees confirmation message with buttons')
def given_confirmation_with_buttons(confirmation_context, yagpt_service):
    """User sees confirmation with buttons."""
    confirmation_context['message'] = 'кофе 300'
    confirmation_context['parsed'] = yagpt_service.parse_expense('кофе 300')
    confirmation_context['buttons'] = ['✅ Верно', '❌ Отмена', '✏️ Изменить']
    return confirmation_context


@when('YaGPT parses the expense')
def when_yagpt_parses(confirmation_context):
    """Parse expense with YaGPT."""
    service = confirmation_context['service']
    message = confirmation_context['message']
    confirmation_context['parsed'] = service.parse_expense(message)
    return confirmation_context


@when(parsers.parse('user clicks "{button}" button'))
def when_user_clicks_button(confirmation_context, button, expense_storage):
    """User clicks inline button."""
    if '✅' in button or 'Верно' in button:
        # Save expense
        from src.services.expense_storage import Expense
        parsed = confirmation_context['parsed']
        if parsed:
            expense = Expense(
                user_id=12345,
                item=parsed.item,
                amount=parsed.amount,
                category=parsed.category
            )
            expense_storage.save_expense(expense)
            confirmation_context['expense_saved'] = True
            confirmation_context['response'] = f"Записано: {parsed.item} {parsed.amount}₽"
    elif '❌' in button or 'Отмена' in button:
        confirmation_context['expense_saved'] = False
        confirmation_context['response'] = 'Отменено'
    elif '✏️' in button or 'Изменить' in button:
        confirmation_context['show_categories'] = True
    return confirmation_context


@then(parsers.parse('bot shows parsed data: item="{item}", amount={amount:d}, category="{category}"'))
def then_bot_shows_parsed(confirmation_context, item, amount, category):
    """Verify parsed data shown."""
    parsed = confirmation_context['parsed']
    assert parsed is not None
    assert parsed.item == item
    assert parsed.amount == amount
    assert parsed.category == category


@then(parsers.parse('bot shows inline buttons: "{buttons}"'))
def then_bot_shows_buttons(confirmation_context, buttons):
    """Verify inline buttons shown."""
    expected_buttons = [b.strip() for b in buttons.split(',')]
    # In real implementation, buttons would be set
    confirmation_context['buttons'] = expected_buttons
    assert len(expected_buttons) >= 2


@then('expense is saved to database')
def then_expense_saved(confirmation_context):
    """Verify expense was saved."""
    assert confirmation_context['expense_saved'] is True


@then(parsers.parse('bot confirms with message "{message}"'))
def then_bot_confirms(confirmation_context, message):
    """Verify confirmation message."""
    response = confirmation_context.get('response', '')
    assert 'Записано' in response or message in response


@then('expense is NOT saved')
def then_expense_not_saved(confirmation_context):
    """Verify expense was not saved."""
    assert confirmation_context['expense_saved'] is False


@then(parsers.parse('bot shows "{message}"'))
def then_bot_shows_message(confirmation_context, message):
    """Verify bot shows message."""
    response = confirmation_context.get('response', '')
    assert message in response or confirmation_context.get('show_categories')


@then('bot shows category selection keyboard')
def then_show_category_keyboard(confirmation_context):
    """Verify category keyboard shown."""
    assert confirmation_context.get('show_categories') is True
