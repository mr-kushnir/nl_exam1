# BDD Reference: NLE-A-17
Feature: Time-based Expense Reports
  As a user
  I want to see expenses for different time periods
  So that I can track my spending over time

  Scenario: Show today's expenses
    Given user has expenses for today
    When user sends /today command
    Then bot shows list of today's expenses
    And bot shows total amount for today

  Scenario: Today with no expenses
    Given user has no expenses for today
    When user sends /today command
    Then bot shows "Сегодня расходов нет"

  Scenario: Weekly comparison
    Given user has expenses for current and previous week
    When user sends /week command
    Then bot shows current week total
    And bot shows comparison with previous week (percentage change)

  Scenario: Weekly increase
    Given current week total is 5000
    And previous week total is 4000
    When user sends /week command
    Then bot shows "На 25% больше чем на прошлой неделе"

  Scenario: Weekly decrease
    Given current week total is 3000
    And previous week total is 4000
    When user sends /week command
    Then bot shows "На 25% меньше чем на прошлой неделе"
