Feature: Expense Storage
  As a user of the expense tracker bot
  I want my expenses to be saved and retrieved
  So that I can track my spending over time

  Scenario: Save new expense
    Given I have an expense storage
    When I save expense "кофе" with amount 300 for user 123
    Then the expense should be saved successfully

  Scenario: Get monthly expenses
    Given I have an expense storage
    And user 123 has saved expenses for this month
    When I request monthly expenses for user 123
    Then I should receive a list of expenses

  Scenario: Get category totals
    Given I have an expense storage
    And user 123 has expenses in different categories
    When I request category totals for user 123
    Then I should receive totals grouped by category

  Scenario: Get item total
    Given I have an expense storage
    And user 123 has multiple expenses for "кофе"
    When I request total for item "кофе" for user 123
    Then I should receive the sum of all "кофе" expenses
