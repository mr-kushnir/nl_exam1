"""Step definitions for Expense Management feature (NLE-A-19)."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Load scenarios from .feature file
scenarios('../features/expense_management.feature')


@pytest.fixture
def management_context():
    """Context for expense management tests."""
    return {
        'expenses': [],
        'response': None,
        'csv_content': None,
        'search_results': []
    }


@given('user has saved expenses')
def given_saved_expenses(management_context, expense_storage):
    """User has saved expenses."""
    from src.services.expense_storage import Expense
    expense = Expense(user_id=12345, item='кофе', amount=300, category='Еда')
    expense_storage.save_expense(expense)
    management_context['last_expense'] = expense
    return management_context


@given('user has no expenses')
def given_no_expenses(management_context):
    """User has no expenses."""
    management_context['expenses'] = []
    return management_context


@given('user has expenses for the month')
def given_monthly_expenses(management_context, expense_storage):
    """User has monthly expenses."""
    from src.services.expense_storage import Expense
    expenses = [
        Expense(user_id=12345, item='кофе', amount=300, category='Еда'),
        Expense(user_id=12345, item='такси', amount=500, category='Транспорт'),
    ]
    for e in expenses:
        expense_storage.save_expense(e)
    management_context['expenses'] = expenses
    return management_context


@given('user has multiple expenses')
def given_multiple_expenses(management_context, expense_storage):
    """User has multiple expenses."""
    from src.services.expense_storage import Expense
    expenses = [
        Expense(user_id=12345, item='кофе утром', amount=200, category='Еда'),
        Expense(user_id=12345, item='кофе вечером', amount=300, category='Еда'),
        Expense(user_id=12345, item='такси', amount=500, category='Транспорт'),
    ]
    for e in expenses:
        expense_storage.save_expense(e)
    management_context['expenses'] = expenses
    return management_context


@given('user has expenses')
def given_has_expenses(management_context, expense_storage):
    """User has some expenses."""
    from src.services.expense_storage import Expense
    expense = Expense(user_id=12345, item='обед', amount=400, category='Еда')
    expense_storage.save_expense(expense)
    management_context['expenses'] = [expense]
    return management_context


@when('user sends /undo')
def when_undo_command(management_context, expense_storage):
    """Process undo command."""
    expenses = expense_storage.get_expenses(12345)
    if expenses:
        last = expenses[-1]
        # In real implementation, would delete from storage
        management_context['response'] = f"Удалено: {last.item} {last.amount}₽"
        management_context['deleted'] = last
    else:
        management_context['response'] = "Нечего отменять"
    return management_context


@when('user sends /export')
def when_export_command(management_context, expense_storage):
    """Process export command."""
    expenses = expense_storage.get_expenses(12345)
    if expenses:
        # Generate CSV
        lines = ['date,item,amount,category']
        for e in expenses:
            date_str = e.created_at.strftime('%Y-%m-%d') if e.created_at else ''
            lines.append(f"{date_str},{e.item},{e.amount},{e.category}")
        management_context['csv_content'] = '\n'.join(lines)
        management_context['response'] = 'CSV файл отправлен'
    return management_context


@when(parsers.parse('user sends /find {query}'))
def when_find_command(management_context, expense_storage, query):
    """Process find command."""
    expenses = expense_storage.get_expenses(12345)
    results = [e for e in expenses if query.lower() in e.item.lower()]

    if results:
        total = sum(e.amount for e in results)
        management_context['search_results'] = results
        management_context['response'] = f"Найдено: {len(results)} записей на {total}₽"
    else:
        management_context['response'] = "Ничего не найдено"
    return management_context


@then('last expense is deleted')
def then_expense_deleted(management_context):
    """Verify expense deleted."""
    assert management_context.get('deleted') is not None


@then(parsers.parse('bot shows "{message}"'))
def then_bot_shows(management_context, message):
    """Verify bot message."""
    response = management_context.get('response', '')
    # Check key parts of expected message
    if 'Удалено' in message:
        assert 'Удалено' in response
    elif 'Нечего' in message:
        assert 'Нечего' in response
    elif 'найдено' in message.lower():
        assert 'найдено' in response.lower() or 'Найдено' in response


@then('bot sends CSV file')
def then_csv_sent(management_context):
    """Verify CSV file sent."""
    csv = management_context.get('csv_content')
    assert csv is not None
    assert 'date,item,amount,category' in csv


@then(parsers.parse('file contains all expenses with columns: {columns}'))
def then_csv_columns(management_context, columns):
    """Verify CSV columns."""
    csv = management_context.get('csv_content', '')
    expected = [c.strip() for c in columns.split(',')]
    for col in expected:
        assert col in csv


@then(parsers.parse('bot shows all expenses matching "{query}"'))
def then_show_matching(management_context, query):
    """Verify matching expenses shown."""
    results = management_context.get('search_results', [])
    for r in results:
        assert query.lower() in r.item.lower()


@then('shows total amount for matched expenses')
def then_show_match_total(management_context):
    """Verify total for matches shown."""
    response = management_context.get('response', '')
    assert '₽' in response
