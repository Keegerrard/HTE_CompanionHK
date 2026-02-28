import pytest

from app.providers.elevenlabs import ElevenLabsVoiceProvider


class FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        content: bytes = b"",
        json_data: dict | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self.content = content
        self._json_data = json_data
        self.text = text

    def json(self) -> dict:
        if self._json_data is None:
            raise ValueError("No JSON payload")
        return self._json_data


def test_synthesize_includes_output_format_query(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    provider = ElevenLabsVoiceProvider()
    captured: dict = {}

    def fake_post(
        url: str,
        *,
        params: dict,
        json: dict,
        headers: dict,
        timeout: int,
    ) -> FakeResponse:
        captured["url"] = url
        captured["params"] = params
        captured["json"] = json
        captured["headers"] = headers
        captured["timeout"] = timeout
        return FakeResponse(status_code=200, content=b"audio-bytes")

    monkeypatch.setattr("app.providers.elevenlabs.requests.post", fake_post)
    audio = provider.synthesize("Hello world", language="en")

    assert audio == b"audio-bytes"
    assert captured["params"]["output_format"] == "mp3_44100_128"
    assert captured["json"]["language_code"] == "en"


def test_transcribe_uses_language_code_and_wav_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    provider = ElevenLabsVoiceProvider()
    captured: dict = {}
    wav_bytes = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 16

    def fake_post(
        url: str,
        *,
        files: dict,
        data: dict,
        headers: dict,
        timeout: int,
    ) -> FakeResponse:
        captured["url"] = url
        captured["files"] = files
        captured["data"] = data
        captured["headers"] = headers
        captured["timeout"] = timeout
        return FakeResponse(
            status_code=200,
            json_data={"text": "transcribed", "language_code": "en"},
        )

    monkeypatch.setattr("app.providers.elevenlabs.requests.post", fake_post)
    text = provider.transcribe(wav_bytes, language="en")

    assert text == "transcribed"
    assert "language_code" in captured["data"]
    assert captured["data"]["language_code"] == "en"
    assert "language" not in captured["data"]
    file_name, file_content, file_content_type = captured["files"]["file"]
    assert file_name == "audio.wav"
    assert file_content == wav_bytes
    assert file_content_type == "audio/wav"


def test_transcribe_omits_language_code_for_unsupported_hint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ELEVENLABS_API_KEY", "test-key")
    provider = ElevenLabsVoiceProvider()
    captured: dict = {}

    def fake_post(
        url: str,
        *,
        files: dict,
        data: dict,
        headers: dict,
        timeout: int,
    ) -> FakeResponse:
        _ = (url, files, headers, timeout)
        captured["data"] = data
        return FakeResponse(
            status_code=200,
            json_data={"text": "ok", "language_code": "en"},
        )

    monkeypatch.setattr("app.providers.elevenlabs.requests.post", fake_post)
    text = provider.transcribe(b"ID3\x00\x00\x00\x00", language="xx")

    assert text == "ok"
    assert captured["data"] == {"model_id": "scribe_v2"}
