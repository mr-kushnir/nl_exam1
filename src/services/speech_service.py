"""
Yandex SpeechKit Voice Recognition Service.
Uses Yandex SpeechKit STT API for transcription.

Replaces ElevenLabs for better Yandex Cloud integration.
"""
import os
import httpx
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class TranscriptionResult:
    """Result of voice transcription"""
    text: str
    success: bool
    error: Optional[str] = None


class SpeechService:
    """Yandex SpeechKit service for voice message transcription"""

    def __init__(self):
        self.api_key = os.getenv("YC_TOKEN", "")
        self.folder_id = os.getenv("YC_FOLDER_ID", "")
        self.api_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"

    def _call_api(self, audio_data: bytes) -> TranscriptionResult:
        """Call Yandex SpeechKit STT API"""
        if not self.api_key:
            return TranscriptionResult(
                text="",
                success=False,
                error="Yandex Cloud token not configured"
            )

        if not self.folder_id:
            return TranscriptionResult(
                text="",
                success=False,
                error="Yandex Cloud folder ID not configured"
            )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

        params = {
            "folderId": self.folder_id,
            "lang": "ru-RU",
            "format": "oggopus",  # Telegram sends OGG Opus
        }

        try:
            with httpx.Client(timeout=30) as client:
                response = client.post(
                    self.api_url,
                    headers=headers,
                    params=params,
                    content=audio_data
                )
                response.raise_for_status()
                result = response.json()

                text = result.get("result", "")
                if text:
                    return TranscriptionResult(text=text, success=True)
                else:
                    return TranscriptionResult(
                        text="",
                        success=False,
                        error="Empty transcription result"
                    )

        except httpx.TimeoutException:
            return TranscriptionResult(
                text="",
                success=False,
                error="Transcription timeout"
            )
        except httpx.HTTPStatusError as e:
            error_text = e.response.text[:200] if e.response else str(e)
            return TranscriptionResult(
                text="",
                success=False,
                error=f"API error {e.response.status_code}: {error_text}"
            )
        except Exception as e:
            return TranscriptionResult(
                text="",
                success=False,
                error=f"Transcription failed: {str(e)}"
            )

    def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """Transcribe audio data to text"""
        if not audio_data:
            return TranscriptionResult(
                text="",
                success=False,
                error="No audio data provided"
            )

        return self._call_api(audio_data)

    def get_error_message(self) -> str:
        """Get user-friendly error message when transcription fails"""
        return (
            "🎙 Не удалось распознать голосовое сообщение.\n"
            "Попробуйте записать ещё раз или напишите текстом.\n\n"
            "Пример: кофе 300"
        )
