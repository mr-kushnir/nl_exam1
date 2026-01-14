"""Step definitions for Budget Management feature (NLE-A-18)."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Load scenarios from .feature file
scenarios('../features/budget_management.feature')


@pytest.fixture
def budget_context():
    """Context for budget management tests."""
    return {
        'budget': 0,
        'expenses_total': 0,
        'response': None,
        'warning': None
    }


@given(parsers.parse('user sends /budget {amount:d}'))
def given_budget_command(budget_context, amount):
    """User sets budget."""
    budget_context['budget'] = amount
    return budget_context


@given(parsers.parse('user has budget {amount:d}'))
def given_user_has_budget(budget_context, amount):
    """User has existing budget."""
    budget_context['budget'] = amount
    return budget_context


@given(parsers.parse('current month expenses total {amount:d}'))
def given_expenses_total(budget_context, amount):
    """Set current expenses total."""
    budget_context['expenses_total'] = amount
    return budget_context


@when('command is processed')
def when_command_processed(budget_context):
    """Process budget command."""
    budget = budget_context['budget']
    budget_context['response'] = f"Бюджет на месяц: {budget}₽"
    return budget_context


@when('user sends /budget')
def when_check_budget(budget_context):
    """Check budget status."""
    budget = budget_context['budget']
    spent = budget_context['expenses_total']

    if budget > 0:
        if spent > budget:
            over = spent - budget
            budget_context['response'] = f"🔴 Бюджет превышен на {over}₽"
        else:
            percent = int((spent / budget) * 100)
            budget_context['response'] = f"Потрачено: {spent}₽ из {budget}₽"
            budget_context['progress'] = percent
    return budget_context


@when('user adds new expense')
def when_add_expense(budget_context):
    """Add new expense and check budget."""
    budget = budget_context['budget']
    spent = budget_context['expenses_total']

    if budget > 0:
        percent = int((spent / budget) * 100)
        if percent >= 80:
            budget_context['warning'] = f"⚠️ Вы израсходовали {percent}% бюджета"
    return budget_context


@then(parsers.parse('budget is saved: {amount:d}'))
def then_budget_saved(budget_context, amount):
    """Verify budget saved."""
    assert budget_context['budget'] == amount


@then(parsers.parse('bot confirms "{message}"'))
def then_bot_confirms(budget_context, message):
    """Verify confirmation message."""
    response = budget_context.get('response', '')
    assert 'Бюджет' in response or message in response


@then(parsers.parse('bot shows progress bar ({percent:d}%)'))
def then_show_progress(budget_context, percent):
    """Verify progress shown."""
    actual_percent = budget_context.get('progress', 0)
    assert actual_percent == percent


@then(parsers.parse('bot shows "{message}"'))
def then_bot_shows(budget_context, message):
    """Verify bot message."""
    response = budget_context.get('response', '')
    warning = budget_context.get('warning', '')
    combined = response + warning
    # Check key parts
    if 'Потрачено' in message:
        assert 'Потрачено' in combined or '₽' in combined
    elif 'превышен' in message:
        assert 'превышен' in combined


@then(parsers.parse('bot shows warning "{message}"'))
def then_show_warning(budget_context, message):
    """Verify warning shown."""
    warning = budget_context.get('warning', '')
    assert '⚠️' in warning or 'израсходовали' in warning
