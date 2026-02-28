import base64
import logging

from fastapi import APIRouter, HTTPException

from app.providers.router import ProviderRouter
from app.core.settings import settings
from app.schemas.voice import TTSRequest, TTSResponse

logger = logging.getLogger(__name__)
router = APIRouter()
provider_router = ProviderRouter(settings)


@router.post("/voice/tts", response_model=TTSResponse)
def text_to_speech(payload: TTSRequest) -> TTSResponse:
    voice_provider = provider_router.resolve_voice_provider(payload.voice_provider)
    if voice_provider is None:
        raise HTTPException(
            status_code=503,
            detail=f"Voice provider '{payload.voice_provider}' is not available. "
                   "Check that the provider is enabled and API key is configured.",
        )

    audio_bytes = voice_provider.synthesize(payload.text, language=payload.language)
    if not audio_bytes:
        raise HTTPException(
            status_code=502,
            detail="Voice provider returned empty audio. The upstream service may be unavailable.",
        )

    audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
    audio_format = "mp3" if payload.voice_provider == "elevenlabs" else "wav"

    logger.info(
        "voice_tts_success provider=%s language=%s bytes=%d",
        payload.voice_provider,
        payload.language,
        len(audio_bytes),
    )

    return TTSResponse(
        provider=payload.voice_provider,
        language=payload.language,
        audio_base64=audio_b64,
        audio_format=audio_format,
    )
