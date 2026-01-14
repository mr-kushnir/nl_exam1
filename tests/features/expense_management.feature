# BDD Reference: NLE-A-19
Feature: Expense Management
  As a user
  I want to manage my expenses
  So that I can correct mistakes and export data

  Scenario: Undo last expense
    Given user has saved expenses
    When user sends /undo
    Then last expense is deleted
    And bot shows "Удалено: кофе 300₽"

  Scenario: Undo with no expenses
    Given user has no expenses
    When user sends /undo
    Then bot shows "Нечего отменять"

  Scenario: Export to CSV
    Given user has expenses for the month
    When user sends /export
    Then bot sends CSV file
    And file contains all expenses with columns: date, item, amount, category

  Scenario: Search expenses by name
    Given user has multiple expenses
    When user sends /find кофе
    Then bot shows all expenses matching "кофе"
    And shows total amount for matched expenses

  Scenario: Search with no results
    Given user has expenses
    When user sends /find unknown
    Then bot shows "Ничего не найдено"
