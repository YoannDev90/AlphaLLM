"""Audio synthesis and processing module with Speechify and Opus conversion."""

import asyncio
import base64
import json
import logging
import os
import subprocess
from io import BytesIO
from typing import Tuple

import librosa
import numpy as np
from dotenv import load_dotenv
from pydub import AudioSegment
from speechify import Speechify

from utils.config.app_config import LOGGER_NAME
from utils.config.constants import (
    OPUS_BITRATE,
    OPUS_SAMPLE_RATE,
    OPUS_FORMAT,
    WAVEFORM_MIN_SAMPLES
)

logger = logging.getLogger(LOGGER_NAME)
load_dotenv()

# Configuration
SPEECHIFY_API_KEY = os.getenv("SPEECHIFY_API_KEY")
DISCORD_TOKEN = os.getenv("BOT_TOKEN")

# Speechify client initialization
client = Speechify(token=SPEECHIFY_API_KEY)


async def list_voices() -> list:
    """Retrieve available Speechify voices.
    
    Returns:
        list: Available voice configurations.
        
    Example:
        >>> voices = await list_voices()
        >>> print(f"Available voices: {len(voices)}")
    """
    try:
        logger.debug("Fetching available Speechify voices")
        voices = client.tts.voices.list()
        
        if hasattr(voices, 'json'):
            result = voices.json()
        else:
            result = voices
            
        logger.debug(f"Retrieved {len(result) if result else 0} voices")
        return result if result else []
    except Exception as e:
        logger.error(f"Failed to fetch voices: {str(e)}")
        return []


async def generate_speech(text: str, voice: str = "oliver") -> bytes | None:
    """Generate speech audio from text using Speechify API.
    
    Args:
        text: Text to convert to speech.
        voice: Voice ID to use (default: 'oliver').
        
    Returns:
        Audio bytes or None if generation fails.
        
    Example:
        >>> audio_bytes = await generate_speech("Hello world")
        >>> if audio_bytes:
        ...     print(f"Generated {len(audio_bytes)} bytes of audio")
    """
    try:
        logger.debug(f"Generating speech with voice '{voice}'")
        audio = client.tts.audio.speech(
            input=text,
            voice_id=voice,
        )
        result = base64.b64decode(audio.audio_data)
        logger.debug(f"Speech generated: {len(result)} bytes")
        return result
    except Exception as e:
        logger.error(f"Speech generation failed: {str(e)}")
        return None


async def convert_to_opus(audio_bytes: BytesIO) -> Tuple[BytesIO | None, float]:
    """Convert audio to Opus format with in-memory processing.
    
    Converts any audio format to Opus codec (48kHz, 128kbps) for Discord streaming.
    
    Args:
        audio_bytes: Audio stream in any format.
        
    Returns:
        Tuple of (converted audio BytesIO, duration in seconds).
        Returns (None, 0.0) on failure.
        
    Example:
        >>> audio_stream, duration = await convert_to_opus(audio_input)
        >>> if audio_stream:
        ...     print(f"Converted audio, duration: {duration}s")
    """
    try:
        logger.debug("Starting Opus conversion")
        audio_bytes.seek(0)
        
        # Get duration from source audio
        try:
            audio = AudioSegment.from_file(audio_bytes)
            duration = audio.duration_seconds
            logger.debug(f"Source duration: {duration}s")
        except Exception as e:
            logger.warning(f"Could not determine duration: {str(e)}")
            duration = 0.0
        
        audio_bytes.seek(0)
        
        # FFmpeg Command for Opus encoding
        ffmpeg_cmd = [
            'ffmpeg',
            '-i', 'pipe:0',
            '-c:a', 'libopus',
            '-b:a', OPUS_BITRATE,
            '-ar', OPUS_SAMPLE_RATE,
            '-f', OPUS_FORMAT,
            '-loglevel', 'error',
            'pipe:1'
        ]
        
        proc = await asyncio.create_subprocess_exec(
            *ffmpeg_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        stdout, stderr = await proc.communicate(input=audio_bytes.read())
        
        if proc.returncode != 0:
            error_msg = stderr.decode()
            logger.error(f"FFmpeg conversion failed: {error_msg}")
            return None, 0.0
        
        logger.debug(f"Opus conversion successful, duration: {duration}s")
        return BytesIO(stdout), round(duration, 1)
        
    except Exception as e:
        logger.error(f"Opus conversion error: {str(e)}", exc_info=True)
        return None, 0.0
    finally:
        audio_bytes.seek(0)


def generate_waveform(audio_bytes: BytesIO) -> str:
    """Generate waveform visualization data from audio.
    
    Creates normalized JSON representation of audio waveform for visualization.
    
    Args:
        audio_bytes: Audio stream to analyze.
        
    Returns:
        JSON string with waveform amplitude data.
        
    Example:
        >>> waveform_json = generate_waveform(audio_stream)
        >>> waveform_data = json.loads(waveform_json)
    """
    try:
        logger.debug("Generating waveform visualization")
        audio_bytes.seek(0)
        
        y, sr = librosa.load(audio_bytes, sr=None, mono=True)
        
        # Downsample if too large
        if len(y) > WAVEFORM_MIN_SAMPLES:
            reduction_factor = len(y) // WAVEFORM_MIN_SAMPLES
            y = y[::reduction_factor]
        
        # Normalize to -1 to 1 range
        y_normalized = np.array(y) / np.max(np.abs(y)) if np.max(np.abs(y)) > 0 else y
        
        # Convert to JSON-serializable format
        waveform_data = {
            "samples": y_normalized.tolist()[:1000],  # Limit to 1000 points
            "duration": len(y) / sr if sr > 0 else 0
        }
        
        result = json.dumps(waveform_data)
        logger.debug("Waveform generation complete")
        return result
        
    except Exception as e:
        logger.error(f"Waveform generation failed: {str(e)}")
        return json.dumps({"samples": [], "duration": 0})
