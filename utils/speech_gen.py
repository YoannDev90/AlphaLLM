import aiohttp
import asyncio
from io import BytesIO
from urllib.parse import quote
from pydub import AudioSegment
import numpy as np
import librosa
import base64
import subprocess
import os
import logging
from dotenv import load_dotenv

load_dotenv()
DISCORD_TOKEN = os.getenv("TESTBOT_TOKEN")
logger = logging.getLogger('AlphaLLM')

VOICES = ["alloy", "echo", "fable", "onyx", "nova", "shimmer", 
         "coral", "verse", "ballad", "ash", "sage", "amuch", "dan"]

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

        if duration <= 0:
            logger.warning("Estimation durée via taille fichier")
            duration = len(stdout) / (128 * 1024)

        return BytesIO(stdout), round(duration, 1)

    except Exception as e:
        logger.error(f"Erreur globale conversion : {str(e)}")
        raise ValueError("Échec conversion audio") from e
    finally:
        audio_bytes.seek(0)
    
def generate_waveform(audio_bytes: BytesIO) -> str:
    """Génère un waveform personnalisé depuis l'audio source"""
    audio_bytes.seek(0)
    y, sr = librosa.load(audio_bytes, sr=None, mono=True)
    
    if len(y) > 480000:
        y = librosa.resample(y, orig_sr=sr, target_sr=24000)
    
    max_points = 100
    segment_size = len(y) // max_points
    waveform = [np.max(y[i*segment_size:(i+1)*segment_size]) * 255 for i in range(max_points)]
    
    return base64.b64encode(np.array(waveform, dtype=np.uint8).tobytes()).decode()


async def test_send_voice_message(channel, text: str):
    for voice in VOICES:
        try:
            logger.info(f"Envoi du message vocal avec la voix : {voice}")
            response = await send_voice_message(channel, text, voice)
            if response:
                logger.debug("Message vocal envoyé avec succès")
                return response
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du message vocal : {str(e)}")


async def send_voice_message(channel, text: str, voice: str = "nova"):
    """Version avec gestion améliorée de la session HTTP"""
    session = None
    try:
        # Génération et conversion audio
        audio_bytes = await asyncio.wait_for(generate_voice(text, voice), timeout=30)
        if not audio_bytes:
            return
            
        opus_data, duration = await convert_to_opus(audio_bytes)
        if not opus_data:
            return

        # Création d'une session HTTP unique
        session = aiohttp.ClientSession()
        
        # Étape 1: Demande d'upload
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
                return
            upload_info = await resp.json()

        # Étape 2: Upload fichier
        opus_data.seek(0)
        async with session.put(
            upload_info['attachments'][0]['upload_url'],
            data=opus_data,
            headers={"Content-Type": "audio/ogg"}
        ) as resp:
            if resp.status != 200:
                return

        # Étape 3: Envoi final
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
                logger.error(f"Erreur message : {error}")
                return
            return await resp.json()

    except Exception as e:
        logger.error(f"Erreur finale : {str(e)}")
    finally:
        if session:
            await session.close()
        if audio_bytes:
            audio_bytes.close()
        if opus_data:
            opus_data.close()

async def fetch_audio(session: aiohttp.ClientSession, text: str, voice: str) -> BytesIO:
    """Version simplifiée avec gestion de cache"""
    try:
        url = f"https://text.pollinations.ai/{quote('Just read the text below:' + text)}"
        async with session.get(
            url,
            params={"model": "openai-audio", "voice": voice},
            timeout=aiohttp.ClientTimeout(total=20)
        ) as response:
            if response.status == 200:
                logger.debug("Audio récupéré avec succès")
                return BytesIO(await response.read())
            else:
                logger.error(f"Échec de la récupération de l'audio : {response.status}")
                return None
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de l'audio : {str(e)}")
        return None

async def generate_voice(
    text: str,
    voice: str = "nova",
    fallback: bool = True
) -> BytesIO:
    """Version avec cache mémoire et priorisation des voix"""
    prompt_text = f"Just read the text below: {text}"
    async with aiohttp.ClientSession() as session:
        if audio := await fetch_audio(session, prompt_text, voice):
            return audio
        
        # Fallback organisé par priorités
        if fallback:
            logger.info("Voix principale échouée, tentative avec fallback")
            for voice_group in [VOICES[:6], VOICES[6:]]:
                tasks = [fetch_audio(session, text, v) for v in voice_group]
                for future in asyncio.as_completed(tasks):
                    if result := await future:
                        logger.info(f"Audio généré avec la voix fallback : {voice_group}")
                        return result
        logger.error("Échec de la génération vocale")
        return None
