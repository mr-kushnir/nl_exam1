Feature: Expense Parsing with YaGPT
  As a user of the expense tracker bot
  I want to send natural language messages about expenses
  So that the bot can automatically parse and categorize them

  Scenario: Parse simple expense message
    Given I have a YaGPT service
    When I send message "кофе 300"
    Then the expense should be parsed with item "кофе" and amount 300

  Scenario: Parse expense with category hint
    Given I have a YaGPT service
    When I send message "такси до работы 500"
    Then the expense should be parsed with item "такси" and amount 500
    And the category should be "transport"

  Scenario: Handle invalid expense message
    Given I have a YaGPT service
    When I send message "привет"
    Then the expense should not be parsed

  Scenario: Detect add expense intent
    Given I have a YaGPT service
    When I send message "потратил на обед 450"
    Then the intent should be "add_expense"

  Scenario: Detect monthly report intent
    Given I have a YaGPT service
    When I send message "покажи расходы за месяц"
    Then the intent should be "report_monthly"
