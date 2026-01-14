"""Step definitions for Expense Parsing feature."""
import pytest
from pytest_bdd import scenarios, given, when, then, parsers

# Load scenarios from .feature file
scenarios('../features/expense_parsing.feature')


@pytest.fixture
def parsing_context():
    """Context for parsing tests."""
    return {}


@given('I have a YaGPT service')
def given_yagpt_service(yagpt_service, parsing_context):
    """Set up YaGPT service."""
    parsing_context['service'] = yagpt_service
    return parsing_context


@when(parsers.parse('I send message "{message}"'))
def when_send_message(parsing_context, message):
    """Send message for parsing."""
    service = parsing_context['service']
    parsing_context['message'] = message
    parsing_context['parsed'] = service.parse_expense(message)
    parsing_context['intent'] = service.detect_intent(message)
    return parsing_context


@then(parsers.parse('the expense should be parsed with item "{item}" and amount {amount:d}'))
def then_expense_parsed(parsing_context, item, amount):
    """Verify expense was parsed correctly."""
    parsed = parsing_context['parsed']
    assert parsed is not None, "Expense was not parsed"
    assert parsed.item == item
    assert parsed.amount == amount


@then(parsers.parse('the category should be "{category}"'))
def then_category_is(parsing_context, category):
    """Verify category."""
    parsed = parsing_context['parsed']
    assert parsed.category == category


@then('the expense should not be parsed')
def then_expense_not_parsed(parsing_context):
    """Verify expense was not parsed."""
    parsed = parsing_context['parsed']
    assert parsed is None, f"Expected None but got {parsed}"


@then(parsers.parse('the intent should be "{intent}"'))
def then_intent_is(parsing_context, intent):
    """Verify detected intent."""
    detected = parsing_context['intent']
    assert detected.type == intent
