import discord
from io import BytesIO
import logging
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('AlphaLLM')

PUBLIC_IMAGE_CHANNEL_ID = os.getenv("GALERIE_ID")

async def gallery(bot : discord.Client, image_data, prompt, user):
    public_channel = await bot.fetch_channel(PUBLIC_IMAGE_CHANNEL_ID)
    file = discord.File(BytesIO(image_data), filename="generated_image.png")
    embed = discord.Embed(
        title=f"Image générée par {user}",
        description=f"Prompt : \n```{prompt}```",
        color=discord.Color.default()
        )
    embed.set_image(url="attachment://generated_image.png")
    await public_channel.send(embed=embed, file=file)