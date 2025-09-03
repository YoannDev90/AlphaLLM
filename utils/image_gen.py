import aiohttp
import asyncio
import logging
from utils.config import logger_name
import urllib.parse
import random
from dotenv import load_dotenv
from utils.ai_gen import get_image_model_info
import litellm
from io import BytesIO
import os

load_dotenv()

logger = logging.getLogger(logger_name)

class ImageGenerationQueue:
    def __init__(self, max_per_minute=3):
        self.queue = asyncio.Queue()
        self.max_per_minute = max_per_minute
        self.semaphore = asyncio.Semaphore(max_per_minute)
        self.tasks = []
        self.start_time = asyncio.get_event_loop().time()

    async def enqueue(self, prompt, model="pollinations/flux", size = "1024x1024"):
        future = asyncio.Future()
        await self.queue.put((prompt, model, size, future))
        return future

    async def process_queue(self):
        while True:
            prompt, model, size, future = await self.queue.get()
            try:
                async with self.semaphore:
                    image_data = await self._generate_image(prompt, model, size)
                    future.set_result(image_data)
            except Exception as e:
                logger.error(f"Error processing image generation task: {str(e)}")
                future.set_exception(e)
            finally:
                self.queue.task_done()

    async def _generate_image(self, prompt, model, size):
        if model.startswith("pollinations/"):
            model = model.replace("pollinations/", "")
            width, height = map(int, size.split("x"))
            logger.info(f"Generating image with prompt: {prompt}, model: {model}, size: {size}")

            try:
                params = {
                    "prompt": prompt,
                    "model": model,
                    "width": width,
                    "height": height,
                    "seed": random.randint(0, 1000000),
                    "nologo": "true",
                    "private": "true",
                    "enhance": "false",
                    "safe": "false",
                    "token": os.getenv("POLLINATIONS_API_KEY")
                }

                url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
                url += "?" + urllib.parse.urlencode(params)

                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            image_data = await response.read()
                            return image_data, False
                        else:
                            error_message = await response.text()
                            logger.error(f"Error generating image. Status: {response.status} - {error_message}")
                            return None, False
            except Exception as e:
                logger.error(f"Error during image generation: {e}")
                return None, False
        
        elif model.startswith("navy/"):
            model = model.replace("navy/", "openai/")
            try:
                model_info = get_image_model_info(model)
                image = litellm.image_generation(
                    model=model,
                    api_key=model_info["api_key"],
                    api_base=model_info["base_url"],
                    size=size,
                    prompt=prompt                
                    )
                if model == "navy/imagen-3":
                    return image, False
                else:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(image.data[0].url) as response:
                            if response.status == 200:
                                image_data = await response.read()
                                return image_data, False
                            else:
                                error_message = await response.text()
                                logger.error(f"Error generating image. Status: {response.status} - {error_message}")
                                return None, False
            except Exception as e:
                logger.error(f"Error during navy image generation: {e}")
                return None, False
        
        else:
            logger.error(f"Unsupported model: {model}")
            return None, False

image_queue = ImageGenerationQueue()
logger.debug("Global image queue initialized")

queue_task = None

def start_image_queue(loop):
    global queue_task
    queue_task = loop.create_task(image_queue.process_queue())

async def generate_image(prompt: str, model="pollinations/flux", size="1024x1024"):
    future = await image_queue.enqueue(prompt=prompt,
                                        model=model,
                                        size=size,
                                        )
    result = await future
    return result

async def image_edit(prompt, url, size):
    width, height = size.split("x")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url) as response:
                if response.status != 200:
                    logger.error("❌ L'image n'existe pas.")
    except Exception as e:
        logger.error(f"💥 Erreur lors de la vérification de l'image: {e}")

    params = {
        "prompt": prompt,
        "model": "kontext",
        "image": url,
        "width": width,
        "height": height,
        "seed": random.randint(0, 1000000),
        "nologo": "true",
        "private": "true",
        "enhance": "false",
        "safe": "false",
        "token": os.getenv("POLLINATIONS_API_KEY")
    }
    base_url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
    request_url = base_url + "?" + urllib.parse.urlencode(params)

    try:
        timeout = aiohttp.ClientTimeout(total=120)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(request_url) as response:
                if response.status == 200:
                    image_data = await response.read()
                    logger.info(f"Image édition réussie. Taille: {len(image_data)} bytes")
                    return image_data, False
                else:
                    error_message = await response.text()
                    logger.error(f"Error editing image. Status: {response.status} - {error_message}")
                    return None, False
    except asyncio.TimeoutError:
        logger.error("Timeout lors de l'édition d'image (120s)")
        return None, False
    except Exception as e:
        logger.error(f"Erreur lors de l'édition d'image: {str(e)}")
        return None, False
            