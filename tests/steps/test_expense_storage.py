"""Step definitions for Expense Storage feature."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from datetime import datetime

# Load scenarios from .feature file
scenarios('../features/expense_storage.feature')


@pytest.fixture
def storage_context():
    """Context for storage tests."""
    return {}


@given('I have an expense storage')
def given_expense_storage(expense_storage, storage_context):
    """Set up expense storage."""
    storage_context['storage'] = expense_storage
    return storage_context


@given(parsers.parse('user {user_id:d} has saved expenses for this month'))
def given_user_has_expenses(storage_context, user_id):
    """Pre-populate expenses for user."""
    from src.services.expense_storage import Expense
    storage = storage_context['storage']
    expenses = [
        Expense(user_id=user_id, item='кофе', amount=300, category='food'),
        Expense(user_id=user_id, item='такси', amount=500, category='transport'),
    ]
    for exp in expenses:
        storage.save_expense(exp)
    storage_context['user_id'] = user_id


@given(parsers.parse('user {user_id:d} has expenses in different categories'))
def given_user_has_categorized_expenses(storage_context, user_id):
    """Pre-populate categorized expenses."""
    from src.services.expense_storage import Expense
    storage = storage_context['storage']
    expenses = [
        Expense(user_id=user_id, item='кофе', amount=300, category='food'),
        Expense(user_id=user_id, item='обед', amount=450, category='food'),
        Expense(user_id=user_id, item='такси', amount=500, category='transport'),
    ]
    for exp in expenses:
        storage.save_expense(exp)
    storage_context['user_id'] = user_id


@given(parsers.parse('user {user_id:d} has multiple expenses for "{item}"'))
def given_user_has_item_expenses(storage_context, user_id, item):
    """Pre-populate item expenses."""
    from src.services.expense_storage import Expense
    storage = storage_context['storage']
    expenses = [
        Expense(user_id=user_id, item=item, amount=300, category='food'),
        Expense(user_id=user_id, item=item, amount=250, category='food'),
        Expense(user_id=user_id, item=item, amount=350, category='food'),
    ]
    for exp in expenses:
        storage.save_expense(exp)
    storage_context['user_id'] = user_id
    storage_context['item'] = item


@when(parsers.parse('I save expense "{item}" with amount {amount:d} for user {user_id:d}'))
def when_save_expense(storage_context, item, amount, user_id):
    """Save an expense."""
    from src.services.expense_storage import Expense
    storage = storage_context['storage']
    expense = Expense(user_id=user_id, item=item, amount=amount, category='food')
    storage_context['result'] = storage.save_expense(expense)
    storage_context['user_id'] = user_id


@when(parsers.parse('I request monthly expenses for user {user_id:d}'))
def when_request_monthly(storage_context, user_id):
    """Request monthly expenses."""
    storage = storage_context['storage']
    storage_context['expenses'] = storage.get_monthly_expenses(user_id)


@when(parsers.parse('I request category totals for user {user_id:d}'))
def when_request_category_totals(storage_context, user_id):
    """Request category totals."""
    storage = storage_context['storage']
    storage_context['totals'] = storage.get_category_totals(user_id)


@when(parsers.parse('I request total for item "{item}" for user {user_id:d}'))
def when_request_item_total(storage_context, item, user_id):
    """Request item total."""
    storage = storage_context['storage']
    storage_context['item_total'] = storage.get_item_total(user_id, item)


@then('the expense should be saved successfully')
def then_expense_saved(storage_context):
    """Verify expense was saved."""
    assert storage_context['result'] is True


@then('I should receive a list of expenses')
def then_receive_expenses(storage_context):
    """Verify expenses list returned."""
    expenses = storage_context['expenses']
    assert isinstance(expenses, list)
    assert len(expenses) > 0


@then('I should receive totals grouped by category')
def then_receive_category_totals(storage_context):
    """Verify category totals."""
    totals = storage_context['totals']
    assert isinstance(totals, dict)
    assert 'food' in totals
    assert totals['food'] == 750  # 300 + 450


@then(parsers.parse('I should receive the sum of all "{item}" expenses'))
def then_receive_item_total(storage_context, item):
    """Verify item total."""
    total = storage_context['item_total']
    assert total == 900  # 300 + 250 + 350
