import logging
import os
from typing import Any

import requests

from app.providers.base import VoiceProvider

logger = logging.getLogger(__name__)

# Supported languages mapping (ISO 639-1 codes)
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "ru": "Russian",
    "ja": "Japanese",
    "zh": "Chinese",
    "ko": "Korean",
    "ar": "Arabic",
    "hi": "Hindi",
    "tr": "Turkish",
    "pl": "Polish",
    "vi": "Vietnamese",
    "th": "Thai",
    "id": "Indonesian",
    "fa": "Persian",
    "ur": "Urdu",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "cs": "Czech",
    "hu": "Hungarian",
    "ro": "Romanian",
    "el": "Greek",
    "uk": "Ukrainian",
    "he": "Hebrew",
}


class ElevenLabsVoiceProvider(VoiceProvider):
    """ElevenLabs Voice Provider with TTS and STT capabilities."""

    provider_name = "elevenlabs"

    def __init__(self) -> None:
        self.api_key = os.getenv("ELEVENLABS_API_KEY")
        if not self.api_key:
            logger.warning("ELEVENLABS_API_KEY environment variable not set")

        self.base_url = "https://api.elevenlabs.io/v1"
        self.tts_model = "eleven_multilingual_v2"
        self.stt_model = "scribe_v2"
        self.default_voice_id = os.getenv(
            "ELEVENLABS_DEFAULT_VOICE_ID",
            "21m00Tcm4TlvDq8ikWAM",
        )
        self.output_format = "mp3_44100_128"

    def synthesize(
        self,
        text: str,
        language: str = "en",
        voice_id: str | None = None,
    ) -> bytes:
        if not self.api_key:
            logger.error("ELEVENLABS_API_KEY not configured")
            return b""

        if not text or not text.strip():
            logger.warning("Empty text provided for synthesis")
            return b""

        selected_voice_id = voice_id or self.default_voice_id

        try:
            url = f"{self.base_url}/text-to-speech/{selected_voice_id}"
            headers = {"xi-api-key": self.api_key,
                       "Content-Type": "application/json"}
            payload = {
                "text": text,
                "model_id": self.tts_model,
                "language_code": language,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            }
            params = {"output_format": self.output_format}

            response = requests.post(
                url,
                params=params,
                json=payload,
                headers=headers,
                timeout=30,
            )

            if response.status_code == 200:
                logger.info("Successfully synthesized text in %s", language)
                return response.content

            logger.error("TTS API error: %s - %s",
                         response.status_code, response.text)
            return b""

        except requests.exceptions.Timeout:
            logger.error("TTS request timeout")
            return b""
        except requests.exceptions.RequestException as exc:
            logger.error("TTS request failed: %s", str(exc))
            return b""
        except Exception as exc:  # pragma: no cover
            logger.error("Unexpected error in synthesize: %s", str(exc))
            return b""

    def transcribe(self, audio_bytes: bytes, language: str | None = None) -> str:
        if not self.api_key:
            logger.error("ELEVENLABS_API_KEY not configured")
            return ""

        if not audio_bytes:
            logger.warning("Empty audio provided for transcription")
            return ""

        file_name, content_type = self._guess_audio_upload_metadata(
            audio_bytes)

        try:
            url = f"{self.base_url}/speech-to-text"
            headers = {"xi-api-key": self.api_key}
            files = {"file": (file_name, audio_bytes, content_type)}
            data: dict[str, str] = {"model_id": self.stt_model}

            if language:
                if self.is_language_supported(language):
                    data["language_code"] = language
                else:
                    logger.warning(
                        "Unsupported language code '%s' for STT hint; using auto detect",
                        language,
                    )

            response = requests.post(
                url,
                files=files,
                data=data,
                headers=headers,
                timeout=60,
            )

            if response.status_code == 200:
                result: dict[str, Any] = response.json()
                transcribed_text = result.get("text", "")
                detected_language = (
                    result.get("language_code")
                    or result.get("language")
                    or "unknown"
                )
                logger.info(
                    "Successfully transcribed audio (detected: %s)",
                    detected_language,
                )
                return transcribed_text

            logger.error("STT API error: %s - %s",
                         response.status_code, response.text)
            return ""

        except requests.exceptions.Timeout:
            logger.error("STT request timeout")
            return ""
        except requests.exceptions.RequestException as exc:
            logger.error("STT request failed: %s", str(exc))
            return ""
        except Exception as exc:  # pragma: no cover
            logger.error("Unexpected error in transcribe: %s", str(exc))
            return ""

    def process_input(
        self,
        input_data: str | bytes,
        input_type: str = "text",
        input_language: str = "en",
    ) -> tuple[str, bytes]:
        try:
            if input_type == "audio":
                if not isinstance(input_data, bytes):
                    logger.error("Audio input must be bytes")
                    return "", b""
                extracted_text = self.transcribe(input_data, input_language)
            elif input_type == "text":
                if not isinstance(input_data, str):
                    logger.error("Text input must be string")
                    return "", b""
                extracted_text = input_data.strip()
            else:
                logger.error("Unknown input type: %s", input_type)
                return "", b""

            if not extracted_text:
                logger.warning("No text extracted from %s input", input_type)
                return "", b""

            audio_output = self.synthesize(
                extracted_text, language=input_language)
            return extracted_text, audio_output

        except Exception as exc:  # pragma: no cover
            logger.error("Error in process_input: %s", str(exc))
            return "", b""

    def get_supported_languages(self) -> dict[str, str]:
        return SUPPORTED_LANGUAGES.copy()

    def is_language_supported(self, language_code: str) -> bool:
        return language_code in SUPPORTED_LANGUAGES

    def _guess_audio_upload_metadata(self, audio_bytes: bytes) -> tuple[str, str]:
        if len(audio_bytes) >= 12 and audio_bytes[:4] == b"RIFF" and audio_bytes[8:12] == b"WAVE":
            return "audio.wav", "audio/wav"
        if audio_bytes.startswith(b"ID3") or audio_bytes.startswith(b"\xff\xfb") or audio_bytes.startswith(b"\xff\xf3") or audio_bytes.startswith(b"\xff\xf2"):
            return "audio.mp3", "audio/mpeg"
        if audio_bytes.startswith(b"OggS"):
            return "audio.ogg", "audio/ogg"
        if audio_bytes.startswith(b"fLaC"):
            return "audio.flac", "audio/flac"
        if len(audio_bytes) >= 12 and audio_bytes[4:8] == b"ftyp":
            return "audio.m4a", "audio/mp4"
        return "audio.bin", "application/octet-stream"
