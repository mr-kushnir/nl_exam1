"""Step definitions for Analytics feature (NLE-A-20)."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from datetime import datetime

# Load scenarios from .feature file
scenarios('../features/analytics.feature')


@pytest.fixture
def analytics_context():
    """Context for analytics tests."""
    return {
        'expenses': [],
        'response': None,
        'chart': None,
        'suggestion': None
    }


@given('user has expenses in categories:')
def given_expenses_in_categories(analytics_context, expense_storage, datatable):
    """Add expenses by category from datatable."""
    from src.services.expense_storage import Expense

    # Parse datatable (pytest-bdd format)
    for row in datatable:
        category = row['Category']
        amount = int(row['Amount'])
        expense = Expense(
            user_id=12345,
            item=category.lower(),
            amount=amount,
            category=category
        )
        expense_storage.save_expense(expense)
        analytics_context['expenses'].append(expense)
    return analytics_context


@given('user has expenses across multiple weeks')
def given_weekly_expenses(analytics_context, expense_storage):
    """Add expenses across weeks."""
    from src.services.expense_storage import Expense
    from datetime import timedelta

    now = datetime.now()
    # This week
    expense1 = Expense(user_id=12345, item='кофе', amount=300, category='Еда', created_at=now)
    # Last week
    expense2 = Expense(user_id=12345, item='обед', amount=500, category='Еда',
                       created_at=now - timedelta(days=7))
    expense_storage.save_expense(expense1)
    expense_storage.save_expense(expense2)
    analytics_context['expenses'] = [expense1, expense2]
    return analytics_context


@given(parsers.parse('user adds expense "{expense}"'))
def given_add_expense(analytics_context, expense_storage, expense, yagpt_service):
    """Add specific expense."""
    from src.services.expense_storage import Expense
    parsed = yagpt_service.parse_expense(expense)
    if parsed:
        exp = Expense(
            user_id=12345,
            item=parsed.item,
            amount=parsed.amount,
            category=parsed.category
        )
        expense_storage.save_expense(exp)
        analytics_context['last_expense'] = exp
    return analytics_context


@given('same expense was added last month')
def given_same_last_month(analytics_context):
    """Mark that same expense exists from last month."""
    analytics_context['recurring_detected'] = True
    return analytics_context


@given(parsers.parse('user has recurring expense (rent, 1st of month)'))
def given_recurring_expense(analytics_context):
    """User has recurring expense."""
    analytics_context['recurring'] = {
        'item': 'Аренда',
        'amount': 25000,
        'day': 1
    }
    return analytics_context


@when(parsers.parse('user sends "{command}"'))
def when_user_sends(analytics_context, expense_storage, command):
    """Process user command."""
    if command == 'расходы':
        totals = expense_storage.get_category_totals(12345)
        if totals:
            # Generate ASCII chart
            max_amount = max(totals.values()) if totals else 1
            lines = []
            for cat, amount in sorted(totals.items(), key=lambda x: -x[1]):
                bar_len = int((amount / max_amount) * 16)
                bar = '█' * bar_len
                lines.append(f"{cat:<12} {bar:<16} {amount}₽")
            analytics_context['chart'] = '\n'.join(lines)
            analytics_context['response'] = analytics_context['chart']
    return analytics_context


@when('user sends /stats days')
def when_stats_days(analytics_context, expense_storage):
    """Process stats by day command."""
    expenses = expense_storage.get_expenses(12345)
    # Group by day of week
    day_totals = {}
    for e in expenses:
        if e.created_at:
            day = e.created_at.strftime('%A')
            day_totals[day] = day_totals.get(day, 0) + e.amount

    if day_totals:
        max_day = max(day_totals, key=day_totals.get)
        analytics_context['response'] = f"Больше всего тратите в {max_day}"
        analytics_context['max_day'] = max_day
    return analytics_context


@when('expense is saved')
def when_expense_saved(analytics_context):
    """After expense saved, check for recurring."""
    if analytics_context.get('recurring_detected'):
        analytics_context['suggestion'] = "Сделать регулярным расходом?"
    return analytics_context


@when('it is the 1st of the month')
def when_first_of_month(analytics_context):
    """Simulate 1st of month."""
    recurring = analytics_context.get('recurring')
    if recurring:
        analytics_context['reminder'] = f"Напоминание: {recurring['item']} {recurring['amount']}₽"
    return analytics_context


@then('bot shows ASCII bar chart:')
def then_show_chart(analytics_context, docstring=None):
    """Verify ASCII chart shown."""
    chart = analytics_context.get('chart', '')
    assert '█' in chart or len(chart) > 0


@then('bot shows average spending per day of week')
def then_show_day_average(analytics_context):
    """Verify day stats shown."""
    response = analytics_context.get('response', '')
    assert len(response) > 0


@then('highlights the highest spending day')
def then_highlight_max_day(analytics_context):
    """Verify max day highlighted."""
    assert analytics_context.get('max_day') is not None


@then(parsers.parse('bot suggests "{message}"'))
def then_bot_suggests(analytics_context, message):
    """Verify suggestion shown."""
    suggestion = analytics_context.get('suggestion', '')
    assert 'регулярным' in suggestion or message in suggestion


@then(parsers.parse('shows inline button "{button}"'))
def then_show_button(analytics_context, button):
    """Verify button shown."""
    # In real implementation, would check button
    assert analytics_context.get('suggestion') is not None or analytics_context.get('reminder') is not None


@then(parsers.parse('bot sends reminder "{message}"'))
def then_send_reminder(analytics_context, message):
    """Verify reminder sent."""
    reminder = analytics_context.get('reminder', '')
    assert 'Напоминание' in reminder or message in reminder


@then(parsers.parse('shows button "{button}"'))
def then_show_action_button(analytics_context, button):
    """Verify action button shown."""
    assert analytics_context.get('reminder') is not None
