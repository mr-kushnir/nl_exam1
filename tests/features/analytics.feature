# BDD Reference: NLE-A-20
Feature: Analytics and Visualization
  As a user
  I want to see visual analytics
  So that I can understand my spending patterns

  Scenario: ASCII chart in monthly report
    Given user has expenses in multiple categories
    When user sends "расходы"
    Then bot shows ASCII bar chart
      """
      Еда         ████████████████ 15000₽
      Транспорт   █████            5000₽
      Развлечения ███              3000₽
      """

  Scenario: Day-of-week statistics
    Given user has expenses across multiple weeks
    When user sends /stats days
    Then bot shows average spending per day of week
    And highlights the highest spending day

  Scenario: Recurring expense suggestion
    Given user adds expense "netflix 699"
    And same expense was added last month
    When expense is saved
    Then bot suggests "Сделать регулярным расходом?"
    And shows inline button "Да, каждый месяц"

  Scenario: Recurring expense reminder
    Given user has recurring expense (rent, 1st of month)
    When it is the 1st of the month
    Then bot sends reminder "Напоминание: Аренда 25000₽"
    And shows button "Записать"
