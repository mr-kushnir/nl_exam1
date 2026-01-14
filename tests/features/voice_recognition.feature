# BDD Reference: NLE-A-9
Feature: Voice Message Processing
  Распознавание голосовых сообщений через ElevenLabs

  Scenario: Transcribe voice message
    Given user sends voice message with audio
    When ElevenLabs processes audio
    Then return text transcription

  Scenario: Handle Russian speech
    Given voice message in Russian
    When transcription completes
    Then text is in Russian
    And passed to YaGPT for parsing

  Scenario: Handle poor audio quality
    Given voice message with noise
    When transcription fails
    Then return error message
    And suggest text input
