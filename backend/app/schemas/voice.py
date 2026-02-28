from pydantic import BaseModel, Field


class TTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    language: str = Field(default="en")
    voice_provider: str = Field(default="elevenlabs")


class TTSResponse(BaseModel):
    provider: str
    language: str
    audio_base64: str
    audio_format: str
