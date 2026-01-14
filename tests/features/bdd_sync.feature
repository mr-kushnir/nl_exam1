Feature: BDD Synchronization
  Ensure KB articles and local .feature files are in sync
  and all step definitions are properly implemented

  Scenario: Sync expense_parsing.feature with KB
    Given KB article NLE-A-8 contains BDD scenarios
    When I compare with tests/features/expense_parsing.feature
    Then they should be identical
    And all step definitions should be implemented

  Scenario: Sync expense_storage.feature with KB
    Given KB article NLE-A-10 contains BDD scenarios
    When I compare with tests/features/expense_storage.feature
    Then they should be identical
    And all step definitions should be implemented

  Scenario: Sync telegram_bot.feature with KB
    Given KB article NLE-A-11 contains BDD scenarios
    When I compare with tests/features/telegram_bot.feature
    Then they should be identical
    And all step definitions should be implemented

  Scenario: All BDD tests pass
    Given all .feature files are synced with KB
    And all step definitions are implemented
    When I run pytest tests/steps/ -v
    Then all 13 scenarios should pass
