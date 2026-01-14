"""
ElevenLabs Voice Recognition Service.
Uses ElevenLabs Speech-to-Text API for transcription.

BDD Reference: NLE-A-9
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


class ElevenLabsService:
    """ElevenLabs service for voice message transcription"""

    def __init__(self):
        self.api_key = os.getenv("ELEVENLABS_API_KEY", "")
        self.api_url = "https://api.elevenlabs.io/v1/speech-to-text"

    def _call_api(self, audio_data: bytes) -> TranscriptionResult:
        """Call ElevenLabs Speech-to-Text API"""
        if not self.api_key:
            return TranscriptionResult(
                text="",
                success=False,
                error="ElevenLabs API key not configured"
            )

        headers = {
            "xi-api-key": self.api_key,
        }

        files = {
            "file": ("audio.ogg", audio_data, "audio/ogg"),
        }

        data = {
            "model_id": "scribe_v1",
            "language_code": "ru",
        }

        try:
            with httpx.Client(timeout=60) as client:
                response = client.post(
                    self.api_url,
                    headers=headers,
                    files=files,
                    data=data
                )
                response.raise_for_status()
                result = response.json()

                text = result.get("text", "")
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
            return TranscriptionResult(
                text="",
                success=False,
                error=f"API error: {e.response.status_code}"
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
