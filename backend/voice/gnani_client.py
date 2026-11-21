import json
import logging
import asyncio
import inspect
from typing import AsyncGenerator, Optional, Dict, Any
import websockets
try:
    from websockets.asyncio.client import ClientConnection
except ImportError:
    from websockets.client import WebSocketClientProtocol as ClientConnection

from backend.voice.config import config, SUPPORTED_LANGUAGES, SPECIAL_STT_MODES
from backend.voice.medical_vocabulary import get_formatted_keyterms_header

logger = logging.getLogger("voice.gnani_client")

class GnaniPrismaClient:
    """
    Client for Gnani Prisma v3.0 Real-time Speech-to-Text Streaming API.
    Official Endpoint: wss://api.vachana.ai/stt/v3/stream
    Audio format: Raw PCM 16-bit little-endian, 16000 Hz, mono.
    Authentication & config: Passed as WebSocket upgrade headers.
    Supports all 10 documented Indian languages & 'indic-auto' Automatic Language Detection.
    Optimized for rural healthcare with clinical keyterm boosting and code-mix mode.
    """

    def __init__(
        self,
        language_code: Optional[str] = None,
        stt_format: Optional[str] = None,
        candidate_languages: Optional[str] = None,
        enable_keyterms: bool = True,
        domain: Optional[str] = None,
        max_keyterms: int = 25
    ):
        self.api_key = config.gnani_api_key.strip()
        self.websocket_url = config.gnani_websocket_url.strip()
        self.model = config.gnani_model  # prisma-v3.0
        
        raw_lang = (language_code or config.default_language).strip()
        if raw_lang in SUPPORTED_LANGUAGES or raw_lang in SPECIAL_STT_MODES:
            self.language_code = raw_lang
        else:
            self.language_code = "indic-auto"

        # Transcription format:
        # Code-mix mode preserves English medical terms in native speech
        # Transcribe mode gives clean native-script output
        if stt_format:
            self.stt_format = stt_format
        elif "en" in self.language_code and ("kn" in self.language_code or "hi" in self.language_code):
            self.stt_format = "codemix"
        else:
            self.stt_format = "transcribe"

        self.candidate_languages = candidate_languages or "kn-IN,en-IN,hi-IN"
        self.enable_keyterms = enable_keyterms
        if enable_keyterms:
            raw_keyterms = get_formatted_keyterms_header(domain=domain, max_terms=max_keyterms)
            # Strict ASCII validation: prevent HTTP header parse errors (RFC 7230)
            clean_ascii = "".join(c for c in raw_keyterms if 32 <= ord(c) <= 126)
            self.keyterms = clean_ascii if clean_ascii else None
        else:
            self.keyterms = None

        self.ws: Optional[ClientConnection] = None
        self.is_connected = False
        self.session_info: Dict[str, Any] = {}
        self.detected_language: Optional[str] = None

    def get_connection_headers(self) -> Dict[str, str]:
        """
        Generates WebSocket upgrade headers required by Gnani Prisma v3.0.
        X-API-Key-ID: Authentication
        model: prisma-v3.0
        language_code: e.g. 'hi-IN', 'kn-IN', 'en-IN', 'ta-IN', 'te-IN', 'ml-IN',
                       'mr-IN', 'bn-IN', 'gu-IN', 'pa-IN', or 'indic-auto'
        format: 'transcribe' or 'codemix'
        keyterms: up to 200 clinical vocabulary terms (strictly ASCII)
        candidate_languages: hints for auto-detect mode
        """
        headers = {
            "X-API-Key-ID": self.api_key,
            "model": self.model,
            "language_code": self.language_code,
            "format": self.stt_format
        }
        if self.enable_keyterms and self.keyterms:
            headers["keyterms"] = self.keyterms
        if self.candidate_languages and self.language_code == "indic-auto":
            headers["candidate_languages"] = self.candidate_languages
        return headers

    async def connect(self) -> Dict[str, Any]:
        """
        Establishes upstream WebSocket connection to Gnani Prisma v3.0.
        Uses correct header parameter based on installed websockets version:
        'additional_headers' (websockets 14+) with fallback to 'extra_headers'.
        """
        if not config.has_real_credentials:
            raise ValueError(
                "Missing or invalid GNANI_API_KEY. Configure a valid key in backend/.env to connect to Gnani Prisma."
            )

        headers = self.get_connection_headers()
        logger.info(
            f"[Gnani STT] Initiating connection to {self.websocket_url} "
            f"(model={self.model}, lang={self.language_code})"
        )

        # Detect the correct header parameter for the installed websockets version
        sig = inspect.signature(websockets.connect)
        if "additional_headers" in sig.parameters:
            header_kwargs = {"additional_headers": headers}
        else:
            header_kwargs = {"extra_headers": headers}

        try:
            self.ws = await websockets.connect(
                self.websocket_url,
                **header_kwargs,
                open_timeout=10,
                ping_interval=20,
                ping_timeout=10,
                close_timeout=5
            )
            self.is_connected = True

            # Receive initial handshake response
            initial_msg = await asyncio.wait_for(self.ws.recv(), timeout=8.0)
            if isinstance(initial_msg, str):
                self.session_info = json.loads(initial_msg)
            else:
                self.session_info = {"type": "connected", "raw": initial_msg.decode("utf-8", errors="ignore")}

            logger.info(
                f"[Gnani STT] Handshake successful! Session connected "
                f"(request_id={self.session_info.get('request_id', 'unknown')})"
            )
            return self.session_info

        except Exception as e:
            self.is_connected = False
            logger.error(f"[Gnani STT] Connection error to Gnani Prisma v3.0: {type(e).__name__} - {str(e)}")
            raise

    async def send_audio_chunk(self, pcm_chunk: bytes):
        """
        Streams binary PCM audio chunk to Gnani Prisma v3.0.
        Chunks must be raw 16-bit PCM (1024 or 2048 bytes).
        """
        if not self.ws or not self.is_connected:
            raise RuntimeError("Gnani Prisma WebSocket is not connected.")
        
        await self.ws.send(pcm_chunk)
        self.chunks_sent_count = getattr(self, "chunks_sent_count", 0) + 1
        if self.chunks_sent_count == 1 or self.chunks_sent_count % 50 == 0:
            logger.info(
                f"[Gnani STT Stage 5 - Audio Forwarded] Sent chunk #{self.chunks_sent_count} "
                f"({len(pcm_chunk)} bytes) to Gnani Prisma v3"
            )

    async def send_commit(self):
        """
        Sends commit control frame to flush and finalize pending speech buffers.
        """
        if self.ws and self.is_connected:
            try:
                commit_msg = json.dumps({"type": "commit"})
                await self.ws.send(commit_msg)
                logger.info("[Gnani STT Stage 5 - Commit Sent] Sent commit frame to finalize transcription.")
            except Exception as e:
                logger.warning(f"[Gnani STT] Error sending commit signal: {e}")

    async def receive_events(self) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Continuously yields incoming transcription events from Gnani Prisma server.
        Only genuine events from Gnani are yielded.
        Normalizes both 'text' and 'transcript' properties.
        """
        if not self.ws:
            return

        try:
            async for raw_message in self.ws:
                if isinstance(raw_message, bytes):
                    raw_message = raw_message.decode("utf-8", errors="ignore")
                
                try:
                    event = json.loads(raw_message)
                    event["engine"] = "gnani_prisma_v3"
                    event["is_mock"] = False
                    
                    if "detected_language_code" in event:
                        self.detected_language = event["detected_language_code"]
                    elif "language_code" in event:
                        self.detected_language = event["language_code"]

                    # Normalize text and transcript fields for universal compatibility
                    text_content = event.get("text") or event.get("transcript") or ""
                    if text_content:
                        event["text"] = text_content
                        event["transcript"] = text_content

                    if event.get("type") == "transcript":
                        logger.info(
                            f"[Gnani STT Stage 6 - Response Received] Recognized text: len={len(text_content)} "
                            f"is_final={event.get('is_final')} lang={self.detected_language}"
                        )
                    elif event.get("type") == "speech_start":
                        logger.info(f"[Gnani STT Stage 6 - Speech Start] Utterance ID: {event.get('utterance_id')}")

                    yield event
                except json.JSONDecodeError:
                    logger.warning(f"[Gnani STT] Non-JSON message from Gnani: {raw_message}")
                    yield {
                        "type": "raw",
                        "content": raw_message,
                        "engine": "gnani_prisma_v3",
                        "is_mock": False
                    }

        except websockets.exceptions.ConnectionClosed as e:
            logger.info(f"[Gnani STT] WebSocket connection closed normally: code={e.code}")
        except Exception as e:
            logger.error(f"[Gnani STT] Error in event receiver loop: {e}")
            yield {
                "type": "error",
                "message": str(e),
                "engine": "gnani_prisma_v3",
                "is_mock": False
            }
        finally:
            self.is_connected = False

    async def close(self):
        """Safely closes the upstream Gnani Prisma connection."""
        if self.ws:
            try:
                await self.ws.close()
            except Exception as e:
                logger.warning(f"[Gnani STT] Error closing WebSocket: {e}")
            finally:
                self.ws = None
                self.is_connected = False
