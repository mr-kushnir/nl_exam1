Feature: Telegram Bot Handlers
  As a Telegram user
  I want to interact with the expense tracker bot
  So that I can manage my expenses through chat

  Scenario: Handle start command
    Given I have a bot handler
    When user 123 sends "/start"
    Then the bot should respond with a welcome message

  Scenario: Handle expense message
    Given I have a bot handler
    When user 123 sends "кофе 300"
    Then the bot should parse the expense
    And save it to storage
    And respond with confirmation

  Scenario: Handle report request
    Given I have a bot handler
    And user 123 has saved expenses
    When user 123 sends "отчет за месяц"
    Then the bot should respond with expense report

  Scenario: Handle unknown message
    Given I have a bot handler
    When user 123 sends "что ты умеешь?"
    Then the bot should respond with help message
