"""Discord voice message generation and streaming module."""

import asyncio
import base64
import json
import logging
import os
from io import BytesIO
from typing import Optional
from urllib.parse import quote

import aiohttp
from dotenv import load_dotenv

from utils.config.app_config import LOGGER_NAME
from utils.config.constants import (
    DISCORD_API_VERSION,
    VOICE_API_URL,
    VOICE_UPLOAD_TIMEOUT,
    AVAILABLE_VOICES,
    VOICE_PRIORITY_1,
    VOICE_PRIORITY_2,
    DEFAULT_VOICE
)
from utils.media.audio import convert_to_opus, generate_waveform

logger = logging.getLogger(LOGGER_NAME)
load_dotenv()

# Configuration
DISCORD_TOKEN = os.getenv("BOT_TOKEN")


async def send_voice_message(channel, text: str, voice: str = "nova") -> Optional[dict]:
    """Send voice message to Discord channel using Pollinations AI.
    
    Generates speech audio, converts to Opus format, uploads to Discord,
    and sends as voice message with waveform visualization.
    
    Args:
        channel: Discord text channel object.
        text: Text to convert to speech.
        voice: Voice ID to use (default: 'nova').
        
    Returns:
        Response JSON from Discord API or None if failed.
        
    Example:
        >>> result = await send_voice_message(channel, "Hello everyone!")
        >>> if result:
        ...     print(f"Voice message sent: {result['id']}")
    """
    session = None
    audio_bytes = None
    opus_data = None
    
    try:
        logger.debug(f"Starting voice message generation with voice '{voice}'")
        
        # Generate audio
        audio_bytes = await generate_voice(text, voice, fallback=True)
        if not audio_bytes:
            logger.warning("Audio generation failed")
            return None
        
        # Convert to Opus format
        opus_data, duration = await convert_to_opus(audio_bytes)
        if not opus_data:
            logger.warning("Opus conversion failed")
            return None
        
        logger.debug(f"Audio ready: {duration}s duration")
        
        # Create HTTP session
        session = aiohttp.ClientSession()
        
        # Step 1: Request file upload slot
        logger.debug("Requesting Discord upload slot")
        upload_info = await _request_upload_slot(session, channel.id, duration)
        if not upload_info:
            logger.warning("Failed to get upload slot")
            return None
        
        # Step 2: Upload file to Discord
        logger.debug("Uploading file to Discord")
        success = await _upload_file(session, upload_info, opus_data)
        if not success:
            logger.warning("File upload failed")
            return None
        
        # Step 3: Send voice message
        logger.debug("Sending voice message with attachment")
        waveform_data = generate_waveform(audio_bytes)
        result = await _send_message(session, channel.id, upload_info, duration, waveform_data)
        
        if result:
            logger.info("Voice message sent successfully")
        
        return result
        
    except Exception as e:
        logger.error(f"Voice message error: {str(e)}", exc_info=True)
        return None
    finally:
        # Cleanup
        if session:
            await session.close()
        if audio_bytes:
            audio_bytes.close()
        if opus_data:
            opus_data.close()


async def _request_upload_slot(session: aiohttp.ClientSession, channel_id: int, duration: float) -> Optional[dict]:
    """Request file upload slot from Discord API.
    
    Args:
        session: Active aiohttp session.
        channel_id: Discord channel ID.
        duration: Audio duration in seconds.
        
    Returns:
        Upload info dict or None if failed.
    """
    try:
        upload_data = {
            "files": [{
                "filename": "voice.ogg",
                "file_size": 1024 * 100,  # Approximate size
                "id": "0"
            }]
        }
        
        headers = {"Authorization": f"Bot {DISCORD_TOKEN}"}
        url = f"https://discord.com/api/{DISCORD_API_VERSION}/channels/{channel_id}/attachments"
        
        async with session.post(url, json=upload_data, headers=headers) as resp:
            if resp.status != 200:
                logger.error(f"Upload request failed: {resp.status}")
                return None
            return await resp.json()
    except Exception as e:
        logger.error(f"Upload slot request error: {str(e)}")
        return None


async def _upload_file(session: aiohttp.ClientSession, upload_info: dict, opus_data: BytesIO) -> bool:
    """Upload audio file to Discord.
    
    Args:
        session: Active aiohttp session.
        upload_info: Upload slot information from Discord.
        opus_data: Audio file bytes.
        
    Returns:
        True if successful, False otherwise.
    """
    try:
        opus_data.seek(0)
        upload_url = upload_info['attachments'][0]['upload_url']
        
        async with session.put(
            upload_url,
            data=opus_data,
            headers={"Content-Type": "audio/ogg"}
        ) as resp:
            if resp.status != 200:
                logger.error(f"File upload failed: {resp.status}")
                return False
            return True
    except Exception as e:
        logger.error(f"File upload error: {str(e)}")
        return False


