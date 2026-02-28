import os
import requests
import logging
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Any, Union, BinaryIO, Tuple
from enum import Enum

from app.providers.base import VoiceProvider

# Configure logging
logger = logging.getLogger(__name__)


class OutputFormat(str, Enum):
    """Output format options for TTS responses."""
    WAV = "wav"
    MP3 = "mp3"
    TEXT = "text"
    JSON = "json"


class TTSResponseMode(str, Enum):
    """TTS response modes."""
    AUDIO = "audio"  # Direct audio file
    TIMESTAMP = "timestamp"  # JSON with timestamps and base64 audio


class CantoneseAIVoiceProvider(VoiceProvider):
    """
    Cantonese.ai voice provider supporting both Text-to-Speech (TTS)
    and Speech-to-Text (STT) with dual output formats (text and voice).

    Official API: https://docs.cantonese.ai/
    Specialized for Cantonese speech, grammar, and syntax.
    """

    provider_name = "cantoneseai"

    # API Configuration
    BASE_URL = "https://cantonese.ai/api"
    TTS_ENDPOINT = f"{BASE_URL}/tts"
    STT_ENDPOINT = f"{BASE_URL}/stt"

    # Supported formats
    SUPPORTED_AUDIO_FORMATS = {"wav", "mp3", "m4a", "flac", "ogg"}
    SUPPORTED_TTS_OUTPUT_FORMATS = {"wav", "mp3"}
    MAX_AUDIO_FILE_SIZE = 100 * 1024 * 1024  # 100MB limit
    MAX_TEXT_LENGTH = 5000  # Cantonese text characters

    # TTS voice options
    AVAILABLE_VOICES = {
        "default": "default",
        "female": "female",
        "male": "male"
    }

    # Frame rates for audio
    SUPPORTED_FRAME_RATES = {"16000", "24000", "48000"}
    DEFAULT_FRAME_RATE = "24000"

    def __init__(self):
        """
        Initialize Cantonese.ai provider.

        Raises:
            ValueError: If CANTONESE_AI_API_KEY environment variable is not set.
        """
        self.api_key = os.getenv("CANTONESE_AI_API_KEY")
        if not self.api_key:
            raise ValueError(
                "CANTONESE_AI_API_KEY environment variable not set. "
                "Register at https://cantonese.ai/ and set your API key."
            )

        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "CantoneseAI-VoiceProvider/2.0"
        })
        logger.info("CantoneseAIVoiceProvider initialized successfully")

    # ========================================================================
    # TEXT-TO-SPEECH (TTS) METHODS - Dual Output (Speech + Text)
    # ========================================================================

    def synthesize(
            self,
            text: str,
            voice: Optional[str] = None,
            output_format: str = "wav",
            frame_rate: str = "24000",
            should_return_timestamp: bool = False
    ) -> Union[bytes, Dict[str, Any]]:
        """
        Convert Cantonese text to speech (TTS) with optional timestamp data.

        Args:
            text (str): Cantonese text to synthesize (1-5000 characters).
                       Must be valid Cantonese characters (Traditional or Simplified).
            voice (str, optional): Voice selection. Options: "default", "female", "male".
                                  Defaults to "default".
            output_format (str): Audio output format. Options: "wav", "mp3". Default: "wav".
            frame_rate (str): Audio frame rate. Options: "16000", "24000", "48000". Default: "24000".
            should_return_timestamp (bool): If True, returns JSON with timestamps and base64 audio.
                                           If False, returns raw audio bytes.
                                           Default: False.

        Returns:
            If should_return_timestamp=False:
                bytes: Raw audio content (WAV or MP3).

            If should_return_timestamp=True:
                Dict with keys:
                    - "file": Base64-encoded audio data
                    - "request_id": Unique request identifier
                    - "srt_timestamp": SRT subtitle format with timings
                    - "timestamps": Array of {start, end, text} for each phrase

        Raises:
            ValueError: If text is empty, too long, or invalid.
            requests.exceptions.RequestException: If API call fails.

        Examples:
            >>> provider = CantoneseAIVoiceProvider()

            # Get raw audio (for playback or saving)
            >>> audio_bytes = provider.synthesize("你好，我係香港人")
            >>> with open("output.wav", "wb") as f:
            ...     f.write(audio_bytes)

            # Get audio with timestamps and metadata
            >>> result = provider.synthesize(
            ...     "你今日點呀？",
            ...     should_return_timestamp=True
            ... )
            >>> print(f"Audio request ID: {result['request_id']}")
            >>> for ts in result["timestamps"]:
            ...     print(f"{ts['text']}: {ts['start']}-{ts['end']}s")
        """
        # ====== INPUT VALIDATION ======
        if not self._validate_text_input(text):
            raise ValueError(
                f"Invalid text input. Must be 1-{self.MAX_TEXT_LENGTH} characters, "
                f"containing valid Cantonese/Chinese characters. "
                f"Received: {len(text)} characters."
            )

        if output_format.lower() not in self.SUPPORTED_TTS_OUTPUT_FORMATS:
            raise ValueError(
                f"Unsupported output format '{output_format}'. "
                f"Supported: {self.SUPPORTED_TTS_OUTPUT_FORMATS}"
            )

        voice_key = voice or "default"
        if voice_key not in self.AVAILABLE_VOICES:
            raise ValueError(
                f"Unsupported voice '{voice_key}'. "
                f"Supported: {list(self.AVAILABLE_VOICES.keys())}"
            )

        if frame_rate not in self.SUPPORTED_FRAME_RATES:
            raise ValueError(
                f"Unsupported frame rate '{frame_rate}'. "
                f"Supported: {self.SUPPORTED_FRAME_RATES}"
            )

        # ====== PREPARE REQUEST ======
        payload = {
            "api_key": self.api_key,
            "text": text,
            "language": "cantonese",
            "output_extension": output_format.lower(),
            "frame_rate": frame_rate,
            "should_return_timestamp": should_return_timestamp
        }

        # ====== MAKE API CALL ======
        try:
            logger.debug(
                f"TTS request: text_length={len(text)}, "
                f"voice={voice_key}, "
                f"format={output_format}, "
                f"with_timestamp={should_return_timestamp}"
            )

            response = self.session.post(
                self.TTS_ENDPOINT,
                json=payload,
                timeout=30
            )

            # ====== HANDLE RESPONSE ======
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "").lower()

                # If should_return_timestamp=True, response is JSON
                if should_return_timestamp or "application/json" in content_type:
                    try:
                        result = response.json()
                        logger.info(
                            f"TTS synthesis successful with timestamps. "
                            f"Request ID: {result.get('request_id')}"
                        )
                        return result
                    except ValueError as e:
                        raise ValueError(f"Failed to parse TTS JSON response: {str(e)}")

                # If should_return_timestamp=False, response is binary audio
                elif "audio" in content_type or output_format.lower() in content_type:
                    logger.info(
                        f"TTS synthesis successful. "
                        f"Audio size: {len(response.content)} bytes"
                    )
                    return response.content

                else:
                    # Try to detect if it's JSON response with base64 audio
                    try:
                        data = response.json()
                        if "file" in data:
                            import base64
                            audio_data = base64.b64decode(data["file"])
                            logger.info(f"TTS synthesis successful (decoded from JSON)")
                            return audio_data
                        return data  # Return as-is if it's valid JSON
                    except:
                        # If all else fails, return raw content
                        return response.content

            # ====== ERROR HANDLING ======
            self._handle_api_error(response, "TTS")

        except requests.exceptions.Timeout:
            raise requests.exceptions.RequestException(
                "TTS request timed out (30s). Text may be too long or service is slow."
            )
        except requests.exceptions.ConnectionError:
            raise requests.exceptions.RequestException(
                "Failed to connect to Cantonese.ai service. Check your internet connection."
            )
        except Exception as e:
            logger.error(f"Unexpected TTS error: {str(e)}")
            raise

    def synthesize_to_file(
            self,
            text: str,
            output_path: str,
            voice: Optional[str] = None,
            output_format: str = "wav"
    ) -> Dict[str, Any]:
        """
        Synthesize Cantonese text and save audio directly to file.

        Args:
            text (str): Cantonese text.
            output_path (str): Path to save audio file (e.g., "/tmp/output.wav").
            voice (str, optional): Voice selection.
            output_format (str): Audio format ("wav" or "mp3").

        Returns:
            Dict with keys:
                - "file_path": Absolute path to saved audio file
                - "file_size_bytes": Size of audio file
                - "audio_format": Format of the audio
                - "text": Original input text

        Raises:
            IOError: If file cannot be written.
            ValueError: If text or format is invalid.

        Example:
            >>> result = provider.synthesize_to_file("你好", "hello.wav")
            >>> print(f"Saved to: {result['file_path']}")
            >>> print(f"File size: {result['file_size_bytes']} bytes")
        """
        try:
            audio = self.synthesize(
                text,
                voice=voice,
                output_format=output_format,
                should_return_timestamp=False
            )

            if not isinstance(audio, bytes):
                raise TypeError("Expected bytes from synthesize(), got dict or other type")

            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with open(output_path, "wb") as f:
                f.write(audio)

            file_size = output_path.stat().st_size
            logger.info(f"Audio saved to {output_path} ({file_size} bytes)")

            return {
                "file_path": str(output_path.resolve()),
                "file_size_bytes": file_size,
                "audio_format": output_format,
                "text": text
            }

        except IOError as e:
            logger.error(f"Failed to save audio file: {str(e)}")
            raise IOError(f"Cannot write audio file to {output_path}: {str(e)}")

    def synthesize_with_metadata(
            self,
            text: str,
            voice: Optional[str] = None,
            output_format: str = "wav",
            return_srt: bool = False
    ) -> Dict[str, Any]:
        """
        Synthesize text and return both audio and metadata (timestamps, SRT format).
        Ensures DUAL OUTPUT: both speech (voice) and text metadata.

        Args:
            text (str): Cantonese text.
            voice (str, optional): Voice selection.
            output_format (str): Audio format.
            return_srt (bool): If True, include SRT subtitle format. Default: True.

        Returns:
            Dict with keys:
                - "audio": Base64-encoded audio data (for transmission/storage)
                - "audio_raw": Raw audio bytes (can be written to file)
                - "text": Original Cantonese text (TEXT OUTPUT)
                - "request_id": Unique request identifier
                - "srt_timestamp": SRT subtitle format string (if available)
                - "timestamps": Array of {start, end, text} (METADATA)
                - "frame_rate": Audio frame rate

        Example:
            >>> result = provider.synthesize_with_metadata("你今日點呀？")
            >>> # Speech output: result["audio_raw"] or result["audio"]
            >>> # Text output: result["text"]
            >>> # Metadata: result["timestamps"]
        """
        response = self.synthesize(
            text,
            voice=voice,
            output_format=output_format,
            should_return_timestamp=True
        )

        if isinstance(response, bytes):
            # Fallback if API didn't return timestamp data
            import base64
            response = {
                "file": base64.b64encode(response).decode('utf-8'),
                "text": text,
                "request_id": "unknown",
                "timestamps": [{"start": 0, "end": 0, "text": text}]
            }

        # Ensure response has all required fields
        import base64

        audio_base64 = response.get("file", "")
        try:
            audio_raw = base64.b64decode(audio_base64) if audio_base64 else b""
        except:
            audio_raw = b""

        return {
            "audio": audio_base64,  # Base64 for JSON transmission
            "audio_raw": audio_raw,  # Raw bytes for file writing
            "text": text,  # TEXT OUTPUT
            "request_id": response.get("request_id", "unknown"),
            "srt_timestamp": response.get("srt_timestamp", "") if return_srt else None,
            "timestamps": response.get("timestamps", []),  # METADATA
            "frame_rate": self.DEFAULT_FRAME_RATE
        }

    # ========================================================================
    # SPEECH-TO-TEXT (STT) METHODS - Dual Output (Text + Confidence/Metadata)
    # ========================================================================

    def transcribe(
            self,
            audio_file: Union[BinaryIO, bytes, str],
            audio_format: Optional[str] = None,
            language: str = "cantonese"
    ) -> Dict[str, Any]:
        """
        Convert Cantonese speech to text (STT).
        Ensures dual output: transcribed text + metadata/confidence.

        Args:
            audio_file (BinaryIO, bytes, or str):
                - str: File path to audio file
                - bytes: Raw audio data
                - BinaryIO: File object opened in binary mode
            audio_format (str, optional): Audio format (wav, mp3, m4a, flac, ogg).
                                         Auto-detected from file extension if not provided.
            language (str): Language code. Default: "cantonese" (yue).

        Returns:
            Dict with keys:
                - "text": Transcribed Cantonese text (TEXT OUTPUT)
                - "duration": Audio duration in seconds
                - "process_time": API processing time in milliseconds
                - "is_cached": Whether result was cached
                - "confidence": Confidence score (0-1) if available
                - "request_id": Unique request identifier
                - "language": Detected/processed language

        Raises:
            ValueError: If audio is invalid or unsupported.
            FileNotFoundError: If audio file path doesn't exist.
            requests.exceptions.RequestException: If API call fails.

        Examples:
            >>> provider = CantoneseAIVoiceProvider()

            # From file path
            >>> result = provider.transcribe("audio.wav")
            >>> print(f"Transcription: {result['text']}")

            # From file object
            >>> with open("recording.mp3", "rb") as f:
            ...     result = provider.transcribe(f)

            # From bytes
            >>> audio_bytes = b"..."
            >>> result = provider.transcribe(audio_bytes, audio_format="wav")
        """
        # ====== NORMALIZE AUDIO INPUT ======
        audio_data, detected_format = self._normalize_audio_input(
            audio_file,
            audio_format
        )

        # ====== INPUT VALIDATION ======
        if not audio_data:
            raise ValueError("Audio data is empty.")

        if len(audio_data) > self.MAX_AUDIO_FILE_SIZE:
            raise ValueError(
                f"Audio file too large. Maximum size: {self.MAX_AUDIO_FILE_SIZE / 1024 / 1024:.0f}MB. "
                f"Received: {len(audio_data) / 1024 / 1024:.2f}MB"
            )

        if detected_format not in self.SUPPORTED_AUDIO_FORMATS:
            raise ValueError(
                f"Unsupported audio format '{detected_format}'. "
                f"Supported: {self.SUPPORTED_AUDIO_FORMATS}"
            )

        # ====== PREPARE REQUEST ======
        files = {
            "data": ("audio", BytesIO(audio_data), f"audio/{detected_format}")
        }

        data = {
            "api_key": self.api_key,
            "language": language
        }

        # ====== MAKE API CALL ======
        try:
            logger.debug(
                f"STT request: audio_size={len(audio_data)}B, "
                f"format={detected_format}, "
                f"language={language}"
            )

            response = self.session.post(
                self.STT_ENDPOINT,
                files=files,
                data=data,
                timeout=120
            )

            # ====== HANDLE RESPONSE ======
            if response.status_code == 200:
                result = response.json()

                # Validate response has transcribed text
                if "text" not in result:
                    raise ValueError(
                        "Invalid response: 'text' field missing from STT result."
                    )

                logger.info(
                    f"STT transcription successful. "
                    f"Text length: {len(result.get('text', ''))} chars, "
                    f"Duration: {result.get('duration')}s"
                )

                # Ensure response has expected structure
                return {
                    "text": result.get("text", ""),  # TEXT OUTPUT
                    "duration": result.get("duration"),
                    "process_time": result.get("process_time"),
                    "is_cached": result.get("is_cached", False),
                    "confidence": result.get("confidence"),  # METADATA
                    "request_id": result.get("request_id", "unknown"),
                    "language": language
                }

            # ====== ERROR HANDLING ======
            self._handle_api_error(response, "STT")

        except requests.exceptions.Timeout:
            raise requests.exceptions.RequestException(
                "STT request timed out (120s). Audio file may be too large."
            )
        except requests.exceptions.ConnectionError:
            raise requests.exceptions.RequestException(
                "Failed to connect to Cantonese.ai service. Check your internet connection."
            )
        except ValueError as e:
            logger.error(f"STT response error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected STT error: {str(e)}")
            raise

    def transcribe_from_file(
            self,
            audio_path: str,
            **kwargs
    ) -> Dict[str, Any]:
        """
        Transcribe audio from file path (convenience method).

        Args:
            audio_path (str): Path to audio file.
            **kwargs: Additional arguments for transcribe().

        Returns:
            Dict: Transcription result with text and metadata.

        Example:
            >>> result = provider.transcribe_from_file("interview.mp3")
            >>> print(result["text"])
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        logger.debug(f"Transcribing from file: {audio_path}")
        with open(audio_path, "rb") as f:
            return self.transcribe(f, **kwargs)

    def transcribe_with_save(
            self,
            audio_file: Union[str, bytes, BinaryIO],
            output_text_path: str
    ) -> Dict[str, Any]:
        """
        Transcribe audio and save the transcribed text to a file.

        Args:
            audio_file: Audio input (file path, bytes, or file object).
            output_text_path: Path to save transcribed text file.

        Returns:
            Dict with transcription result and saved file info.

        Example:
            >>> result = provider.transcribe_with_save("audio.wav", "transcript.txt")
            >>> print(f"Transcript saved to: {result['text_file_path']}")
        """
        result = self.transcribe(audio_file)

        output_path = Path(output_text_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result["text"])

        logger.info(f"Transcription saved to {output_path}")

        return {
            **result,
            "text_file_path": str(output_path.resolve()),
            "text_file_size_bytes": output_path.stat().st_size
        }

    def batch_transcribe(
            self,
            audio_files: list,
            **kwargs
    ) -> Dict[str, Dict[str, Any]]:
        """
        Transcribe multiple audio files in batch.

        Args:
            audio_files (list): List of file paths or file objects.
            **kwargs: Additional arguments for transcribe().

        Returns:
            Dict mapping file identifiers to transcription results.

        Example:
            >>> files = ["audio1.wav", "audio2.mp3"]
            >>> results = provider.batch_transcribe(files)
            >>> for file_id, result in results.items():
            ...     print(f"{file_id}: {result['text']}")
        """
        results = {}

        for i, audio_file in enumerate(audio_files):
            try:
                file_id = (
                    Path(audio_file).name if isinstance(audio_file, str)
                    else f"audio_{i}"
                )
                results[file_id] = self.transcribe(audio_file, **kwargs)
                logger.info(f"Batch transcribe: {file_id} completed successfully")
            except Exception as e:
                logger.error(f"Batch transcribe error for {audio_file}: {str(e)}")
                results[file_id] = {
                    "error": str(e),
                    "success": False,
                    "text": ""
                }

        return results

    # ========================================================================
    # UNIFIED I/O METHOD - Get both Text and Speech Output
    # ========================================================================

    def process_dual_output(
            self,
            mode: str,
            input_data: Union[str, bytes, BinaryIO],
            **kwargs
    ) -> Dict[str, Any]:
        """
        Universal method to process input and return DUAL OUTPUT (text + speech).

        Args:
            mode (str): "tts" for text-to-speech or "stt" for speech-to-text.
            input_data: Input data (text for TTS, audio for STT).
            **kwargs: Additional parameters specific to TTS/STT.

        Returns:
            Dict with dual outputs:
                - TTS: {"audio": bytes, "text": original_text, "metadata": {...}}
                - STT: {"text": transcribed_text, "audio_analyzed": metadata, ...}

        Examples:
            >>> # TTS: Input text, get both audio and text info
            >>> result = provider.process_dual_output("tts", "你好")
            >>> audio = result["audio"]  # Voice output
            >>> original_text = result["text"]  # Text output

            >>> # STT: Input audio, get transcribed text
            >>> result = provider.process_dual_output("stt", "audio.wav")
            >>> transcribed_text = result["text"]  # Text output
        """
        if mode.lower() == "tts":
            return self.synthesize_with_metadata(input_data, **kwargs)

        elif mode.lower() == "stt":
            return self.transcribe(input_data, **kwargs)

        else:
            raise ValueError(f"Invalid mode '{mode}'. Use 'tts' or 'stt'.")

    # ========================================================================
    # UTILITY / HELPER METHODS
    # ========================================================================

    def _validate_text_input(self, text: str) -> bool:
        """
        Validate Cantonese text input.

        Returns:
            bool: True if text is valid, False otherwise.
        """
        if not isinstance(text, str):
            return False

        text = text.strip()
        if not text or len(text) > self.MAX_TEXT_LENGTH:
            return False

        # Allow Chinese characters, English, numbers, and common punctuation
        import re
        # This regex accepts: CJK characters, Latin, digits, spaces, and common punctuation
        valid_pattern = (
            r'^[\u4e00-\u9fff\u3400-\u4dbf'  # CJK Unified Ideographs + CJK Extension A
            r'\u3040-\u309f\u30a0-\u30ff'  # Hiragana + Katakana
            r'a-zA-Z0-9\s\.\,\!\?\：\；\「\」\『\』'
            r'\（\）\，\。\？\！\：\；\—\·\—\-\*\'\"\、\;:,()\[\]{{}}<>\/\\@#\$%\^&\+=\|~`!]+$'
        )
        return bool(re.match(valid_pattern, text))

    def _normalize_audio_input(
            self,
            audio_file: Union[BinaryIO, bytes, str],
            audio_format: Optional[str]
    ) -> Tuple[bytes, str]:
        """
        Normalize audio input to bytes and detect format.

        Args:
            audio_file: Audio input (file path, bytes, or file object).
            audio_format: Optional explicit format.

        Returns:
            Tuple of (audio_bytes, detected_format_lowercase)

        Raises:
            TypeError: If audio_file type is unsupported.
            FileNotFoundError: If file path doesn't exist.
        """
        audio_data = None
        detected_format = audio_format

        # Handle string (file path)
        if isinstance(audio_file, str):
            file_path = Path(audio_file)
            if not file_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file}")

            # Auto-detect format from extension
            if not detected_format:
                detected_format = file_path.suffix.lstrip(".").lower()

            with open(file_path, "rb") as f:
                audio_data = f.read()

        # Handle bytes
        elif isinstance(audio_file, bytes):
            audio_data = audio_file
            if not detected_format:
                detected_format = "wav"  # Default to WAV for raw bytes

        # Handle file-like object (BinaryIO)
        elif hasattr(audio_file, "read"):
            audio_data = audio_file.read()
            if isinstance(audio_data, str):
                audio_data = audio_data.encode()

            # Try to get format from file object name
            if not detected_format and hasattr(audio_file, "name"):
                detected_format = Path(audio_file.name).suffix.lstrip(".").lower()

        else:
            raise TypeError(
                f"Unsupported audio_file type: {type(audio_file).__name__}. "
                "Must be: str (file path), bytes, or file-like object (BinaryIO)."
            )

        # Fallback format
        if not detected_format:
            detected_format = "wav"

        return audio_data, detected_format.lower()

    def _handle_api_error(self, response: requests.Response, service: str) -> None:
        """
        Handle API errors with descriptive messages.

        Args:
            response: API response object.
            service: Service name ("TTS" or "STT").

        Raises:
            requests.exceptions.RequestException with descriptive message.
        """
        status_code = response.status_code

        # Try to extract error message from response
        try:
            error_data = response.json()
            error_msg = error_data.get(
                "message",
                error_data.get("error", str(error_data))
            )
        except:
            error_msg = response.text or "Unknown error"

        # Map status codes to user-friendly messages
        error_messages = {
            400: f"{service} Bad Request: {error_msg}. Check your input parameters.",
            401: "Unauthorized: Invalid API key. Check CANTONESE_AI_API_KEY environment variable.",
            403: "Forbidden: You don't have permission to access this resource.",
            413: f"{service} Payload Too Large: File/text exceeds size limit.",
            415: f"{service} Unsupported Media Type: Check audio format or content type.",
            422: f"{service} Unprocessable Entity: {error_msg}",
            429: "Too Many Requests: Rate limit exceeded. Please try again later.",
            500: "Cantonese.ai Server Error: Internal server error occurred.",
            503: "Service Unavailable: Cantonese.ai service is temporarily down."
        }

        message = error_messages.get(
            status_code,
            f"{service} API Error (HTTP {status_code}): {error_msg}"
        )

        logger.error(f"{service} API Error: {message}")
        raise requests.exceptions.RequestException(message)

    def health_check(self) -> bool:
        """
        Check if Cantonese.ai API is accessible and API key is valid.

        Returns:
            bool: True if API is accessible, False otherwise.

        Example:
            >>> provider = CantoneseAIVoiceProvider()
            >>> if provider.health_check():
            ...     print("API is accessible")
            >>> else:
            ...     print("API is unavailable")
        """
        try:
            # Simple test request with minimal data
            test_payload = {
                "api_key": self.api_key,
                "text": "test",
                "language": "cantonese",
                "output_extension": "wav",
                "should_return_timestamp": False
            }

            response = self.session.post(
                self.TTS_ENDPOINT,
                json=test_payload,
                timeout=5
            )

            is_healthy = response.status_code in [200, 400, 422]  # 400/422 = bad input, but API is up

            if is_healthy:
                logger.info("Health check: API is accessible")
            else:
                logger.warning(f"Health check: API returned {response.status_code}")

            return is_healthy

        except Exception as e:
            logger.warning(f"Health check failed: {str(e)}")
            return False
