Feature: Integration Testing
  Test bot components with real external APIs

  Scenario: YaGPT API integration
    Given YaGPT API credentials are configured
    When I send expense message to YaGPT
    Then I should receive parsed expense response
    And response should contain item, amount, category

  Scenario: ElevenLabs API integration
    Given ElevenLabs API credentials are configured
    When I send audio data for transcription
    Then I should receive transcribed text
    And text should be in Russian

  Scenario: YDB database integration
    Given YDB connection is configured
    When I save and retrieve expense
    Then data should be persisted correctly

  Scenario: End-to-end bot flow
    Given all services are configured
    When user sends expense message
    Then bot should parse, save, and confirm
