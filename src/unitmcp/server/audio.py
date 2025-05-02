"""
audio.py
"""

"""Audio server for microphone and speaker control."""

import asyncio
import base64
import io
from typing import Dict, Any, Optional

from .base import MCPServer
from ..protocols.hardware_protocol import MCPRequest, MCPResponse, MCPErrorCode

try:
    import pyaudio
    import wave
    import sounddevice as sd
    import numpy as np

    HAS_AUDIO = True
except ImportError:
    HAS_AUDIO = False

    # Mock classes for environments without audio
    class MockPyAudio:
        def open(self, *args, **kwargs):
            return MockStream()

    class MockStream:
        def read(self, frames):
            return b""

        def write(self, data):
            pass

        def start_stream(self):
            pass

        def stop_stream(self):
            pass

        def close(self):
            pass

    pyaudio = MockPyAudio()


class AudioServer(MCPServer):
    """MCP server for audio device control."""

    def __init__(self):
        super().__init__()
        self.is_recording = False
        self.is_playing = False
        self.audio_format = pyaudio.paInt16
        self.channels = 1
        self.rate = 44100
        self.chunk_size = 1024
        self.audio = pyaudio.PyAudio() if HAS_AUDIO else None
        self.stream = None
        self.recorded_frames = []

    async def handle_request(self, request: MCPRequest) -> MCPResponse:
        """Handle audio requests."""
        try:
            method_parts = request.method.split(".")
            if len(method_parts) < 2:
                return self.create_error_response(
                    request.id, MCPErrorCode.METHOD_NOT_FOUND, "Invalid method format"
                )

            action = method_parts[1]

            # Map methods to handlers
            handlers = {
                "startRecording": self.start_recording,
                "stopRecording": self.stop_recording,
                "playAudio": self.play_audio,
                "setVolume": self.set_volume,
                "getVolume": self.get_volume,
                "listDevices": self.list_devices,
                "textToSpeech": self.text_to_speech,
                "speechToText": self.speech_to_text,
            }

            if action not in handlers:
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.METHOD_NOT_FOUND,
                    f"Unknown audio method: {action}",
                )

            return await handlers[action](request)

        except Exception as e:
            self.logger.error(f"Audio error: {e}")
            return self.create_error_response(
                request.id, MCPErrorCode.INTERNAL_ERROR, str(e)
            )

    async def start_recording(self, request: MCPRequest) -> MCPResponse:
        """Start recording from microphone."""
        if not HAS_AUDIO:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, "Audio support not available"
            )

        if self.is_recording:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Already recording"
            )

        try:
            # Get parameters
            duration = request.params.get("duration", 0)  # 0 means continuous
            device_id = request.params.get("device_id")

            # Start recording stream
            self.recorded_frames = []
            self.stream = self.audio.open(
                format=self.audio_format,
                channels=self.channels,
                rate=self.rate,
                input=True,
                input_device_index=device_id,
                frames_per_buffer=self.chunk_size,
            )

            self.is_recording = True

            # If duration specified, schedule stop
            if duration > 0:
                asyncio.create_task(self._auto_stop_recording(duration))

            return MCPResponse(
                id=request.id,
                result={
                    "status": "recording_started",
                    "device": device_id or "default",
                    "rate": self.rate,
                    "channels": self.channels,
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to start recording: {e}",
            )

    async def _auto_stop_recording(self, duration: float):
        """Automatically stop recording after duration."""
        await asyncio.sleep(duration)
        if self.is_recording:
            await self.stop_recording(
                MCPRequest(id="auto_stop", method="audio.stopRecording", params={})
            )

    async def stop_recording(self, request: MCPRequest) -> MCPResponse:
        """Stop recording and return audio data."""
        if not self.is_recording:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Not recording"
            )

        try:
            # Stop stream
            self.is_recording = False
            if self.stream:
                self.stream.stop_stream()
                self.stream.close()
                self.stream = None

            # Convert frames to base64
            audio_data = b"".join(self.recorded_frames)
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")

            # Create WAV file
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, "wb") as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(self.audio.get_sample_size(self.audio_format))
                wav_file.setframerate(self.rate)
                wav_file.writeframes(audio_data)

            wav_base64 = base64.b64encode(wav_buffer.getvalue()).decode("utf-8")

            return MCPResponse(
                id=request.id,
                result={
                    "status": "recording_stopped",
                    "audio_data": audio_base64,
                    "wav_data": wav_base64,
                    "duration": len(audio_data) / (self.rate * self.channels * 2),
                    "format": "wav",
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to stop recording: {e}",
            )

    async def play_audio(self, request: MCPRequest) -> MCPResponse:
        """Play audio data."""
        if not HAS_AUDIO:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, "Audio support not available"
            )

        audio_data = request.params.get("audio_data")
        if not audio_data:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing audio_data parameter"
            )

        try:
            # Decode base64 audio data
            audio_bytes = base64.b64decode(audio_data)

            # Play audio
            if request.params.get("format") == "wav":
                # Play WAV file
                wav_buffer = io.BytesIO(audio_bytes)
                with wave.open(wav_buffer, "rb") as wav_file:
                    rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    frames = wav_file.readframes(wav_file.getnframes())

                    # Convert to numpy array
                    audio_array = np.frombuffer(frames, dtype=np.int16)
                    if channels == 2:
                        audio_array = audio_array.reshape(-1, 2)

                    # Play using sounddevice
                    sd.play(audio_array, rate)
                    sd.wait()
            else:
                # Raw audio data
                stream = self.audio.open(
                    format=self.audio_format,
                    channels=self.channels,
                    rate=self.rate,
                    output=True,
                )
                stream.write(audio_bytes)
                stream.stop_stream()
                stream.close()

            return MCPResponse(
                id=request.id,
                result={
                    "status": "audio_played",
                    "duration": len(audio_bytes) / (self.rate * self.channels * 2),
                },
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to play audio: {e}"
            )

    async def set_volume(self, request: MCPRequest) -> MCPResponse:
        """Set system volume (platform-specific)."""
        volume = request.params.get("volume")
        if volume is None or not (0 <= volume <= 100):
            return self.create_error_response(
                request.id,
                MCPErrorCode.INVALID_PARAMS,
                "Volume must be between 0 and 100",
            )

        try:
            # Platform-specific volume control
            import platform

            system = platform.system()

            if system == "Windows":
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None
                )
                volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
                volume_interface.SetMasterVolumeLevelScalar(volume / 100, None)
            elif system == "Darwin":  # macOS
                import subprocess

                subprocess.run(
                    ["osascript", "-e", f"set volume output volume {volume}"]
                )
            elif system == "Linux":
                import subprocess

                subprocess.run(
                    ["amixer", "-D", "pulse", "sset", "Master", f"{volume}%"]
                )
            else:
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.HARDWARE_ERROR,
                    f"Volume control not supported on {system}",
                )

            return MCPResponse(
                id=request.id, result={"status": "volume_set", "volume": volume}
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to set volume: {e}"
            )

    async def get_volume(self, request: MCPRequest) -> MCPResponse:
        """Get current system volume."""
        try:
            import platform

            system = platform.system()

            if system == "Windows":
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(
                    IAudioEndpointVolume._iid_, CLSCTX_ALL, None
                )
                volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
                current_volume = int(
                    volume_interface.GetMasterVolumeLevelScalar() * 100
                )
            elif system == "Darwin":  # macOS
                import subprocess

                result = subprocess.run(
                    ["osascript", "-e", "output volume of (get volume settings)"],
                    capture_output=True,
                    text=True,
                )
                current_volume = int(result.stdout.strip())
            elif system == "Linux":
                import subprocess

                result = subprocess.run(
                    ["amixer", "-D", "pulse", "sget", "Master"],
                    capture_output=True,
                    text=True,
                )
                # Parse amixer output
                import re

                match = re.search(r"\[(\d+)%\]", result.stdout)
                current_volume = int(match.group(1)) if match else 0
            else:
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.HARDWARE_ERROR,
                    f"Volume control not supported on {system}",
                )

            return MCPResponse(
                id=request.id, result={"status": "success", "volume": current_volume}
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to get volume: {e}"
            )

    async def list_devices(self, request: MCPRequest) -> MCPResponse:
        """List available audio devices."""
        if not HAS_AUDIO:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, "Audio support not available"
            )

        try:
            devices = []

            # List input devices
            for i in range(self.audio.get_device_count()):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info["maxInputChannels"] > 0:
                    devices.append(
                        {
                            "id": i,
                            "name": device_info["name"],
                            "type": "input",
                            "channels": device_info["maxInputChannels"],
                            "default": i
                            == self.audio.get_default_input_device_info()["index"],
                        }
                    )
                if device_info["maxOutputChannels"] > 0:
                    devices.append(
                        {
                            "id": i,
                            "name": device_info["name"],
                            "type": "output",
                            "channels": device_info["maxOutputChannels"],
                            "default": i
                            == self.audio.get_default_output_device_info()["index"],
                        }
                    )

            return MCPResponse(
                id=request.id, result={"status": "success", "devices": devices}
            )
        except Exception as e:
            return self.create_error_response(
                request.id, MCPErrorCode.HARDWARE_ERROR, f"Failed to list devices: {e}"
            )

    async def text_to_speech(self, request: MCPRequest) -> MCPResponse:
        """Convert text to speech (TTS)."""
        text = request.params.get("text")
        if not text:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing text parameter"
            )

        try:
            import pyttsx3

            engine = pyttsx3.init()

            # Configure voice parameters
            rate = request.params.get("rate", 150)
            volume = request.params.get("volume", 1.0)
            voice_id = request.params.get("voice_id")

            engine.setProperty("rate", rate)
            engine.setProperty("volume", volume)

            if voice_id:
                engine.setProperty("voice", voice_id)

            # Generate speech
            # Note: pyttsx3 doesn't provide direct audio data output
            # For advanced TTS, consider using cloud services
            engine.say(text)
            engine.runAndWait()

            return MCPResponse(
                id=request.id, result={"status": "speech_generated", "text": text}
            )
        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to generate speech: {e}",
            )

    async def speech_to_text(self, request: MCPRequest) -> MCPResponse:
        """Convert speech to text (STT)."""
        audio_data = request.params.get("audio_data")
        if not audio_data:
            return self.create_error_response(
                request.id, MCPErrorCode.INVALID_PARAMS, "Missing audio_data parameter"
            )

        try:
            import speech_recognition as sr

            recognizer = sr.Recognizer()

            # Decode audio data
            audio_bytes = base64.b64decode(audio_data)

            # Create AudioData object
            audio = sr.AudioData(audio_bytes, self.rate, 2)

            # Recognize speech
            language = request.params.get("language", "en-US")

            try:
                text = recognizer.recognize_google(audio, language=language)
                return MCPResponse(
                    id=request.id,
                    result={"status": "success", "text": text, "language": language},
                )
            except sr.UnknownValueError:
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.INVALID_PARAMS,
                    "Could not understand audio",
                )
            except sr.RequestError as e:
                return self.create_error_response(
                    request.id,
                    MCPErrorCode.HARDWARE_ERROR,
                    f"Speech recognition service error: {e}",
                )

        except Exception as e:
            return self.create_error_response(
                request.id,
                MCPErrorCode.HARDWARE_ERROR,
                f"Failed to recognize speech: {e}",
            )

    def __del__(self):
        """Cleanup audio resources."""
        if HAS_AUDIO and self.audio:
            self.audio.terminate()
