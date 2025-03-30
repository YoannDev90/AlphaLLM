# image_generator.py

import aiohttp
import asyncio
import logging
import urllib.parse
import random

logger = logging.getLogger('AlphaLLM')

class ImageGenerationQueue:
    def __init__(self, max_per_minute=5):
        self.queue = asyncio.Queue()
        self.max_per_minute = max_per_minute
        self.semaphore = asyncio.Semaphore(max_per_minute)
        self.tasks = []
        self.start_time = asyncio.get_event_loop().time()
        logger.debug(f"ImageGenerationQueue initialized with max_per_minute={max_per_minute}")

    async def enqueue(self, prompt, model="flux", seed=None, width=1024, height=1024, nologo=True, private=False, enhance=False, safe=True):
        logger.debug(f"Enqueuing image generation task: prompt={prompt}, model={model}, seed={seed}, width={width}, height={height}, nologo={nologo}, private={private}, enhance={enhance}, safe={safe}")
        future = asyncio.Future()
        await self.queue.put((prompt, model, seed, width, height, nologo, private, enhance, safe, future))
        logger.debug("Task enqueued successfully")
        return future

    async def process_queue(self):
        logger.debug("Starting queue processing")
        while True:
            prompt, model, seed, width, height, nologo, private, enhance, safe, future = await self.queue.get()
            logger.debug(f"Processing task: prompt={prompt}, model={model}, seed={seed}, width={width}, height={height}, nologo={nologo}, private={private}, enhance={enhance}, safe={safe}")
            try:
                async with self.semaphore:
                    logger.debug("Semaphore acquired for task")
                    image_data = await self._generate_image(prompt, model, seed, width, height, nologo, private, enhance, safe)
                    future.set_result(image_data)
                    logger.debug("Image generation task completed successfully")
            except Exception as e:
                logger.exception("Error processing image generation task:")
                future.set_exception(e)
            finally:
                self.queue.task_done()
                logger.debug("Task marked as done")

    async def _generate_image(self, prompt, model="flux", seed=None, width=1024, height=1024, nologo=True, private=False, enhance=False, safe=True):
        logger.debug(f"Generating image with parameters: prompt={prompt}, model={model}, seed={seed}, width={width}, height={height}, nologo={nologo}, private={private}, enhance={enhance}, safe={safe}")
        try:
            params = {
                "prompt": prompt,
                "model": model,
                "width": width,
                "height": height,
                "nologo": str(nologo).lower(),
                "private": str(private).lower(),
                "enhance": str(enhance).lower(),
                "safe": str(safe).lower(),
                "referrer": "AlphaLLM - AI Discord Bot",
            }
            if seed is not None:
                params["seed"] = seed
            elif seed is None:
                params["seed"] = random.randint(0, 1000000)
                logger.debug(f"Random seed generated: {params['seed']}")

            url = f"https://image.pollinations.ai/prompt/{urllib.parse.quote(prompt)}"
            url += "?" + urllib.parse.urlencode(params)
            logger.debug(f"Generated URL for image generation: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        logger.debug("Image generation request successful")
                        return await response.read()
                    else:
                        error_message = await response.text()
                        logger.error(f"Error generating image. Status: {response.status} - {error_message}")
                        return None
        except Exception as e:
            logger.error(f"Error during image generation: {e}")
            return None

# Initialize queue globally
image_queue = ImageGenerationQueue()
logger.debug("Global image queue initialized")

# Start the queue processing task globally
asyncio.create_task(image_queue.process_queue())
logger.debug("Queue processing task started")

async def generate_image(prompt: str, model="flux", seed=None, width=1024, height=1024, nologo=True, private=False, enhance=False, safe=True):
    logger.debug(f"generate_image called with: prompt={prompt}, model={model}, seed={seed}, width={width}, height={height}, nologo={nologo}, private={private}, enhance={enhance}, safe={safe}")
    future = await image_queue.enqueue(prompt=prompt,
                                        model=model,
                                        seed=seed,
                                        width=width,
                                        height=height,
                                        nologo=nologo,
                                        private=private,
                                        enhance=enhance,
                                        safe=safe)
    result = await future
    logger.debug("generate_image completed")
    return result
