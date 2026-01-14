# BDD Reference: NLE-A-18
Feature: Monthly Budget Management
  As a user
  I want to set and track a monthly budget
  So that I can control my spending

  Scenario: Set monthly budget
    Given user sends /budget 50000
    When command is processed
    Then budget is saved: 50000
    And bot confirms "Бюджет на месяц: 50000₽"

  Scenario: Show budget progress
    Given user has budget 50000
    And current month expenses total 30000
    When user sends /budget
    Then bot shows progress bar (60%)
    And bot shows "Потрачено: 30000₽ из 50000₽"

  Scenario: Budget warning at 80%
    Given user has budget 50000
    And current month expenses total 40000
    When user adds new expense
    Then bot shows warning "⚠️ Вы израсходовали 80% бюджета"

  Scenario: Budget exceeded
    Given user has budget 50000
    And current month expenses total 52000
    When user sends /budget
    Then bot shows "🔴 Бюджет превышен на 2000₽"
