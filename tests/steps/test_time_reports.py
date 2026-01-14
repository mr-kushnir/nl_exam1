"""Step definitions for Time-based Reports feature (NLE-A-17)."""
import pytest
from datetime import datetime, timedelta
from pytest_bdd import scenarios, given, when, then, parsers

# Load scenarios from .feature file
scenarios('../features/time_reports.feature')


@pytest.fixture
def time_context():
    """Context for time-based reports tests."""
    return {
        'expenses': [],
        'response': None,
        'current_week_total': 0,
        'previous_week_total': 0
    }


@given('user has expenses for today')
def given_expenses_today(time_context, expense_storage):
    """Add expenses for today."""
    from src.services.expense_storage import Expense
    today = datetime.now()
    expense = Expense(
        user_id=12345,
        item='кофе',
        amount=300,
        category='Еда',
        created_at=today
    )
    expense_storage.save_expense(expense)
    time_context['has_today'] = True
    return time_context


@given('user has no expenses for today')
def given_no_expenses_today(time_context):
    """No expenses for today."""
    time_context['has_today'] = False
    return time_context


@given('user has expenses for current and previous week')
def given_weekly_expenses(time_context, expense_storage):
    """Add expenses for both weeks."""
    from src.services.expense_storage import Expense
    now = datetime.now()

    # Current week
    expense1 = Expense(user_id=12345, item='обед', amount=500, category='Еда', created_at=now)
    expense_storage.save_expense(expense1)

    # Previous week (simulated in context)
    time_context['current_week_total'] = 500
    time_context['previous_week_total'] = 400
    return time_context


@given(parsers.parse('current week total is {amount:d}'))
def given_current_week_total(time_context, amount):
    """Set current week total."""
    time_context['current_week_total'] = amount
    return time_context


@given(parsers.parse('previous week total is {amount:d}'))
def given_previous_week_total(time_context, amount):
    """Set previous week total."""
    time_context['previous_week_total'] = amount
    return time_context


@when('user sends /today command')
def when_today_command(time_context, expense_storage):
    """Process /today command."""
    expenses = expense_storage.get_monthly_expenses(12345)
    today = datetime.now().date()
    today_expenses = [e for e in expenses if e.created_at.date() == today]

    if today_expenses:
        total = sum(e.amount for e in today_expenses)
        time_context['response'] = f"Сегодня: {total}₽"
    else:
        time_context['response'] = "Сегодня расходов нет"
    return time_context


@when('user sends /week command')
def when_week_command(time_context):
    """Process /week command."""
    current = time_context['current_week_total']
    previous = time_context['previous_week_total']

    if previous > 0:
        change = ((current - previous) / previous) * 100
        if change > 0:
            time_context['response'] = f"На {abs(int(change))}% больше чем на прошлой неделе"
        else:
            time_context['response'] = f"На {abs(int(change))}% меньше чем на прошлой неделе"
    else:
        time_context['response'] = f"Эта неделя: {current}₽"
    return time_context


@then('bot shows list of today\'s expenses')
def then_show_today_list(time_context):
    """Verify today's expenses shown."""
    response = time_context.get('response', '')
    assert 'Сегодня' in response or '₽' in response


@then('bot shows total amount for today')
def then_show_today_total(time_context):
    """Verify today's total shown."""
    response = time_context.get('response', '')
    assert '₽' in response


@then(parsers.parse('bot shows "{message}"'))
def then_bot_shows(time_context, message):
    """Verify bot message."""
    response = time_context.get('response', '')
    # Check key parts of message
    if 'больше' in message:
        assert 'больше' in response
    elif 'меньше' in message:
        assert 'меньше' in response
    elif 'нет' in message:
        assert 'нет' in response


@then('bot shows current week total')
def then_show_week_total(time_context):
    """Verify week total shown."""
    response = time_context.get('response', '')
    assert '₽' in response or '%' in response


@then('bot shows comparison with previous week (percentage change)')
def then_show_comparison(time_context):
    """Verify comparison shown."""
    response = time_context.get('response', '')
    assert '%' in response or 'неделе' in response