async def _send_message(
    session: aiohttp.ClientSession,
    channel_id: int,
    upload_info: dict,
    duration: float,
    waveform_data: str
) -> Optional[dict]:
    """Send message with voice attachment to Discord.
    
    Args:
        session: Active aiohttp session.
        channel_id: Discord channel ID.
        upload_info: Upload info from Discord API.
        duration: Audio duration in seconds.
        waveform_data: JSON waveform visualization data.
        
    Returns:
        Response from Discord API or None if failed.
    """
    try:
        attachment_info = upload_info['attachments'][0]
        
        message_payload = {
            "flags": 8192,  # Suppress embeds
            "attachments": [{
                "id": "0",
                "filename": "voice.ogg",
                "uploaded_filename": attachment_info['upload_filename'],
                "duration_secs": round(float(duration), 1),
                "waveform": waveform_data,
                "flags": 0,
                "description": None
            }]
        }
        
        headers = {
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (AlphaLLM 1.0.0)"
        }
        
        url = f"https://discord.com/api/{DISCORD_API_VERSION}/channels/{channel_id}/messages"
        
        async with session.post(url, json=message_payload, headers=headers) as resp:
            if resp.status != 200:
                error = await resp.json()
                logger.error(f"Message send failed: {error}")
                return None
            return await resp.json()
    except Exception as e:
        logger.error(f"Message send error: {str(e)}")
        return None


async def generate_voice(text: str, voice: str = "nova", fallback: bool = True) -> Optional[BytesIO]:
    """Generate speech audio from text using Pollinations API.
    
    Uses cascading voice fallback for reliability.
    
    Args:
        text: Text to convert to speech.
        voice: Preferred voice ID.
        fallback: If True, try alternative voices on failure.
        
    Returns:
        Audio bytes or None if all attempts fail.
        
    Example:
        >>> audio = await generate_voice("Hello world", voice="nova")
        >>> if audio:
        ...     print(f"Generated {len(audio.getvalue())} bytes of audio")
    """
    logger.debug(f"Voice generation - voice: {voice}, fallback: {fallback}")
    
    async with aiohttp.ClientSession() as session:
        # Try primary voice
        audio = await _fetch_audio(session, text, voice)
        if audio:
            logger.debug(f"Voice generated with '{voice}'")
            return audio
        
        if not fallback:
            logger.warning(f"Voice generation failed - no fallback")
            return None
        
        # Try priority group 1
        logger.debug("Trying priority voice group 1")
        for alt_voice in VOICE_PRIORITY_1:
            if alt_voice != voice:
                audio = await _fetch_audio(session, text, alt_voice)
                if audio:
                    logger.info(f"Fallback success with '{alt_voice}'")
                    return audio
        
        # Try priority group 2
        logger.debug("Trying priority voice group 2")
        for alt_voice in VOICE_PRIORITY_2:
            audio = await _fetch_audio(session, text, alt_voice)
            if audio:
                logger.info(f"Fallback success with '{alt_voice}'")
                return audio
        
        logger.error("All voice generation attempts failed")
        return None


async def _fetch_audio(session: aiohttp.ClientSession, text: str, voice: str) -> Optional[BytesIO]:
    """Fetch audio from Pollinations API for given text and voice.
    
    Args:
        session: Active aiohttp session.
        text: Text to synthesize.
        voice: Voice ID to use.
        
    Returns:
        Audio bytes or None if failed.
    """
    try:
        prompt = f"Just read the text below: {text}"
        url = f"{VOICE_API_URL}/{quote(prompt)}"
        
        params = {
            "model": "openai-audio",
            "voice": voice
        }
        
        async with session.get(
            url,
            params=params,
            timeout=aiohttp.ClientTimeout(total=VOICE_UPLOAD_TIMEOUT)
        ) as response:
            if response.status == 200:
                audio_data = await response.read()
                logger.debug(f"Audio fetched: {len(audio_data)} bytes with voice '{voice}'")
                return BytesIO(audio_data)
            else:
                logger.debug(f"Audio fetch failed with status {response.status}")
                return None
    except Exception as e:
        logger.debug(f"Audio fetch error: {str(e)}")
        return None
