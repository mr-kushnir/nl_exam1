"""
Tests for Yandex SpeechKit Voice Service
BDD Reference: NLE-A-9
"""
import pytest
from unittest.mock import Mock, patch
from src.services.speech_service import SpeechService, TranscriptionResult


class TestSpeechService:
    """Feature: Voice Message Processing with Yandex SpeechKit"""

    @pytest.fixture
    def service(self):
        return SpeechService()

    def test_transcribe_voice_message(self, service):
        """Scenario: Transcribe voice message
        Given user sends voice message with audio
        When SpeechKit processes audio
        Then return text transcription
        """
        audio_data = b"fake_audio_data"

        with patch.object(service, '_call_api') as mock_api:
            mock_api.return_value = TranscriptionResult(text="кофе 300", success=True)
            result = service.transcribe(audio_data)

        assert result.success is True
        assert result.text == "кофе 300"

    def test_handle_russian_speech(self, service):
        """Scenario: Handle Russian speech
        Given voice message in Russian
        When transcription completes
        Then text is in Russian
        """
        audio_data = b"fake_russian_audio"

        with patch.object(service, '_call_api') as mock_api:
            mock_api.return_value = TranscriptionResult(text="такси до работы", success=True)
            result = service.transcribe(audio_data)

        assert result.success is True
        # Check for Cyrillic characters
        assert any('\u0400' <= c <= '\u04FF' for c in result.text)

    def test_handle_poor_audio_quality(self, service):
        """Scenario: Handle poor audio quality
        Given voice message with noise
        When transcription fails
        Then return error message
        """
        audio_data = b"noisy_audio"

        with patch.object(service, '_call_api') as mock_api:
            mock_api.return_value = TranscriptionResult(
                text="",
                success=False,
                error="Could not transcribe audio"
            )
            result = service.transcribe(audio_data)

        assert result.success is False
        assert result.error is not None

    def test_get_error_message(self, service):
        """Test error message generation"""
        error_msg = service.get_error_message()
        assert "текст" in error_msg.lower() or "голосов" in error_msg.lower()

    def test_transcribe_empty_audio(self, service):
        """Scenario: Handle empty audio data
        Given empty audio data
        When trying to transcribe
        Then return error
        """
        result = service.transcribe(b"")
        assert result.success is False
        assert "No audio data" in result.error

    def test_transcribe_none_audio(self, service):
        """Scenario: Handle None audio data
        Given None as audio data
        When trying to transcribe
        Then return error
        """
        result = service.transcribe(None)
        assert result.success is False
