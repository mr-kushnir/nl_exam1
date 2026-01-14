# BDD Reference: NLE-A-15
Feature: Expense Confirmation Flow
  As a user
  I want to confirm expenses before saving
  So that I can verify the parsed data is correct

  Scenario: Show confirmation after expense input
    Given user sends message "кофе 300"
    When YaGPT parses the expense
    Then bot shows parsed data: item="кофе", amount=300, category="Еда"
    And bot shows inline buttons: "✅ Верно", "❌ Отмена", "✏️ Изменить"

  Scenario: Confirm expense saves to database
    Given user sees confirmation message with buttons
    When user clicks "✅ Верно" button
    Then expense is saved to database
    And bot confirms with message "Записано: кофе 300₽"

  Scenario: Cancel expense discards data
    Given user sees confirmation message with buttons
    When user clicks "❌ Отмена" button
    Then expense is NOT saved
    And bot shows "Отменено"

  Scenario: Edit opens category selection
    Given user sees confirmation message with buttons
    When user clicks "✏️ Изменить" button
    Then bot shows category selection keyboard
