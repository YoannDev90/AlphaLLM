from speechify import Speechify
import os
import json
import base64
import aiohttp
import asyncio
from io import BytesIO
from pydub import AudioSegment
import numpy as np
import librosa
import subprocess
import logging
from dotenv import load_dotenv
from utils.config import logger_name

load_dotenv()
SPEECHIFY_API_KEY = os.getenv("SPEECHIFY_API_KEY")
DISCORD_TOKEN = os.getenv("BOT_TOKEN")

logger = logging.getLogger(logger_name)

client = Speechify(
    token=SPEECHIFY_API_KEY,
)

async def list_voices():
    try:
        voices = client.tts.voices.list()
        if hasattr(voices, 'json'):
            return voices.json()
        else:
            return voices
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des voix : {str(e)}")
        return []

async def generate_speech(text: str, voice: str = "oliver"):
    try:
        audio = client.tts.audio.speech(
            input=text,
            voice_id=voice,
        )
        return base64.b64decode(audio.audio_data)
    except Exception as e:
        logger.error(f"Erreur lors de la génération de la parole : {str(e)}")
        return None

async def convert_to_opus(audio_bytes: BytesIO) -> tuple[BytesIO, float]:
    """Conversion in-memory avec durée précise via Pydub"""
    try:
        audio_bytes.seek(0)
        
        try:
            audio = AudioSegment.from_file(audio_bytes)
            duration = audio.duration_seconds
        except Exception as e:
            logger.error(f"Erreur lecture durée : {str(e)}")
            duration = 0.0

        audio_bytes.seek(0)

        ffmpeg_cmd = [
            'ffmpeg',
            '-i', 'pipe:0',
            '-c:a', 'libopus',
            '-b:a', '128k',
            '-ar', '48000',
            '-f', 'ogg',
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
            logger.error(f"Erreur FFmpeg : {stderr.decode()}")
            return None, 0.0

        logger.debug(f"Conversion Opus réussie, durée : {duration} secondes")
        return BytesIO(stdout), round(duration, 1)

    except Exception as e:
        logger.error(f"Erreur globale conversion : {str(e)}")
        raise ValueError("Échec conversion audio") from e
    finally:
        audio_bytes.seek(0)

def generate_waveform(audio_bytes: BytesIO) -> str:
    """Génère un waveform personnalisé depuis l'audio source"""
    try:
        audio_bytes.seek(0)
        y, sr = librosa.load(audio_bytes, sr=None, mono=True)
        
        if len(y) > 480000:
            y = librosa.resample(y, orig_sr=sr, target_sr=24000)
        
        max_points = 100
        segment_size = len(y) // max_points
        waveform = [np.max(y[i*segment_size:(i+1)*segment_size]) * 255 for i in range(max_points)]

        logger.debug(f"Waveform généré avec {len(waveform)} points")
        return base64.b64encode(np.array(waveform, dtype=np.uint8).tobytes()).decode()
    except Exception as e:
        logger.error(f"Erreur génération waveform : {str(e)}")
        # Fallback: waveform générique
        return base64.b64encode(np.zeros(100, dtype=np.uint8).tobytes()).decode()

async def send_voice_message(channel, text: str, voice: str = "oliver"):
    """Envoie un message vocal Discord au format Opus avec l'API Speechify"""
    session = None
    audio_bytes = None
    opus_data = None
    
    try:
        # Génération audio avec Speechify
        logger.debug(f"Génération audio avec Speechify, voix: {voice}")
        audio_data = await generate_speech(text, voice)
        if not audio_data:
            logger.error("Échec de la génération audio")
            return
            
        audio_bytes = BytesIO(audio_data)
        
        # Conversion en Opus
        logger.debug("Conversion audio en format Opus")
        opus_data, duration = await convert_to_opus(audio_bytes)
        if not opus_data:
            logger.error("Échec de la conversion Opus")
            return

        # Création d'une session HTTP unique
        session = aiohttp.ClientSession()
        
        # Étape 1: Demande d'upload
        logger.debug("Demande d'upload de fichier Discord")
        upload_data = {
            "files": [{
                "filename": "voice.ogg",
                "file_size": len(opus_data.getvalue()),
                "id": "0"
            }]
        }        
        async with session.post(
            f"https://discord.com/api/v10/channels/{channel.id}/attachments",
            json=upload_data,
            headers={"Authorization": f"Bot {DISCORD_TOKEN}"}
        ) as resp:
            if resp.status != 200:
                logger.error(f"Erreur upload Discord : {resp.status}")
                return
            upload_info = await resp.json()

        # Étape 2: Upload fichier
        logger.debug("Upload du fichier audio vers Discord")
        opus_data.seek(0)
        async with session.put(
            upload_info['attachments'][0]['upload_url'],
            data=opus_data,
            headers={"Content-Type": "audio/ogg"}
        ) as resp:
            if resp.status != 200:
                logger.error(f"Erreur upload fichier Discord : {resp.status}")
                return

        # Étape 3: Envoi final
        logger.debug("Envoi du message vocal Discord")
        waveform = generate_waveform(audio_bytes)
        headers = {
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (AlphaLLM 1.0.0)"
        }

        message_payload = {
            "flags": 8192,
            "attachments": [{
                "id": "0",
                "filename": "voice.ogg",
                "uploaded_filename": upload_info['attachments'][0]['upload_filename'],
                "duration_secs": round(float(duration), 1),
                "waveform": waveform,
                "flags": 0,
                "description": None
            }]
        }

        async with session.post(
            f"https://discord.com/api/v10/channels/{channel.id}/messages",
            json=message_payload,
            headers=headers
        ) as resp:
            if resp.status != 200:
                error = await resp.json()
                logger.error(f"Erreur envoi message Discord : {error}")
                return
            logger.info("Message vocal envoyé avec succès")
            return await resp.json()

    except Exception as e:
        logger.error(f"Erreur globale send_voice_message : {str(e)}")
    finally:
        if session:
            await session.close()
        if audio_bytes:
            audio_bytes.close()
        if opus_data:
            opus_data.close()