"""
Yandex SpeechKit Voice Recognition Service.
Uses Yandex SpeechKit STT API for transcription.
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
        self.oauth_token = os.getenv("YC_TOKEN", "")
        self.folder_id = os.getenv("YC_FOLDER_ID", "")
        self.api_url = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"
        self._iam_token = None

    def _get_iam_token(self) -> Optional[str]:
        """Get IAM token from OAuth token"""
        if not self.oauth_token:
            return None

        try:
            response = httpx.post(
                "https://iam.api.cloud.yandex.net/iam/v1/tokens",
                json={"yandexPassportOauthToken": self.oauth_token},
                timeout=10
            )
            if response.status_code == 200:
                return response.json().get("iamToken")
        except Exception:
            pass
        return None

    def _call_api(self, audio_data: bytes) -> TranscriptionResult:
        """Call Yandex SpeechKit STT API"""
        if not self.oauth_token:
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

        # Get fresh IAM token
        iam_token = self._get_iam_token()
        if not iam_token:
            return TranscriptionResult(
                text="",
                success=False,
                error="Failed to get IAM token"
            )

        headers = {
            "Authorization": f"Bearer {iam_token}",
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

                if response.status_code == 200:
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
                else:
                    error_msg = response.json().get("error_message", response.text[:200])
                    return TranscriptionResult(
                        text="",
                        success=False,
                        error=f"API error {response.status_code}: {error_msg}"
                    )

        except httpx.TimeoutException:
            return TranscriptionResult(
                text="",
                success=False,
                error="Transcription timeout"
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
